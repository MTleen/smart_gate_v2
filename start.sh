###
 # @Description: 
 # @Author: Shengxiang Hu
 # @Github: https://github.com/MTleen
 # @Date: 2021-03-08 00:38:31
 # @LastEditors: Shengxiang Hu
 # @LastEditTime: 2021-03-17 20:31:24
 # @FilePath: /smart_gate_v2/start.sh
### 
cd /home/mathripper/Docker/smart_gate_v2
nohup /home/mathripper/anaconda3/envs/torch/bin/python -u /home/mathripper/Docker/smart_gate_v2/detect.py --camera rtsp://admin:HikLZDADB@192.168.1.27:554/h265/ch1/main > /dev/null 2>&1 &
nohup /home/mathripper/anaconda3/envs/torch/bin/gunicorn -c ./configs/gunicorn.conf.py controller:app > /dev/null 2>&1 &