'''
Description: 
Author: Shengxiang Hu
Github: https://github.com/MTleen
Date: 2021-02-01 00:41:22
LastEditors: Shengxiang Hu
LastEditTime: 2021-02-27 18:06:41
FilePath: /smart_gate_v2/man_utils/log.py
'''
import logging
import logging.config
import json
import os
import traceback


def get_logger(name='root', cfg_path='./configs/logger_config.json'):
    try:
        assert os.path.isfile(cfg_path)
        with open(cfg_path, 'r') as f:
            config = json.load(f)
            logging.config.dictConfig(config)
        return logging.getLogger('root')
    except Exception as e:
        traceback.print_exc()
        print('logger 配置文件有误，返回基础 logger！')
        logging.basicConfig(level=logging.DEBUG)
        return logging.getLogger('root')


