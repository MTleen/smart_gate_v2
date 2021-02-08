'''
Description: 门禁控制模块
Author: Shengxiang Hu
Github: https://github.com/MTleen
Date: 2021-02-07 23:12:03
LastEditors: Shengxiang Hu
LastEditTime: 2021-02-09 02:03:28
FilePath: /smart_gate_v2/controller.py
'''
from flask import Flask
from flask import request
import os
import requests
import yaml
import argparse
from threading import Timer

from man_utils.parser import get_config
from man_utils.log import get_logger
from detect import VideoTracker, check_accesstoken

app = Flask(__name__)
mode = 0

def send_command(mode):
    if mode == 0:
        url = cfg.sys.gate_server_url
        params = {
            'operation': request.form['command'],
            'number': request.form['number']
        }
        res = requests.get(url, params=params, timeout=5)
        return res.json()
    else:
        return "现在处在手动模式，自动指令无效。"

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


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    app.run()

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

    with VideoTracker(cfg, args, video_path=args.VIDEO_PATH) as vdo_trk:
        vdo_trk.run()