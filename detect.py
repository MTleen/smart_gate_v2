import logging
import os
import traceback
import cv2
import time
import argparse
import torch
import warnings
import numpy as np
import base64
import requests
from threading import Timer
import yaml

from deep_sort import build_tracker
from man_utils.draw import draw_boxes
from man_utils.parser import get_config
from man_utils.log import get_logger
from man_utils.io import write_results, save_img
from man_utils.RTSCapture import RTSCapture

from matplotlib import pyplot as plt


class VideoTracker(object):
    def __init__(self, cfg, args, video_path=None):
        self.cfg = cfg
        self.args = args
        self.video_path = video_path
        self.cur_objects = {}
        # self.logger = get_logger("root")
        self.is_close = False
        self.int2command = {1: "open", 2: "close"}

        use_cuda = args.use_cuda and torch.cuda.is_available()
        if not use_cuda:
            warnings.warn("Running in cpu mode which maybe very slow!",
                          UserWarning)

        if args.display:
            cv2.namedWindow("test", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("test", args.display_width, args.display_height)

        if args.cam != -1:
            print("Using webcam " + str(args.cam))
            self.vdo = RTSCapture.create(args.cam)
            self.vdo.start_read()
        else:
            self.vdo = cv2.VideoCapture()
        # self.detector = build_detector(cfg, use_cuda=use_cuda)
        # 构建目标检测器
        self.detector = torch.hub.load('ultralytics/yolov5',
                                       'yolov5s',
                                       pretrained=True,
                                       force_reload=False)
        self.detector.conf = 0.5
        classes = list(self.cfg.classes.keys())[:-2]
        self.detector.classes = list(map(lambda x: int(x), classes))
        # 构建目标跟踪器
        self.deepsort = build_tracker(cfg, use_cuda=use_cuda)

    def __enter__(self):
        if self.args.cam != -1:
            ret, frame = self.vdo.read_latest_frame()
            assert ret, "Error: Camera error"
            self.im_width = frame.shape[0]
            self.im_height = frame.shape[1]

        else:
            assert os.path.isfile(self.video_path), "Path error"
            self.vdo.open(self.video_path)
            assert self.vdo.isOpened()

        self.im_width = int(self.vdo.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.im_height = int(self.vdo.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if self.args.save_path:
            os.makedirs(self.args.save_path, exist_ok=True)

            # path of saved video and results
            self.save_video_path = os.path.join(self.args.save_path,
                                                "results.avi")
            self.save_results_path = os.path.join(self.args.save_path,
                                                  "results.txt")

            # create video writer
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.writer = cv2.VideoWriter(self.save_video_path, fourcc, 20,
                                          (self.im_width, self.im_height))

            # logging
            logging.info("Save results to {}".format(self.args.save_path))

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            print(exc_type, exc_value, exc_traceback)

    def run(self):
        logging.info(
            '############################# 开始检测 #############################')
        results = []
        # idx_frame = 0
        while self.vdo.read_latest_frame():
        # while self.vdo.grab():
            # idx_frame += 1
            # if idx_frame % self.args.frame_interval:
            #     continue
            start = time.time()
            _, ori_im = self.vdo.retrieve()
            im = cv2.cvtColor(ori_im, cv2.COLOR_BGR2RGB)

            # do detection
            detector_result = self.detector(im)
            if len(detector_result.pred) > 0 and len(
                    detector_result.pred[0] > 0):

                bbox_xywh = detector_result.xywh[0][:, :4]
                cls_conf = detector_result.pred[0][:, 4]
                cls = detector_result.pred[0][:, -1]
                outputs = self.deepsort.update(bbox_xywh, cls_conf, im)

                # draw boxes for visualization
                if len(outputs) > 0:
                    bbox_tlwh = []
                    bbox_xyxy = outputs[:, :4]
                    identities = outputs[:, -1]

                    for bb_xyxy in bbox_xyxy:
                        bbox_tlwh.append(self.deepsort._xyxy_to_tlwh(bb_xyxy))

                    for i, xyxy, c in zip(identities, bbox_xyxy, cls):
                        if not str(i) in self.cur_objects.keys():
                            self.cur_objects[str(i)] = {
                                'class': int(c),
                                'init': xyxy,
                                'current': xyxy
                            }
                            if xyxy[0] < 200:
                                self.is_close = True
                        else:
                            self.cur_objects[str(i)]['current'] = xyxy

                    command, res = self.get_command(ori_im)
                    # 执行指令
                    if command:
                        self.reset_states()

                        exec_res = self.send_command(
                            self.cfg.sys.mode, self.int2command[command],
                            res['words_result']['number']
                            if isinstance(res, dict)
                            and 'words_result' in res.keys() else None)
                        logging.info(f'触发条件：{res}，\n执行指令：{self.int2command[command]}，\n执行结果：{exec_res}')
                        # logging.info(f'执行指令：{self.int2command[command]}')

                        time.sleep(10)
                    logging.info(self.cur_objects)

                    ori_im = draw_boxes(ori_im, bbox_xyxy, identities)
                    save_img(ori_im)
                    if self.args.save_path:
                        results.append(
                            (bbox_tlwh, identities,
                            [self.cfg.classes[str(int(c))] for c in cls]))

                end = time.time()

                if self.args.display:
                    cv2.imshow("test", ori_im)
                    cv2.waitKey(1)

                if self.args.save_path:
                    self.writer.write(ori_im)

                    # save results
                    write_results(self.save_results_path, results, 'mot')

                # logging
                # logging.info("frame: {}, time: {:.03f}s, fps: {:.03f}, detection numbers: {}, tracking numbers: {}" \
                #                 .format(idx_frame, end - start, 1 / (end - start), bbox_xywh.shape[0], len(outputs)))
            else:
                # 视野里没有对象，清空对象字典
                self.reset_states()

                if self.args.save_path:
                    self.writer.write(ori_im)
                end = time.time()
                if end - start < 0.2:
                    time.sleep(0.2 - (end - start))
                print('当前画面没有对象。')
            time.sleep(0.5)

    def get_command(self, ori_im):
        """
        开门逻辑：任何一个目标符合开门条件就开门
        关门逻辑：所有需要判定是否关门的目标都满足关门条件
        """
        command = None
        res = None
        if self.is_close:
            # 进入关门判定流程
            command = 2
            for v in self.cur_objects.values():
                if v['init'][0] < 200 and v['current'][0] < 550:
                    command = None
                    break
        else:
            # 进入开门判定流程
            pic_str = base64.b64encode(cv2.imencode('.jpeg',
                                                    ori_im)[1]).decode()
            for v in self.cur_objects.values():
                init = v['init'][0]
                current = v['current'][0]
                # 判断是否开门
                if init > 550 and current < 250:
                    access_token = self.cfg['sys']['baidu']['access_token'][
                        'token']
                    if v['class'] == 0:
                        # 人脸识别
                        request_url = self.cfg['sys']['baidu']['face_search'][
                            'base_url']
                        params = self.cfg['sys']['baidu']['face_search'][
                            'params']
                        params['image'] = pic_str
                        request_url = request_url + "?access_token=" + access_token
                        headers = {'content-type': 'application/json'}
                        response = requests.post(request_url,
                                                 data=params,
                                                 headers=headers)
                        result = response.json()
                        print(result)
                        if result['error_code'] == 0 and len(
                                result['result']['user_list']) > 0:
                            print(
                                any(user['score'] > 75
                                    for user in result['result']['user_list']))
                            if any(user['score'] > 75
                                   for user in result['result']['user_list']):
                                command = 1
                                res = result
                                break
                    elif v['class'] == 2:
                        # 车牌识别
                        request_url = self.cfg['sys']['baidu'][
                            'license_plate']['base_url']
                        params = self.cfg['sys']['baidu']['license_plate'][
                            'params']
                        params['image'] = pic_str
                        headers = {
                            'content-type': 'application/x-www-form-urlencoded'
                        }
                        response = requests.post(request_url,
                                                 data=params,
                                                 headers=headers)
                        result = response.json()
                        if 'error_code' not in result.keys() and (
                                result['words_result']['number']
                                in self.cfg['license']):
                            command = 1
                            res = result
                            break
        return command, res

    def send_command(self, mode, command, number):
        if mode == 0:
            url = cfg.sys.gate_server_url
            params = {'operation': command, 'number': number}
            res = requests.get(url, params=params, timeout=5)
            return res.json()
        else:
            return "现在处在手动模式，自动指令无效。"

    def reset_states(self):
        if len(self.cur_objects) > 0:
            self.cur_objects = {}
        if self.is_close == True:
            self.is_close = False

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_path", type=str)
    parser.add_argument("--config_detection",
                        type=str,
                        default="./configs/yolov3.yaml")
    parser.add_argument("--config_classes",
                        type=str,
                        default="./configs/classes.yaml")
    parser.add_argument("--config_deepsort",
                        type=str,
                        default="./configs/deep_sort.yaml")
    parser.add_argument("--config_sys",
                        type=str,
                        default="./configs/sys_conf.yaml")
    parser.add_argument("--config_license",
                        type=str,
                        default="./configs/license.yaml")
    # parser.add_argument("--ignore_display", dest="display", action="store_false", default=True)
    parser.add_argument("--display", action="store_true")
    parser.add_argument("--frame_interval", type=int, default=1)
    parser.add_argument("--display_width", type=int, default=1920)
    parser.add_argument("--display_height", type=int, default=1080)
    # parser.add_argument("--save_path", type=str, default="./output/")
    parser.add_argument("--save_path", type=str, default="")
    parser.add_argument("--use_cuda",
                        dest="use_cuda",
                        action="store_false",
                        default=True)
    parser.add_argument(
        "--camera",
        action="store",
        dest="cam",
        # type=int,
        default=-1)
    return parser.parse_args()


def check_accesstoken(cfg, args):
    now = time.time()
    last_update = cfg.sys.baidu.access_token.fresh_time
    if not last_update or now - last_update > 5 * 24 * 3600:
        host = cfg['sys']['baidu']['access_token']['base_url']
        params = cfg['sys']['baidu']['access_token']['params']
        res = requests.get(host, params=params)
        token = res.json()['access_token']
        cfg['sys']['baidu']['access_token']['token'] = token
        logging.info('更新 access_token。')


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    args = parse_args()
    cfg = get_config()
    # cfg.merge_from_file(args.config_detection)
    cfg.merge_from_file(args.config_deepsort)
    cfg.merge_from_file(args.config_classes)
    cfg.merge_from_file(args.config_sys)
    cfg.merge_from_file(args.config_license)

    logger = get_logger()

    check_accesstoken(cfg, args)
    update_token = Timer(24 * 3600, check_accesstoken, (cfg, args))
    update_token.start()
    try:
        with VideoTracker(cfg, args, args.video_path) as vdo_trk:
            vdo_trk.run()
    except Exception as e:
        logging.exception()
        with VideoTracker(cfg, args, args.video_path) as vdo_trk:
            vdo_trk.run()
