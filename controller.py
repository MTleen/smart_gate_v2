'''
Description: 门禁控制模块
Author: Shengxiang Hu
Github: https://github.com/MTleen
Date: 2021-02-07 23:12:03
LastEditors: Shengxiang Hu
LastEditTime: 2021-02-10 14:15:39
FilePath: /smart_gate_v2/controller.py
'''
from flask import Flask
from flask import request
import os
import requests
import yaml
import json
import argparse
from threading import Timer
import logging
from easydict import EasyDict as edict

from man_utils.parser import merge_from_file
from man_utils.log import get_logger
from detect import VideoTracker, check_accesstoken

app = Flask(__name__)

@app.route('/set_mode')
def set_mode():
    cfg.sys.mode = request.args.get('mode', 1)



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


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # app.run()
    args = parse_args()
    cfg = edict()
    # cfg.merge_from_file(args.config_detection)
    merge_from_file(
        cfg, args.config_deepsort, args.config_classes, args.config_sys, args.config_license)
    # merge_from_file(cfg, args.config_classes)
    # cfg.merge_from_file(args.config_sys)
    # cfg.merge_from_file(args.config_license)

    with open('./configs/test.yaml', 'w') as f:
        yaml.dump(cfg['sys'], f)

    logger = get_logger()

    check_accesstoken(cfg, args)
    update_token = Timer(24 * 3600, check_accesstoken, (cfg, args))
    update_token.start()
    try:
        with VideoTracker(cfg, args, args.video_path) as vdo_trk:
            vdo_trk.run()
    except Exception as e:
        logging.exception('检测出错')
        with VideoTracker(cfg, args, args.video_path) as vdo_trk:
            vdo_trk.run()