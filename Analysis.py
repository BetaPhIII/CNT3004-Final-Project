# Analysis.py

def getSpeed(size, time):
    speed = size / time
    if speed >= 10e9:
        speed = speed / 10e9
        unit = "GB/s"
    elif speed >= 10e6:
        speed = speed / 10e6
        unit = "MB/s"
    elif speed >= 10e3:
        speed = speed / 10e3
        unit = "KB/s"
    print("Data Speed: ", speed, " ", unit)