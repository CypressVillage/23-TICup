thresholds_redpoint = [
#(95, 100, -5, 5, -5, 5),
#(0, 100, 21, 127, -38, 127),
(48, 75, 36, 74, -15, 25)
]

def find_red_point():
    '''找到红点的坐标，返回x, y'''
    x, y, sumx, sumy = 0, 0, 0, 0
    find_point = False
    blobs = []
    while not find_point:
        img = sensor.snapshot()
        blobs = img.find_blobs(thresholds_redpoint)
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