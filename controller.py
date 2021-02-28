'''
Description: 门禁控制模块
Author: Shengxiang Hu
Github: https://github.com/MTleen
Date: 2021-02-07 23:12:03
LastEditors: Shengxiang Hu
LastEditTime: 2021-02-27 23:52:38
FilePath: /smart_gate_v2/controller.py
'''
from flask import Flask
from flask import request
import os
from numpy.lib.histograms import histogram
import requests
import yaml
import json
import argparse
from threading import Timer, Thread
import logging
from easydict import EasyDict as edict
import time
from redis import StrictRedis

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

@app.route('/get_history')
def get_history():
    date = time.strftime('%Y-%m-%d', time.localtime())
    if redis:
        try:
            raw_history = redis.lrange(date, 0, -1)
            history = list(map(lambda x: x.decode(), raw_history))
            return json.dumps(history, ensure_ascii=False)
        except Exception:
            logging.error('redis 操作出错！')
            return 'error'
    else:
        return 'error'

def start_server():
    try:
        app.run(host='0.0.0.0',
                ssl_context=('./server/server.pem', './server/server.key'))
    except Exception:
        logging.error('服务器报错，重启服务器！')
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

    hbt = Thread(target=heartbeat)
    hbt.setDaemon(True)
    hbt.start()

    try:
        redis = StrictRedis('127.0.0.1', port=6379, db=1)
    except Exception:
        logging.error('redis 数据库连接错误！')
        redis = None

    try:
        with VideoTracker(cfg, args, args.video_path, redis=redis) as vdo_trk:
            vdo_trk.run()
    except Exception as e:
        logging.exception('检测出错')
        with VideoTracker(cfg, args, args.video_path, redis=redis) as vdo_trk:
            vdo_trk.run()
