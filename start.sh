###
 # @Description: 
 # @Author: Shengxiang Hu
 # @Github: https://github.com/MTleen
 # @Date: 2021-03-08 00:38:31
 # @LastEditors: Shengxiang Hu
 # @LastEditTime: 2021-03-08 00:39:06
 # @FilePath: /smart_gate_v2/start.sh
### 
cd /home/mathripper/Docker/smart_gate_v2
/home/mathripper/anaconda3/envs/torch/bin/gunicorn -c gunicorn.conf.py controller:app