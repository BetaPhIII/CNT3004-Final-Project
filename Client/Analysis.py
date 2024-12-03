"""
Analysis module for system performance calculations and storage
"""
import datetime

def initializeData(socketTime):
    # Writes the server response time at the top of the txt file
    with open('analysis.txt', 'a') as file:
        file.write(f'--------------------------------------------------------\nSocket created in {round(socketTime * 10e3, 2)} ms on {datetime.datetime.now()}\n--------------------------------------------------------\n')

def getData(size, time, direction):
    # Calculates the data transfer speed
    speed = size / time
    # Converts the speed to appropriate unit
    if speed >= 10e9:
        speed = speed / 10e9
        unit = "GB/s"
    elif speed >= 10e6:
        speed = speed / 10e6
        unit = "MB/s"
    elif speed >= 10e3:
        speed = speed / 10e3
        unit = "B/s"
    else:
        unit = "B/s"
    # Appends the speed and timestamp to the txt file
    with open('analysis.txt','a') as fd:
        fd.write(f'> File {direction} at {datetime.datetime.now()}. Transfer Speed: {round(speed,2)} {unit}\n')
