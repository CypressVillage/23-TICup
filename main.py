import sensor, image, time, math

thresholds = (100, 29, -128, 81, 2, 58) # 激光灯在纸上颜色的阈值，可以执行调节
thresholds = (99, 100, -1, 1, -1, 1)
from pyb import Pin
ain1 = Pin('P0',Pin.OUT_PP)#激光模块的引脚
ain1.high()
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
#sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((240, 240)) # 240x240 center pixels of VGA
sensor.set_auto_gain(False) # must be turned off for color tracking
sensor.skip_frames(20)
sensor.set_auto_exposure(False, 1400)
#sensor.set_auto_whitebal(False) #如果使用彩图读取，则白平衡需要关闭，即sensor.set_auto_whitebal(False)
clock = time.clock()

def color_blob(threshold):
    blobs = img.find_blobs([threshold])
    if len(blobs) == 1 or True:
        # Draw a rect around the blob.
        b = blobs[0]
        #print(b)
        img.draw_rectangle(b[0:4]) # rect
        cx = b[5]
        cy = b[6]
        img.draw_cross(b[5], b[6]) # cx, cy
        print(b[5], b[6])
    return 160, 120

while(True):
    clock.tick()
    img = sensor.snapshot()
    img = img.binary([(170, 255)])
    img = img.dilate(2)
    blobs = img.find_blobs([thresholds])
    if blobs:
        for blob in blobs:
            img.draw_rectangle(blob[0:4]) # rect
            img.draw_cross(blob[5], blob[6]) # cx, cy
        print('have')
    else:
        print("don't have")
    #print(clock.fps())
