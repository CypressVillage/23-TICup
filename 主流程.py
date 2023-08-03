# 主函数流程(红)
import sensor, image, time, math
from pyb import Pin

'''常量定义'''
white_background_size_min = 3000 # 白纸背景最小面积
'''阈值定义'''
thresholds_redpoint = [
#(95, 100, -5, 5, -5, 5), # 全白
#(0, 100, 21, 127, -38, 127), # 白板黑胶带红光，都可以跟踪，但是方框比较大
(48, 75, 36, 74, -15, 25), # 白板红光，方框比较小，但是不能跟踪黑色部分
]
thresholds_whitebackground = [
(40, 78, -19, 4, -22, -3), # 3号上午白纸背景
#(64, 83, -19, 4, -22, -3)
]

'''初始化摄像头'''
sensor.reset()
#sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.set_windowing((240, 240)) # 240x240 center pixels of QQVGA
sensor.set_auto_gain(False) # 如果使用彩图读取，则自动增益需要关闭
sensor.skip_frames(20) # 丢失一些帧，等待摄像头初始化完成
#sensor.set_auto_exposure(False, 1400) # 关闭自动曝光，这个操作会导致图像变暗
sensor.set_auto_whitebal(False) #如果使用彩图读取，则白平衡需要关闭，即sensor.set_auto_whitebal(False)
clock = time.clock()


def find_red_point():
    '''找到红点的坐标，返回x, y'''
    x, y, sumx, sumy = 0, 0, 0, 0
    find_point = False
    blobs = []
    while not find_point:
        img = sensor.snapshot()
        blobs = img.find_blobs(thresholds_whitebackground)
        if blobs:
            for blob in blobs:
                img.draw_rectangle(blob[0:4]) # rect
                img.draw_cross(blob[5], blob[6]) # cx, cy
                sumx += blob[5]
                sumy += blob[6]
            x, y = int(sumx / len(blobs)), int(sumy / len(blobs))
            print('find red point: ', x, y)
            find_point = True
        else:
            print("find red point: not found")
    return x, y

def find_white_background():
    '''
    找到白纸背景，返回白纸背景的坐标

    返回值：x1, y1, x2, y2, x3, y3, x4, y4（从左下方逆时针旋转）
    '''
    find_background_times = 0
    x1, y1, x2, y2, x3, y3, x4, y4 = 0, 0, 0, 0, 0, 0, 0 ,0
    while find_background_times < 5:
        img = sensor.snapshot()
        blobs = img.find_blobs(thresholds_whitebackground)
        if not blobs: continue
        for blob in blobs:
            if blob[2] * blob[3] > white_background_size_min:
                find_background_times += 1
                x1 += blob[0]
                y1 += blob[1]
                x2 += blob[0] + blob[2]
                y2 += blob[1]
                x3 += blob[0] + blob[2]
                y3 += blob[1] + blob[3]
                x4 += blob[0]
                y4 += blob[1] + blob[3]
                img.draw_rectangle(blob[0:4])
                # print('find white background: ', blob)

    x1, y1 = int(x1 / find_background_times), int(y1 / find_background_times)
    x2, y2 = int(x2 / find_background_times), int(y2 / find_background_times)
    x3, y3 = int(x3 / find_background_times), int(y3 / find_background_times)
    x4, y4 = int(x4 / find_background_times), int(y4 / find_background_times)
    print(f'find white background: ({x1}, {y1}), ({x2}, {y2}), ({x3}, {y3}), ({x4}, {y4})')
    return x1, y1, x2, y2, x3, y3, x4, y4

def calculate_pencil_line():
    '''铅笔线是50x50，外边框是60x60，根据外边框计算铅笔线'''
    dx = (x2 - x1) / 12
    dy = (y2 - y1) / 12
    px1, py1 = int(x1 + dx), int(y1 + dy)
    px2, py2 = int(x2 - dx), int(y2 + dy)
    px3, py3 = int(x3 - dx), int(y3 - dy)
    px4, py4 = int(x4 + dx), int(y4 - dy)
    # 画
    img = sensor.snapshot()
    img.draw_line((px1, py1, px2, py2))
    img.draw_line((px2, py2, px3, py3))
    img.draw_line((px3, py3, px4, py4))
    img.draw_line((px4, py4, px1, py1))
    return px1, py1, px2, py2, px3, py3, px4, py4

def find_A4_rectangle():
    '''找到A4纸矩形，返回矩形4点的坐标'''
    # return x1, y1, x2, y2, x3, y3, x4, y4
    return 0,1,2,3,4,5,6,7

def move2point(x, y):
    '''让px,py移动到x,y
    用法: px, py = move2point(x, y)'''
    # pid(x, y, px, py)
    print('move to point: ', x, y)
    return x, y

def trace_rectangle(x1, y1, x2, y2, x3, y3, x4, y4):
    move2point(x1, y1)
    move2point(x2, y2)
    move2point(x3, y3)
    move2point(x4, y4)

def reset(px, py):
    move2point(centerx, centery)

def wait_mode_btn():
    '''等待模式按钮，切换模式'''
    global mode
    print('wait mode btn')
    #mode = 'trace_A4Rectangle'

'''初始化各global位置变量'''
x1, y1, x2, y2, x3, y3, x4, y4 = find_white_background()
px1, py1, px2, py2, px3, py3, px4, py4 = calculate_pencil_line()
centerx, centery = (x1 + x2 + x3 + x4) / 4, (y1 + y2 + y3 + y4) / 4
rx, ry = find_red_point()
mode = 'reset_'

while(True):
    wait_mode_btn()

    if mode == 'reset':
        reset(rx, ry)
    elif mode == 'trace_border':
        # trace_rectangle(x1, y1, x2, y2, x3, y3, x4, y4)
        pass
    elif mode == 'trace_A4Rectangle':
        # trace_rectangle(find_A4_rectangle())
        pass
    else:
        # find_red_point()
        x1, y1, x2, y2, x3, y3, x4, y4 = find_white_background()
        print(calculate_pencil_line())
