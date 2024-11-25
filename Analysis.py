# Analysis.py

import csv

def initializeData():
    with open('analysis.csv', 'w') as file:
        file.write("Transfer Speed\n")

def getData(size, time):
    speed = size / time
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
    with open('analysis.csv','a') as fd:
        data = f'{round(speed,2)} {unit}\n'
        fd.write(data)
