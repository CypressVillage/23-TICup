# openmv控制舵机

import sensor, image, time, pyb

# 舵机初始化
servo = pyb.Servo(1) # P7

#1:8
#2:-27
servo.angle(8)
