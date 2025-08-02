from pymata4 import pymata4 
import time
board = pymata4.Pymata4() 

def read_ldr_value(): 
    """
    Function that sets up the LDR system and reads the light level
    """
    board.set_pin_mode_analog_input(0)
    #resistor = 2k ohm
    listOneSecData = [0]*10
    readCount = 0
    while True:
        read = board.analog_read(0)[0]
        #print(read)
        time.sleep(0.1)
        listOneSecData.append(read)
        listOneSecData.pop(0)
        readCount += 1
        if readCount >= 10:
            dataAverage = sum(listOneSecData)/ 10
            print(dataAverage)
            if dataAverage > 508: #(when it reach 2.5v)
                print("night")
            else:
                print("day")
            voltage = dataAverage*0.0048828125
            lux = ((2500/voltage)-500/2) #source: https://www.emant.com/316002.page (to calculate lux)
            print(lux)
            readCount = 0
            
            
read_ldr_value()
board.shutdown()