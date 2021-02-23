'''
Description: 门禁控制模块
Author: Shengxiang Hu
Github: https://github.com/MTleen
Date: 2021-02-07 23:12:03
LastEditors: Shengxiang Hu
LastEditTime: 2021-02-23 17:20:23
FilePath: /smart_gate_v2/controller.py
'''
from flask import Flask
from flask import request
import os
import requests
import yaml
import json
import argparse
from threading import Timer, Thread
import logging
from easydict import EasyDict as edict

from man_utils.parser import get_config
from man_utils.log import get_logger
from detect import VideoTracker, check_accesstoken, heartbeat, parse_args

app = Flask(__name__)

@app.route('/set_mode')
def set_mode():
    mode = request.args.get('mode')
    cfg.sys.mode = int(mode)
    logging.info(f'设置模式：{mode}')
    return 'ok'

@app.route('/get_whitelist')
def get_white_list():
    return json.dumps(cfg.sys.white_list, ensure_ascii=False)

@app.route('/get_mode')
def get_mode():
    return {'1': '自动模式', '0': '手动模式'}[str(cfg.sys.mode)]

@app.route('/send_command')
def send_command():
    command = request.args.get('operation')
    url = cfg.sys.manual_command_url
    print(command)
    res = requests.get(url, params={'operation': command})
    if res.status_code == 200:
        return 'ok'
    else:
        return 'error'
    # return 'ok'

# @app.route('/test')
# def test():
#     print(1)
#     return 'test'

def start_server():
    app.run(host='0.0.0.0',
            ssl_context=('./server/server.pem', './server/server.key'))
    start_server()
    


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # 启动服务器
    Thread(target=start_server).start()

    args = parse_args()
    cfg = get_config()
    cfg.merge_from_file(args.config_deepsort)
    cfg.merge_from_file(args.config_classes)
    cfg.merge_from_file(args.config_sys)
    cfg.merge_from_file(args.config_license)

    logger = get_logger()

    check_accesstoken(cfg, args)
    heartbeat()

    try:
        with VideoTracker(cfg, args, args.video_path) as vdo_trk:
            vdo_trk.run()
    except Exception as e:
        logging.exception('检测出错')
        with VideoTracker(cfg, args, args.video_path) as vdo_trk:
            vdo_trk.run()
