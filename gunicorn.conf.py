'''
Description: 
Author: Shengxiang Hu
Github: https://github.com/MTleen
Date: 2021-03-07 22:28:59
LastEditors: Shengxiang Hu
LastEditTime: 2021-03-08 00:22:33
FilePath: /smart_gate_v2/gunicorn.conf.py
'''
workers = 5  # 定义同时开启的处理请求的进程数量，根据网站流量适当调整
worker_class = "gevent"  # 采用gevent库，支持异步处理请求，提高吞吐量
bind = "0.0.0.0:5000"
certfile = "./server/server.pem"
keyfile = "./server/server.key"