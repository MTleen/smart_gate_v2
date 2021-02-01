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

    # formatter = logging.Formatter(
    #     # fmt='%(asctime)s [%(levelname)s]: %(filename)s(%(funcName)s:%(lineno)s) >> %(message)s')
    #     fmt='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # handler = logging.StreamHandler()
    # handler.setFormatter(formatter)

    # logger = logging.getLogger(name)
    # logger.setLevel(logging.INFO)
    # logger.addHandler(handler)
    # return logger


