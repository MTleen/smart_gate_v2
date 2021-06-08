#!/bin/sh
###
 # @Description: 
 # @Author: Shengxiang Hu
 # @Github: https://github.com/MTleen
 # @Date: 2021-05-10 18:17:25
 # @LastEditors: Shengxiang Hu
 # @LastEditTime: 2021-05-10 18:26:30
 # @FilePath: /smart_gate_v2/listen.sh
### 
workdir=$(cd $(dirname $0); pwd)
ps -fe | grep -v grep | grep "/home/mathripper/anaconda3/envs/torch/bin/python -u /home/mathripper/Docker/smart_gate_v2/detect.py --camera rtsp://admin:HikLZDADB@192.168.1.27:554/h265/ch1/main"
if [ $? -ne 0 ]
then
{
	date > $workdir/logs/listen.log
	echo "detecting process stoped, restart" >> $workdir/logs/listen.log
	nohup /home/mathripper/anaconda3/envs/torch/bin/python -u /home/mathripper/Docker/smart_gate_v2/detect.py --camera rtsp://admin:HikLZDADB@192.168.1.27:554/h265/ch1/main > /dev/null 2>&1 &
}
else
{
	date > $workdir/logs/listen.log
	echo "detecting is running" >> $workdir/logs/listen.log
}
fi
