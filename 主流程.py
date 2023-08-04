# 主函数流程(红)
import sensor, image, time, math
from pyb import Pin, Servo, ExtInt, delay
from pid import PID

'''阈值定义'''
thresholds_redpoint_base = [
(0, 100, 18, 62, -128, 12),
#(48, 75, 36, 74, -15, 25), # 白板红光，方框比较小，但是不能跟踪黑色部分👍
#(68, 86, 12, 59, -95, 112), # 4号上午实测
#(95, 100, -5, 5, -5, 5), # 全白
#(0, 100, 21, 127, -38, 127), # 白板黑胶带红光，都可以跟踪，但是方框比较大
]
thresholds_redpoint_blackline = [
(0, 100, 15, 53, -30, 40), # 3号上午黑线红点👍
(0, 100, 5, 33, -128, 127),
]
thresholds_greenpoint_base = [
(65, 100, -79, 6, -2, 85)
]
thresholds_whitebackground = [
# (40, 78, -19, 4, -22, -3), # 3号上午白纸背景
# (48, 68, -16, 27, -20, -1), # 3号下午白板背景
# (46, 79, -23, -6, -5, 5),   # 4号上午残破openmv
#(49, 100, -128, 127, -128, 127), # 隔一段时间准
(58, 79, -128, 127, -128, 127), # 开始几帧准
(56, 80, -15, 4, -15, 4),
]
'''常量定义'''
corr_val = 1.6                                                     # 畸变系数
white_background_size_min = 3000                                    # 白纸背景最小面积
pan_servo_default_angle = 13                                         # 舵机水平方向默认角度
tilt_servo_default_angle = -40                                      # 舵机垂直方向默认角度
pan_servo_angle_limit = [-20, 25]
tilt_servo_angle_limit = [-40, -20]
'''变量定义'''
x1, y1, x2, y2, x3, y3, x4, y4 = 0, 0, 0, 0, 0, 0, 0 ,0             # 白纸背景坐标
centerx, centery = 0, 0                                             # 白纸背景中心坐标
px1, py1, px2, py2, px3, py3, px4, py4 = 0, 0, 0, 0, 0, 0, 0 ,0     # 铅笔线坐标
rx, ry = 0, 0                                                       # 红点坐标
mode = ''                                                           # 模式

'''初始化PID'''
#pid_pan = PID(p=0.07, i=0.02, d=0, imax=90) # 舵机水平方向PID
#pid_tilt = PID(p=0.07, i=0.15, d=0.02, imax=90) # 舵机垂直方向PID
#pid_tilt = PID(p=0.03, i=0.0, d=0.0, imax=90) # 舵机垂直方向PID

#pid_pan = PID(p=0.1, i=0.05, d=0, imax=90) # 舵机水平方向PID
#pid_tilt = PID(p=0.1, i=0.1, d=0, imax=90) # 舵机垂直方向PID

# 4号下午5点半调参
pid_pan = PID(p=0.1, i=0.05, d=0, imax=90) # 舵机水平方向PID
pid_tilt = PID(p=0.1, i=0.0, d=0, imax=90) # 舵机垂直方向PID

'''初始化按键'''
p_reset = Pin('P1', Pin.IN, Pin.PULL_DOWN)
p_start = Pin('P2', Pin.IN, Pin.PULL_DOWN)

'''初始化舵机'''
pan_servo = Servo(1) # P7水平
tilt_servo = Servo(2) # P8竖直
# TODO：如果有时间去调
# pan_servo.calibration(500, 2500, 500)
# tilt_servo.calibration(500, 2500, 500)
pan_servo.angle(pan_servo_default_angle, 5)
tilt_servo.angle(tilt_servo_default_angle, 5)

'''初始化摄像头'''
sensor.reset()
#sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.set_windowing((240, 240)) # 240x240 center pixels of QQVGA
sensor.set_auto_gain(False) # 如果使用彩图读取，则自动增益需要关闭
sensor.skip_frames(20) # 丢失一些帧，等待摄像头初始化完成
# sensor.set_auto_exposure(False, 500) # 关闭自动曝光，这个操作会导致图像变暗
sensor.set_auto_whitebal(False) #如果使用彩图读取，则白平衡需要关闭，即sensor.set_auto_whitebal(False)
clock = time.clock()

def callback_reset(line):
    delay(1000)
    tilt_servo.angle(90)
    pan_servo.angle(63)
    print("一次中断完成1111")

def callback_start(line):
    delay(1000)
    tilt_servo.angle(0)
    pan_servo.angle(83)
    print("一次中断完成2222")

ext_reset = ExtInt(p_reset, ExtInt.IRQ_RISING, Pin.PULL_DOWN, callback_reset)
ext_start = ExtInt(p_start, ExtInt.IRQ_RISING, Pin.PULL_DOWN, callback_start)


def find_red_point():
    '''
    找到红点的坐标，返回x, y

    如果使用第一种阈值就能找到红点，就使用第一种阈值，否则使用第二种阈值的均值
    '''
    x, y, sumx, sumy = 0, 0, 0, 0
    find_point = False
    blobs = []
    print('finding red point')
    while not find_point:
        clock.tick() # 用于计算FPS
        img = sensor.snapshot().lens_corr(corr_val)
        # 用第一种阈值找红点
        blobs = img.find_blobs(thresholds_redpoint_base)
        if blobs and blobs[0]:
            x, y = blobs[0].cx(), blobs[0].cy()
            if not (x-5 <= x <= x2+5 and y2-10 <= y <= y3+10): continue
            break

        # 用第二种阈值找红点
        blobs = img.find_blobs(thresholds_redpoint_blackline)
        if blobs:
            nblob = 0
            for blob in blobs:
                if not (x1 <= blob[5] <= x2 and y2 <= blob[6] <= y3): continue
                nblob += 1
                sumx += blob[5]
                sumy += blob[6]
            if nblob == 0: continue
            x, y = sumx / nblob, sumy / nblob
            find_point = True
    print('find red point: ', x, y)
    img.draw_cross(int(x), int(y))
    return x, y

def find_white_background():
    '''
    找到白纸背景，返回白纸背景的坐标

    返回值：x1, y1, x2, y2, x3, y3, x4, y4（从左上方顺时针旋转）
    '''
    find_background_times = 0
    x1, y1, x2, y2, x3, y3, x4, y4 = 0, 0, 0, 0, 0, 0, 0 ,0
    while find_background_times < 5:
        img = sensor.snapshot().lens_corr(corr_val)
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

    x1, y1 = x1 / find_background_times, y1 / find_background_times
    x2, y2 = x2 / find_background_times, y2 / find_background_times
    x3, y3 = x3 / find_background_times, y3 / find_background_times
    x4, y4 = x4 / find_background_times, y4 / find_background_times
    print(f'find white background: ({x1}, {y1}), ({x2}, {y2}), ({x3}, {y3}), ({x4}, {y4})')
    return x1, y1, x2, y2, x3, y3, x4, y4

def calculate_pencil_line():
    '''铅笔线是50x50，外边框是60x60，根据外边框计算铅笔线'''
    dx = (x2 - x1) / 12
    dy = (y2 - y1) / 12
    px1, py1 = x1 + dx, y1 + dy
    px2, py2 = x2 - dx, y2 + dy
    px3, py3 = x3 - dx, y3 - dy
    px4, py4 = x4 + dx, y4 - dy
    # 画
    # img = sensor.snapshot()
    # img.draw_line((px1, py1, px2, py2))
    # # print('sep')
    # img.draw_line((px2, py2, px3, py3))
    # img.draw_line((px3, py3, px4, py4))
    # img.draw_line((px4, py4, px1, py1))
    print(f'calculate pencil line: ({px1}, {py1}), ({px2}, {py2}), ({px3}, {py3}), ({px4}, {py4})')
    return px1, py1, px2, py2, px3, py3, px4, py4

def find_A4_rectangle():
    '''找到A4纸矩形，返回矩形4点的坐标'''
    clock.tick()
    img = sensor.snapshot().lens_corr(corr_val)
    for r in img.find_rects(threshold = 45000):
        # img.draw_rectangle(r.rect(), color = (255, 0, 0))
        for p in r.corners():
            # img.draw_circle(p[0], p[1], 5, color = (0, 255, 0))  #在四个角上画圆
            pass

    # 找到A4纸的四个角
    return r.corners()[0].x(), r.corners()[0].y(), r.corners()[1].x(), r.corners()[1].y(), r.corners()[2].x(), r.corners()[2].y(), r.corners()[3].x(), r.corners()[3].y()


def servo_step(pan_error, tilt_error):
    '''
    舵机转动一下，这里使用了pid控制

    根据pan_error, tilt_error计算舵机转动的角度，然后转动一下舵机

    每调用一次用时100ms左右
    '''

    print('pan_error, tilt_error: ', pan_error, tilt_error)
    pan_output = pid_pan.get_pid(pan_error, 1)
    tilt_output = pid_tilt.get_pid(tilt_error, 1)
    # if -1.5 < pan_output < 0:
    #     pan_output = 0
    # elif 0 < pan_output < 1.5:
    #     pan_output = 0
    # if -1.5 < tilt_output < 0:
    #     tilt_output = 0
    # elif 0 < tilt_output < 1.5:
    #     tilt_output = 0

    print('delta angle(pan_output, tilt_output): ', pan_output, tilt_output)
    delta_x = pan_servo.angle() - pan_output
    delta_y = tilt_servo.angle() + tilt_output
    if pan_servo_angle_limit[0] < delta_x <= pan_servo_angle_limit[1]:
        #pan_servo.angle(delta_x, 5)
        print('x set angle:', pan_output)
    if tilt_servo_angle_limit[0] < delta_y <= tilt_servo_angle_limit[1]:
        tilt_servo.angle(delta_y, 5)
        print('y set angle:', tilt_output)
    delay(50)


pid_x_limit = 0                                                     # PID允许的x方向误差
pid_y_limit = 2                                                     # PID允许的y方向误差
def move2point(x, y):
    '''
    让rx,ry移动到x,y

    '''
    print('move to point: ', x, y)
    while(True):
        rx, ry = find_red_point()
        pan_error, tilt_error = rx - x, ry - y
        pan_error = 0 # 只调y用
        if (-pid_x_limit < pan_error <= pid_x_limit) and (-pid_y_limit < tilt_error <= pid_y_limit):
            break
        servo_step(pan_error, tilt_error)

def trace_rectangle(x1, y1, x2, y2, x3, y3, x4, y4):
    move2point(x1, y1)
    move2point(x2, y2)
    move2point(x3, y3)
    move2point(x4, y4)

def move2center():
    move2point(centerx, centery)

def servo_reset():
    '''
    舵机复位，如果中心点已知，则移动到中心点，否则移动到(0, 0)
    '''
    if centerx == 0 and centery == 0:
        pan_servo.angle(pan_servo_default_angle)
        tilt_servo.angle(tilt_servo_default_angle)
    else:
        move2center()
    print('servo reset done')

def wait_mode_btn():
    '''等待模式按钮，切换模式'''
    global mode
    print('wait mode btn')

def process_init():
    global x1, y1, x2, y2, x3, y3, x4, y4
    global centerx, centery
    global px1, py1, px2, py2, px3, py3, px4, py4
    global rx, ry
    #servo_reset() # 舵机复位
    '''初始化各global位置变量'''
    print('process initing...')
    x1, y1, x2, y2, x3, y3, x4, y4 = find_white_background()
    centerx, centery = (x1 + x2 + x3 + x4) / 4, (y1 + y2 + y3 + y4) / 4
    print(f'center: ({centerx}, {centery})')
    px1, py1, px2, py2, px3, py3, px4, py4 = calculate_pencil_line()
    rx, ry = find_red_point()
    mode = ''
    print('process init done.')

def task_1():
    move2center()

def task_2():
    x1, y1, x2, y2, x3, y3, x4, y4 = calculate_pencil_line()
    trace_rectangle(x1, y1, x2, y2, x3, y3, x4, y4)


'''程序入口'''
process_init()

#task_1()
#task_1()
#task_2()
#tx, ty = find_red_point()
#move2point(tx,ty-5)
print('done')
while(True):
    find_white_background()
    ##find_red_point()
    #move2center()
    pass

#move2center()
#move2center()
#move2center()
#move2center()
#move2center()

