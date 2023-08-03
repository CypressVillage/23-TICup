'''阈值定义'''
thresholds_redpoint_base = [
(48, 75, 36, 74, -15, 25), # 白板红光，方框比较小，但是不能跟踪黑色部分👍
#(95, 100, -5, 5, -5, 5), # 全白
#(0, 100, 21, 127, -38, 127), # 白板黑胶带红光，都可以跟踪，但是方框比较大
]
thresholds_redpoint_blackline = [
(0, 100, 15, 53, -30, 40), # 3号上午黑线红点👍
]

def find_red_point():
    '''
    找到红点的坐标，返回x, y

    如果使用第一种阈值就能找到红点，就使用第一种阈值，否则使用第二种阈值的均值
    '''
    x, y, sumx, sumy = 0, 0, 0, 0
    find_point = False
    blobs = []
    blob_0, blob_1, blob_2, blob_3 = 0, 0, 0, 0
    while not find_point:
        img = sensor.snapshot()
        clock.tick() # 用于计算FPS
        # 用第一种阈值找红点
        blobs = img.find_blobs(thresholds_redpoint_base)
        if blobs and blobs[0]:
            x, y = blobs[0].cx(), blobs[0].cy()
            blob_0, blob_1, blob_2, blob_3 = blobs[0][0], blobs[0][1], blobs[0][2], blobs[0][3]
            break

        # 用第二种阈值找红点
        blobs = img.find_blobs(thresholds_redpoint_blackline)
        if blobs:
            for blob in blobs:
                sumx += blob[5]
                sumy += blob[6]
                blob_0 += blob[0]
                blob_1 += blob[1]
                blob_2 += blob[2]
                blob_3 += blob[3]
            x, y = int(sumx / len(blobs)), int(sumy / len(blobs))
            blob_0, blob_1, blob_2, blob_3 = int(blob_0 / len(blobs)), int(blob_1 / len(blobs)), int(blob_2 / len(blobs)), int(blob_3 / len(blobs))
            print('find red point: ', x, y)
            find_point = True
        # else:
        #     print("find red point: not found")
    # 画出红点的外接矩形
    img.draw_rectangle(blob_0, blob_1, blob_2, blob_3)
    img.draw_cross(x, y)
    return x, y