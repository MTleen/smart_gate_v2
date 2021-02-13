'''
Description: 
Author: Shengxiang Hu
Github: https://github.com/MTleen
Date: 2021-02-01 00:41:22
LastEditors: Shengxiang Hu
LastEditTime: 2021-02-10 14:07:36
FilePath: /smart_gate_v2/man_utils/parser.py
'''
import os
import yaml
from easydict import EasyDict as edict

class YamlParser(edict):
    """
    This is yaml parser based on EasyDict.
    """
    def __init__(self, cfg_dict=None, config_file=None):
        if cfg_dict is None:
            cfg_dict = {}

        if config_file is not None:
            assert(os.path.isfile(config_file))
            with open(config_file, 'r') as fo:
                cfg_dict.update(yaml.load(fo.read(), Loader=yaml.FullLoader))

        super(YamlParser, self).__init__(cfg_dict)


    def merge_from_file(self, config_file):
        with open(config_file, 'r') as fo:
            self.update(yaml.load(fo.read(), Loader=yaml.FullLoader))


    def merge_from_dict(self, config_dict):
        self.update(config_dict)


def get_config(config_file=None):
    return YamlParser(config_file=config_file)


def merge_from_file(cfg, *config_files):
    for config_file in config_files:
        with open(config_file, 'r') as fo:
            cfg.update(yaml.load(fo.read(), Loader=yaml.FullLoader))


if __name__ == "__main__":
    cfg = YamlParser(config_file="../configs/classes.yaml")
    cfg.merge_from_file("../configs/deep_sort.yaml")

    import ipdb; ipdb.set_trace()