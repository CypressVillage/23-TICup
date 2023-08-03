# Find Rects Example
#
# 这个例子展示了如何使用april标签代码中的四元检测代码在图像中找到矩形。 四元检测算法以非常稳健的方式检测矩形，并且比基于Hough变换的方法好得多。 例如，即使镜头失真导致这些矩形看起来弯曲，它仍然可以检测到矩形。 圆角矩形是没有问题的！
# (但是，这个代码也会检测小半径的圆)...

import sensor, image, time, pyb

sensor.reset()
sensor.set_pixformat(sensor.RGB565) # 灰度更快(160x120 max on OpenMV-M7)
sensor.set_framesize(sensor.QQVGA)#160 * 120
sensor.skip_frames(time = 2000)
clock = time.clock()

p1 = pyb.Pin('P1', pyb.Pin.OUT_PP)
p2 = pyb.Pin('P2', pyb.Pin.OUT_PP)
p1.high()
p2.low()

while(True):
    clock.tick()
    img = sensor.snapshot()

    # 下面的`threshold`应设置为足够高的值，以滤除在图像中检测到的具有
    # 低边缘幅度的噪声矩形。最适用与背景形成鲜明对比的矩形。

    #find_rects只有两个参数roi(x,y,w,h) + threshold
    #如果只想显示图像右下角位置，则roi=(80,60,80,60)
    for r in img.find_rects(threshold = 20000):
               #rect.rect()返回一个矩形元组(x, y, w, h)，用于如矩形的边界框的image.draw_rectangle()等其他的 image 方法。

        img.draw_rectangle(r.rect(), color = (255, 0, 0))
        #image.draw_rectangle(x, y, w, h[, color[, thickness=1[, fill=False]]])在图像上绘制一个矩形。
            # 您可以单独传递x，y，w，h或作为元组(x，y，w，h)传递。
            #color 是用于灰度或RGB565图像的RGB888元组。默认为白色。但是，您也可以传递灰度图像的基础像素值(0-255)或RGB565图像的字节反转RGB565值。
            #thickness 控制线的粗细像素。
            #将 fill 设置为True以填充矩形。

        #rect.corners()
        #返回一个由矩形对象的四个角组成的四个元组(x,y)的列表。四个角通常是按照从左上角开始沿顺时针顺序返回的。

        #嵌套循环！rect.corners()返回一个由矩形对象的四个角组成的四个元组(x,y)的列表。四个角通常是按照从左上角开始沿顺时针顺序返回的。
        for p in r.corners(): img.draw_circle(p[0], p[1], 5, color = (0, 255, 0))  #在四个角上画圆
            #image.draw_circle(x, y, radius[, color[, thickness=1[, fill=False]]])
            #在图像上绘制一个圆形。与上方draw_rects()类似

        print(r)

    print("FPS %f" % clock.fps())


#rect.x()返回矩形的左上角的x位置。您也可以通过索引 [0] (如上方r[0])取得这个值。
#rect.y()返回矩形的左上角的y位置。您也可以通过索引 [1] (如上方r[1])取得这个值。
#rect.w()返回矩形的宽度。您也可以通过索引 [2] (如上方r[2])取得这个值。
#rect.h()返回矩形的高度。您也可以通过索引 [3] (如上方r3])取得这个值。
#rect.magnitude()返回矩形的模(magnitude)。您也可以通过索引 [4] (如上方r[4])取得这个值。
