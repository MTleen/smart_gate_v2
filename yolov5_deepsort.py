import os
import cv2
import time
import argparse
import torch
import warnings
import numpy as np

from detector import build_detector
from deep_sort import build_tracker
from man_utils.draw import draw_boxes
from man_utils.parser import get_config
from man_utils.log import get_logger
from man_utils.io import write_results


class VideoTracker(object):
    def __init__(self, cfg, args, video_path):
        self.cfg = cfg
        self.args = args
        self.video_path = video_path
        self.logger = get_logger("root")

        use_cuda = args.use_cuda and torch.cuda.is_available()
        if not use_cuda:
            warnings.warn("Running in cpu mode which maybe very slow!",
                          UserWarning)

        if args.display:
            cv2.namedWindow("test", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("test", args.display_width, args.display_height)

        if args.cam != -1:
            print("Using webcam " + str(args.cam))
            self.vdo = cv2.VideoCapture(args.cam)
        else:
            self.vdo = cv2.VideoCapture()
        # self.detector = build_detector(cfg, use_cuda=use_cuda)
        self.detector = torch.hub.load('ultralytics/yolov5',
                                       'yolov5s',
                                       pretrained=True,
                                       force_reload=False)
        self.detector.conf = 0.5
        self.detector.classes = [0, 2]

        self.deepsort = build_tracker(cfg, use_cuda=use_cuda)
        # self.class_names = self.detector.class_names

    def __enter__(self):
        if self.args.cam != -1:
            ret, frame = self.vdo.read()
            assert ret, "Error: Camera error"
            self.im_width = frame.shape[0]
            self.im_height = frame.shape[1]

        else:
            assert os.path.isfile(self.video_path), "Path error"
            self.vdo.open(self.video_path)
            self.im_width = int(self.vdo.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.im_height = int(self.vdo.get(cv2.CAP_PROP_FRAME_HEIGHT))
            assert self.vdo.isOpened()

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
            if len(detector_result.pred) > 0 and len(detector_result.pred[0] > 0):
                bbox_xywh = detector_result.xywh[0][:, :4]
                cls_conf = detector_result.pred[0][:, 4]
                cls = detector_result.pred[0][:, -1]
                # select person class
                # 已经在 detector 中做限制，所以此处已不需要
                # mask = cls_ids == 0

                # bbox_xywh = bbox_xywh[mask]
                # bbox dilation just in case bbox too small, delete this line if using a better pedestrian detector
                # bbox_xywh[:, 3:] *= 1.2
                # cls_conf = cls_conf[mask]

                # do tracking
                outputs = self.deepsort.update(bbox_xywh, cls_conf, im)

                # draw boxes for visualization
                if len(outputs) > 0:
                    bbox_tlwh = []
                    bbox_xyxy = outputs[:, :4]
                    # bbox_xyxy = self.deepsort._xywh_to_xyxy(bbox_xywh)
                    identities = outputs[:, -1]
                    ori_im = draw_boxes(ori_im, bbox_xyxy, identities)

                    for bb_xyxy in bbox_xyxy:
                        bbox_tlwh.append(self.deepsort._xyxy_to_tlwh(bb_xyxy))

                    results.append((idx_frame - 1, bbox_tlwh, identities))

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
                self.logger.info(f'帧 {idx_frame} 没有对象。')
                


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("VIDEO_PATH", type=str)
    parser.add_argument("--config_detection",
                        type=str,
                        default="./configs/yolov3.yaml")
    parser.add_argument("--config_deepsort",
                        type=str,
                        default="./configs/deep_sort.yaml")
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
    parser.add_argument("--camera",
                        action="store",
                        dest="cam",
                        # type=int,
                        default=-1)
    return parser.parse_args()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    args = parse_args()
    cfg = get_config()
    cfg.merge_from_file(args.config_detection)
    cfg.merge_from_file(args.config_deepsort)

    with VideoTracker(cfg, args, video_path=args.VIDEO_PATH) as vdo_trk:
        vdo_trk.run()
