from pymata4 import pymata4
import time

board = pymata4.Pymata4()

def sonar_reading():
    """
    Function that sets up the sonar tester and reads the hight values
    """
    triggerPin = 7
    echoPin = 6
   
    board.set_pin_mode_sonar(triggerPin, echoPin, timeout=400000)
    try:
        while True:
            data = board.sonar_read(triggerPin)
            distance = data[0]  # this is the distance data only 
            print(distance) # this prints the distance data from the Sonar sensor on the wood 
            

    except KeyboardInterrupt:
        print("finished ")
