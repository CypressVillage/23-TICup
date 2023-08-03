# Untitled - By: liuha - 周三 8月 2 2023
import sensor, image, time, car
from time import sleep
'''
声明库部分
'''
#声明屏幕，程欢欢智能小车专属库。
screen=car.screen()
#声明蜂鸣器，程欢欢智能小车专属库。
buzzer=car.buzzer()

'''
全局变量
'''
pencil_points = [[67, 30], [248, 16], [294, 216], [37, 229], [166, 110]]  #铅笔画的方形的定点坐标和中心点坐标，共5组
laser_on_pencil_servo_value = [[102.243, 72.6351], [79.8784, 71.8379], [79.5676, 96.3784], [102.689, 96.5541], [91.6757, 84.8243], [102.392, 72.3919], [79.7973, 71.7027], [79.6081, 95.6487], [102.851, 96.2297], [91.3379, 84.4189]] #激光在铅笔痕迹上时，舵机的角度。用于校准
servo_rotation = 1  #自转轴舵机序号，程欢欢智能小车专属库。
servo_pitch = 0 #仰俯轴舵机序号，程欢欢智能小车专属库。
servo_rotation_value = 90  #两个舵机的当前角度。程欢欢小车体系中，以度为单位，支持浮点。
servo_pitch_value = 90  #这组变量建议固定初值为90。
servo_rotation_limit = [30,110]  #两个舵机的限位值，按需设置
servo_pitch_limit = [30,110]
servo_rotation_direction = False    #自转轴舵机的方向，数值增加，光点向右为真，反之为伪
servo_pitch_direction = True    #仰俯轴舵机的方向，数值增加，光点向下为真，反之为伪


laser_threshold=[(30, 75, 30, 90, 0, 60)]#[(85, 100, -20, 20, -20, 20)]   #激光颜色阈值
black_line_threshold=[(0, 30, -20, 20, -20, 20)]   #激光颜色阈值

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(True)  #针对我的硬件，颠倒画面
sensor.set_hmirror(True)

sensor.set_brightness(-3)   #设置亮度
sensor.set_contrast(3) #对比度
#sensor.set_gainceiling(2)   #增益上限
#sensor.set_auto_gain(False,gain_db=-1) #增益
sensor.set_auto_exposure(False,500)  #曝光速度

clock = time.clock()

servo = car.servo_motor() #声明激光电源，因为激光电源用的是舵机供电
servo.vout_off()  #关闭激光
servo.vout_on()  #打开激光
servo.channel_off(servo_rotation)   #关闭两个舵机信号
servo.channel_off(servo_pitch)
'''
激光云台，以绝对舵机角度移动.
注意，所有涉及舵机控制的程序，一定要包装成子函数再调用，防止超出范围损坏云台。
'''
def laser_move_by_degress(rotation, pitch):
    global servo_rotation,servo_pitch,servo_rotation_limit,servo_pitch_limit
    if servo_rotation_limit[0] < rotation < servo_rotation_limit[1]:
        servo.degree(servo_rotation,rotation)
    if servo_pitch_limit[0] < pitch < servo_pitch_limit[1]:
        servo.degree(servo_pitch,pitch)

'''
激光云台以画布增量坐标移动，坐标为原始值，并非实际像素值。
仅用于闭环移动程序
'''
def laser_move_increment(x,y):
    global servo_rotation,servo_pitch,servo_rotation_value,servo_pitch_value,\
        servo_rotation_limit,servo_pitch_limit,servo_rotation_direction,servo_pitch_direction
    if not servo_rotation_direction:#根据设置，是否调转x轴方向
        x = -x
    if not servo_pitch_direction:#根据设置，是否调转y轴方向
        y = -y
    #在限位内，驱动X轴，Y轴移动
    if servo_rotation_limit[0] < servo_rotation_value + x < servo_rotation_limit[1]:
        servo_rotation_value += x
        servo.degree(servo_rotation,servo_rotation_value)
    if servo_pitch_limit[0] < servo_pitch_value + y < servo_pitch_limit[1]:
        servo_pitch_value += y
        servo.degree(servo_pitch,servo_pitch_value)
'''
激光云台闭环移动到目标点（画布像素点）
只用了比例P，可能是我的舵机够好
要加PID可以使用OpenMV自带的PID库，直接加上
参数：
target_x,target_y-希望移动到的坐标
laser_x,laser_y-激光点的坐标
'''
def laser_move_to_traget_close_loop(target_x, target_y, laser_x, laser_y):
    laser_move_increment((target_x - laser_x)*0.03, (target_y - laser_y)*0.03)

'''
现场校准程序，手动将激光点，从左上角开始，顺时针依次落在铅笔正方形的角上
然后按下触屏（或其他输入装置）
最后落在中心点上，一共5个点。
'''
def cam_calibration():
    global pencil_points,laser_threshold
    pencil_points = []  #先清空原有数据
    sensor.set_brightness(-3)   #设置亮度
    sensor.set_contrast(3) #对比度
    sensor.set_auto_exposure(False,500)  #曝光速度
    loop = True
    while loop:
        img = sensor.snapshot()
        blobs = img.find_blobs(laser_threshold)
        if blobs:
            img.draw_cross(blobs[0].cx(),blobs[0].cy(),color=(0,0,0))
            screen.get_touch()  #获取触屏触摸
            if screen.touch_exist():    #如果触摸存在
                if len(pencil_points)<5:#少于5组数据，未输入完成
                    #坐标追加如
                    pencil_points.append([blobs[0].cx(),blobs[0].cy()])
                    buzzer.frequency(500)
                    sleep(0.5)
                    buzzer.frequency(0)
                else: #等于5组数据，输入完成
                    loop = False
        for n in range(len(pencil_points)):
            img.draw_cross(pencil_points[n][0],pencil_points[n][1],color=(0,0,255))
            img.draw_string(pencil_points[n][0],pencil_points[n][1],str(n),color=(0,0,255))

        screen.display(img)
'''
激光棒校准程序
使激光点落在铅笔方框的四个定点
和一个中心点，记录舵机角度
'''
def laser_calibration():
    global laser_threshold,pencil_points,laser_on_pencil_servo_value,laser_threshold,pencil_points

    sensor.set_brightness(-3)   #设置亮度
    sensor.set_contrast(3) #对比度
    sensor.set_auto_exposure(False,500)  #曝光速度
    servo.channel_on(servo_rotation)   #打开两个舵机信号
    servo.channel_on(servo_pitch)
    laser_move_by_degress(90,90)

    laser_point_stable_n = 0 #用于判断激光点是否稳定的计数

    move_pencil_step_tot = 30 #每个边细分成多少份进行移动
    move_pencil_point_n = 0  #临时存储变量，用于存储当前执行到铅笔方形的哪个角
    move_pencil_step_n = 0  #临时存储变量，用于存储在当前边的第几步。步总数参考上述变量。
    laser_calibration_enter_mode = True #录入模式，停止移动。录入完成后继续移动。
    loop = True
    while loop:
        img = sensor.snapshot()
        blobs = img.find_blobs(laser_threshold)
        if blobs:
            img.draw_cross(blobs[0].cx(),blobs[0].cy(),color=(0,0,0))
            if move_pencil_point_n == 4: #最后一定点，需要和第一个点作差
                x = (pencil_points[0][0] - pencil_points[4][0]) / move_pencil_step_tot *move_pencil_step_n + pencil_points[4][0]
                y = (pencil_points[0][1] - pencil_points[4][1]) / move_pencil_step_tot *move_pencil_step_n + pencil_points[4][1]
            else:
                x = (pencil_points[move_pencil_point_n + 1][0] - pencil_points[move_pencil_point_n][0]) / move_pencil_step_tot *move_pencil_step_n +pencil_points[move_pencil_point_n][0]
                y = (pencil_points[move_pencil_point_n + 1][1] - pencil_points[move_pencil_point_n][1]) / move_pencil_step_tot *move_pencil_step_n +pencil_points[move_pencil_point_n][1]
            print('x:'+str(x)+',y:'+str(y))
            laser_move_to_traget_close_loop(x, y, blobs[0].cx(),blobs[0].cy())
            if not laser_calibration_enter_mode:
                move_pencil_step_n += 1 #每边细分的步骤加1
                if move_pencil_step_n > move_pencil_step_tot:   #每边加满
                    laser_calibration_enter_mode = True #进入录入模式
                    move_pencil_step_n = 0  #步数清零
                    move_pencil_point_n += 1    #边序号加一
                    if move_pencil_point_n > 4: #边序号满
                        move_pencil_point_n = 0 #边序号清零
                        loop = False
            if laser_calibration_enter_mode:    #录入模式
                print(blobs[0].cx() - pencil_points[move_pencil_point_n][0])
                if abs(blobs[0].cx() - pencil_points[move_pencil_point_n][0]) < 3 and abs(blobs[0].cy() - pencil_points[move_pencil_point_n][1]) < 3:
                    laser_point_stable_n += 1
                else:
                    laser_point_stable_n = 0
                if laser_point_stable_n > 50:
                    laser_on_pencil_servo_value.append([servo.degree_state(servo_rotation), servo.degree_state(servo_pitch)])
                    laser_calibration_enter_mode = False


'''
针对规则的触屏功能按键。放在各个执行光点移动的循环里。
只有两个功能，分别为按屏幕左半边和右半边。
可以简单化的改成两个按键。
功能分别为：左半边复位(光点回到原点)，右半边暂停
停止状态下
'''
def screen_function_touch_button():
    global laser_on_pencil_servo_value
    screen.get_touch()  #获取触屏触摸
    if screen.touch_exist(): #如果触摸存在
        if screen.touch_x() < 160: #按下左半边,执行光点复位
            #暂存之前舵机角度
            last_rotation_value = servo.degree_state(servo_rotation)
            last_pitch_value = servo.degree_state(servo_pitch)
            laser_move_by_degress(laser_on_pencil_servo_value[-1][0], laser_on_pencil_servo_value[-1][1])
            buzzer.frequency(500)#蜂鸣器提示，外加0.5秒延迟防误触
            sleep(0.5)
            buzzer.frequency(0)
            while True:
                screen.get_touch()  #获取触屏触摸
                if screen.touch_exist():    #触摸任意位置返回
                    #之前的角度执行回去，不进行这个操作，直接回到之前的的闭环程序，极容易超调。
                    laser_move_by_degress(last_rotation_value,last_pitch_value)
                    buzzer.frequency(500)
                    sleep(0.5)
                    buzzer.frequency(0)
                    break
        else:#右边按下
            buzzer.frequency(500)
            sleep(0.5)
            buzzer.frequency(0)
            while True:
                screen.get_touch()  #获取触屏触摸
                if screen.touch_exist():
                    buzzer.frequency(500)
                    sleep(0.5)
                    buzzer.frequency(0)
                    break

'''
运行问题2的程序
'''
def question_2():
    global laser_threshold,pencil_points

    move_pencil_step_tot = 80 #每个边细分成多少份进行移动
    move_pencil_point_n = 0  #临时存储变量，用于存储当前执行到铅笔方形的哪个角
    move_pencil_step_n = 0  #临时存储变量，用于存储在当前边的第几步。步总数参考上述变量。
    loop = True
    while loop:
        clock.tick()
        img = sensor.snapshot()

        blobs = img.find_blobs(laser_threshold)
        if blobs:
            img.draw_cross(blobs[0].cx(),blobs[0].cy(),color=(0,0,0))
            if move_pencil_point_n == 3: #最后一定点，需要和第一个点作差
                x = (pencil_points[0][0] - pencil_points[3][0]) / move_pencil_step_tot *move_pencil_step_n + pencil_points[3][0]
                y = (pencil_points[0][1] - pencil_points[3][1]) / move_pencil_step_tot *move_pencil_step_n + pencil_points[3][1]
            else:
                x = (pencil_points[move_pencil_point_n + 1][0] - pencil_points[move_pencil_point_n][0]) / move_pencil_step_tot *move_pencil_step_n +pencil_points[move_pencil_point_n][0]
                y = (pencil_points[move_pencil_point_n + 1][1] - pencil_points[move_pencil_point_n][1]) / move_pencil_step_tot *move_pencil_step_n +pencil_points[move_pencil_point_n][1]
            #print('x:'+str(x)+',y:'+str(y))
            laser_move_to_traget_close_loop(x, y, blobs[0].cx(),blobs[0].cy())
            move_pencil_step_n += 1 #每边细分的步骤加1
            if move_pencil_step_n > move_pencil_step_tot:   #每边加满
                move_pencil_step_n = 0  #步数清零
                move_pencil_point_n += 1    #边序号加一
                if move_pencil_point_n > 3: #边序号满
                    move_pencil_point_n = 0 #边序号清零
        screen_function_touch_button()
        print(clock.fps())
'''
输入舵机角度关键节点，自动生成插补进行移动
输入参数：points-舵机角度的数组,格式为[[自转轴,仰俯轴],[自转轴,仰俯轴]...]
step_tot-每个边的分解步骤数量，数量越多越慢，但越稳定
step_time-每个步骤的等待时间
'''
def servo_degress_points_to_move(points, step_tot=100, step_time=0.02):
    loop = True
    point_n = 0 #临时存储用。记录当前进行到第几个节点（多边形的顶点）
    step_n = 0  #临时存储用。记录当前在一条边的哪个位置
    last_points_num = len(points) - 1
    while loop:
        if point_n == last_points_num:#最后一个节点，要与第一个节点作差
            #下面分别求自转轴和仰俯轴，在当前步骤下的过渡值
            ro = (points[0][0] - points[last_points_num][0]) / step_tot * step_n + points[last_points_num][0]
            pi = (points[0][1] - points[last_points_num][1]) / step_tot * step_n + points[last_points_num][1]
        else:
            ro = (points[point_n+1][0] - points[point_n][0]) / step_tot * step_n + points[point_n][0]
            pi = (points[point_n+1][1] - points[point_n][1]) / step_tot * step_n + points[point_n][1]
        laser_move_by_degress(ro, pi)
        step_n += 1
        if step_n > step_tot:
            step_n = 0
            point_n += 1
            if point_n > last_points_num:
                point_n = 0
        sleep(step_time)

#cam_calibration()
#laser_calibration()

print(pencil_points)
print(laser_on_pencil_servo_value)

servo.channel_on(servo_rotation)   #打开两个舵机信号
servo.channel_on(servo_pitch)
#laser_move_by_degress(90,90)   #舵机归位，使光点出现在画面中

#question_2()   #题目2，闭环移动
#题目2，开环移动
#servo_degress_points_to_move(laser_on_pencil_servo_value[:4])

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.set_vflip(True)  #针对我的硬件，颠倒画面
sensor.set_hmirror(True)
sensor.set_brightness(-2)   #设置亮度
sensor.set_contrast(3) #对比度
#sensor.set_gainceiling(2)   #增益上限
sensor.set_auto_gain(False,gain_db=5) #增益
#sensor.set_auto_exposure(True,800)  #曝光速度
pencil_points_in_QQVGA = []
img_pencil_area = sensor.alloc_extra_fb(180,180, sensor.GRAYSCALE)
for n1 in range(4):
        pencil_points_in_QQVGA.append([round(pencil_points[n1][0]*0.5), round(pencil_points[n1][1]*0.5)])
        print(pencil_points_in_QQVGA[n1])


red_threshold = [(30, 75, 30, 90, 0, 60)]
green_threshold = [(50, 100, -65, -15, -15, 40)]
n = 0
laser_move_by_degress(70,70)
while n < 50:
    img = sensor.snapshot()
    img.rotation_corr(corners = (pencil_points_in_QQVGA[:4]))
    img.draw_image(img,0,0,x_size=120,y_size=120)
    img.draw_rectangle(120,0,40,120,color=(0,0,0),fill=True)
    img.midpoint(1, bias=0.7, threshold=True, offset=5, invert=True)
    rr = img.find_rects()
    if rr:
        for r in rr:
            taruge_rec_original = r.corners()
            img.draw_rectangle(r.rect(), color = (255, 0, 0))
            for p in r.corners():
                img.draw_circle(p[0], p[1], 5, color = (0, 255, 0))
    blobs = img.find_blobs(red_threshold)
    n += 1
    '''
    if blobs:
        for blob in blobs:
            img.draw_rectangle(blob.rect())
            img.draw_cross(blob.cx(), blob.cy())
            img.draw_string(blob.x(),blob.y(),'red')
    blobs = img.find_blobs(green_threshold)
    if blobs:
        for blob in blobs:
            img.draw_rectangle(blob.rect())
            img.draw_cross(blob.cx(), blob.cy())
            img.draw_string(blob.x(),blob.y(),'green')
    '''
    #img.laplacian(4)  #通过拉普拉斯变换，突出色彩分界线（数值越大效果越好，但越慢。所以用最小值，再提高画面亮度）
    #img.gamma_corr(gamma=1.2,contrast=30) #提高画面伽马值、对比度、亮度
'''
尝试闭环跑
'''
laser_move_by_degress(90,90)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(True)  #针对我的硬件，颠倒画面
sensor.set_hmirror(True)
sensor.set_brightness(-2)   #设置亮度
sensor.set_contrast(3) #对比度
#sensor.set_gainceiling(2)   #增益上限
sensor.set_auto_gain(False,gain_db=5) #增益
#sensor.set_auto_exposure(True,800)  #曝光速度
taruge_rec = []
x_offset = 0
y_offset = 0
for n in range(3, -1, -1):
    taruge_rec.append([round((taruge_rec_original[n][0]+x_offset)*2), round((taruge_rec_original[n][1]+y_offset)*2)])


while True:

    move_pencil_step_tot = 80 #每个边细分成多少份进行移动
    move_pencil_point_n = 0  #临时存储变量，用于存储当前执行到铅笔方形的哪个角
    move_pencil_step_n = 0  #临时存储变量，用于存储在当前边的第几步。步总数参考上述变量。
    loop = True
    while loop:
        clock.tick()
        img = sensor.snapshot()
        img.rotation_corr(corners = (pencil_points[:4]))
        img.draw_image(img,0,0,x_size=240,y_size=240)
        img.draw_rectangle(240,0,80,240,color=(0,0,0),fill=True)
        blobs = img.find_blobs(red_threshold)
        if blobs:
            img.draw_cross(blobs[0].cx(),blobs[0].cy(),color=(0,0,0))
            if move_pencil_point_n == 3: #最后一定点，需要和第一个点作差
                x = (taruge_rec[0][0] - taruge_rec[3][0]) / move_pencil_step_tot *move_pencil_step_n + taruge_rec[3][0]
                y = (taruge_rec[0][1] - taruge_rec[3][1]) / move_pencil_step_tot *move_pencil_step_n + taruge_rec[3][1]
            else:
                x = (taruge_rec[move_pencil_point_n + 1][0] - taruge_rec[move_pencil_point_n][0]) / move_pencil_step_tot *move_pencil_step_n +taruge_rec[move_pencil_point_n][0]
                y = (taruge_rec[move_pencil_point_n + 1][1] - taruge_rec[move_pencil_point_n][1]) / move_pencil_step_tot *move_pencil_step_n +taruge_rec[move_pencil_point_n][1]
            #print('x:'+str(x)+',y:'+str(y))
            laser_move_to_traget_close_loop(x, y, blobs[0].cx(),blobs[0].cy())
            move_pencil_step_n += 1 #每边细分的步骤加1
            if move_pencil_step_n > move_pencil_step_tot:   #每边加满
                move_pencil_step_n = 0  #步数清零
                move_pencil_point_n += 1    #边序号加一
                if move_pencil_point_n > 3: #边序号满
                    move_pencil_point_n = 0 #边序号清零
        screen_function_touch_button()
        print(clock.fps())


##识别180*180画幅识别方框，开环移动，效果不好
#taruge_rec = [[16, 63], [54, 93], [96, 40], [60, 9]]
taruge_rec = []
x_offset = -4
y_offset = -1
for n in range(4):
    taruge_rec.append([taruge_rec_original[n][0]+x_offset, taruge_rec_original[n][1]+y_offset])

rotation_starting = (laser_on_pencil_servo_value[0][0] + laser_on_pencil_servo_value[3][0])/2
rotation_ending = (laser_on_pencil_servo_value[1][0] + laser_on_pencil_servo_value[2][0])/2
pitch_starting = (laser_on_pencil_servo_value[0][1] + laser_on_pencil_servo_value[1][1])/2
pitch_ending = (laser_on_pencil_servo_value[2][1] + laser_on_pencil_servo_value[3][1])/2

rotation_step = (rotation_ending - rotation_starting) / 120
pitch_step = (pitch_ending - pitch_starting) / 120
print(rotation_step)
print(pitch_step)
target_rectangle_points = []
for n in range(3, -1, -1):
    target_rectangle_points.append( [rotation_step * taruge_rec[n][0] + rotation_starting, pitch_step * taruge_rec[n][1] + pitch_starting] )

print(target_rectangle_points)
servo_degress_points_to_move(target_rectangle_points)
while True:
    pass
#题目三四
while True:
    clock.tick()
    img = sensor.snapshot()
    img_pencil_area.draw_image(img,0,0,x_size=240,y_size=180)
    img_pencil_area.laplacian(4)  #通过拉普拉斯变换，突出色彩分界线（数值越大效果越好，但越慢。所以用最小值，再提高画面亮度）
    img_pencil_area.gamma_corr(gamma=1,contrast=10) #提高画面伽马值、对比度、亮度
    img_pencil_area.rotation_corr(corners = (pencil_points_in_QQVGA[:4]))
    img_pencil_area.draw_image(img_pencil_area,0,0,x_size=180,y_size=180)
    img_pencil_area.draw_rectangle(180,0,60,180,color=(0,0,0),fill=True)
    rr = img_pencil_area.find_rects()
    img.draw_image(img_pencil_area,0,0)
    if rr:
        for r in rr:
            print(r.corners())
            img.draw_rectangle(r.rect(), color = (255, 0, 0))
            for p in r.corners():
                img.draw_circle(p[0], p[1], 5, color = (0, 255, 0))
    print(clock.fps())

#保存以前的程序
x = 120
y = 120
while(True):

    clock.tick()
    img = sensor.snapshot()
    #img.rotation_corr(corners = (pencil_points[:4]))
    #img.draw_image(img,0,0,x_size=240,y_size=240)
    #img.draw_rectangle(241,0,80,240,color=(0,0,0),fill=True)

    blobs = img.find_blobs(laser_threshold)

    if blobs:
        img.draw_cross(blobs[0].cx(),blobs[0].cy(),color=(0,0,0))
        if move_pencil_point_n == 3: #最后一定点，需要和第一个点作差
            x = (pencil_points[0][0] - pencil_points[3][0]) / move_pencil_step_tot *move_pencil_step_n + pencil_points[3][0]
            y = (pencil_points[0][1] - pencil_points[3][1]) / move_pencil_step_tot *move_pencil_step_n + pencil_points[3][1]
        else:
            x = (pencil_points[move_pencil_point_n + 1][0] - pencil_points[move_pencil_point_n][0]) / move_pencil_step_tot *move_pencil_step_n +pencil_points[move_pencil_point_n][0]
            y = (pencil_points[move_pencil_point_n + 1][1] - pencil_points[move_pencil_point_n][1]) / move_pencil_step_tot *move_pencil_step_n +pencil_points[move_pencil_point_n][1]
        print('x:'+str(x)+',y:'+str(y))
        laser_move_to_traget_close_loop(x, y, blobs[0].cx(),blobs[0].cy())
        move_pencil_step_n += 1 #每边细分的步骤加1
        if move_pencil_step_n > move_pencil_step_tot:   #每边加满
            move_pencil_step_n = 0  #步数清零
            move_pencil_point_n += 1    #边序号加一
            if move_pencil_point_n > 3: #边序号满
                move_pencil_point_n = 0 #边序号清零

    #screen.display(img)

    print(clock.fps())
