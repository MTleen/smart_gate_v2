import os
import cv2
import time
import argparse
import torch
import warnings
import numpy as np
import base64
import requests

from deep_sort import build_tracker
from man_utils.draw import draw_boxes
from man_utils.parser import get_config
from man_utils.log import get_logger
from man_utils.io import write_results
from man_utils.RTSCapture import RTSCapture

from matplotlib import pyplot as plt


class VideoTracker(object):
    def __init__(self, cfg, args, video_path):
        self.cfg = cfg
        self.args = args
        self.video_path = video_path
        self.cur_objects = {}
        self.logger = get_logger("root")
        self.is_close = False

        use_cuda = args.use_cuda and torch.cuda.is_available()
        if not use_cuda:
            warnings.warn("Running in cpu mode which maybe very slow!",
                          UserWarning)

        if args.display:
            cv2.namedWindow("test", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("test", args.display_width, args.display_height)

        if args.cam != -1:
            print("Using webcam " + str(args.cam))
            self.vdo = RTSCapture(args.cam)
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
            self.logger.info("Save results to {}".format(self.args.save_path))

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            print(exc_type, exc_value, exc_traceback)

    def run(self):
        results = []
        idx_frame = 0
        while self.vdo.grab():
            idx_frame += 1
            if idx_frame % self.args.frame_interval:
                continue

            start = time.time()
            _, ori_im = self.vdo.retrieve()
            im = cv2.cvtColor(ori_im, cv2.COLOR_BGR2RGB)

            # do detection
            # bbox_xywh, cls_conf, cls_ids =
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
                            self.cur_objects[str(i)]['class'] = int(c)
                            self.cur_objects[str(i)]['init'] = xyxy
                            self.cur_objects[str(i)]['current'] = xyxy
                        else:
                            self.cur_objects[str(i)]['current'] = xyxy

                    command = self.get_command(ori_im)

                    ori_im = draw_boxes(ori_im, bbox_xyxy, identities)

                    results.append(
                        (idx_frame - 1, bbox_tlwh, identities,
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
                self.logger.info("frame: {}, time: {:.03f}s, fps: {:.03f}, detection numbers: {}, tracking numbers: {}" \
                                .format(idx_frame, end - start, 1 / (end - start), bbox_xywh.shape[0], len(outputs)))
            else:
                if self.args.save_path:
                    self.writer.write(ori_im)
                end = time.time()
                if end - start < 0.2:
                    time.sleep(0.2 - (end - start))
                print(f'帧 {idx_frame} 没有对象。')

    def is_open(self):
        pass

    def get_command(self, ori_im):
        """
        开门逻辑：任何一个目标符合开门条件就开门
        关门逻辑：所有需要判定是否关门的目标都满足关门条件
        """
        for k, v in self.cur_objects.items():
            init = v['init'][0]
            current = v['current'][0]
            # 判断是否开门
            if init > 550 and current < 500:
                pic_str = base64.b64encode(cv2.imencode('.jpeg', ori_im))
                access_token = self.cfg['sys']['baidu']['access_token_url']['access_token']
                if v['class'] == 0:
                    request_url = self.cfg['sys']['baidu']['face_search']['base_url']
                    params = self.cfg['sys']['baidu']['face_search']['params']
                    params['image'] = pic_str
                    request_url = request_url + "?access_token=" + access_token
                    headers = {'content-type': 'application/json'}
                    response = requests.post(request_url, data=params, headers=headers)
                    result = response.json()
                    if result['error_code'] == 0 and len(
                            result['result']['user_list']) > 0:
                        for user in result['result']['user_list']:
                            if user['score'] > 75:
                                return 0, time.time() * 1000, result
                elif v['class'] == 2:
                    request_url = self.cfg['sys']['baidu']['license_plate'][
                        'base_url']
                    params = self.cfg['sys']['baidu']['license_plate'][
                        'params']
                    params['image'] = pic_str
                    headers = {
                        'content-type': 'application/x-www-form-urlencoded'
                    }
                    response = requests.post(request_url, data=params, headers=headers)
                    result = response.json()
                    if 'error_code' not in result.keys() and (
                    result['words_result']['number'] in self.cfg['license']):
                        return 0, time.time() * 1000, result
        
        return None

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("VIDEO_PATH", type=str)
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
    parser.add_argument("--save_path", type=str, default="./output/")
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


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    args = parse_args()
    cfg = get_config()
    # cfg.merge_from_file(args.config_detection)
    cfg.merge_from_file(args.config_deepsort)
    cfg.merge_from_file(args.config_classes)
    cfg.merge_from_file(args.config_sys)
    cfg.merge_from_file(args.config_license)

    with VideoTracker(cfg, args, video_path=args.VIDEO_PATH) as vdo_trk:
        vdo_trk.run()
