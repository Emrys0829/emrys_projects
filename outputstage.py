# Output stage script
# This script controls output stage related functions (7 segment display, lights, stage 4 buzzer).
# Created By: Chee
# Creation date: 01/09/2024
# Ver = 1.4

# Imports
from pymata4 import pymata4
import time

# get required global variables, functions, etc
import setup

def seven_seg_and_lights():
    """
    Function which controls shift registers for traffic lights and 7 seg display. 
    lightsInputArray and stringToDisplay must both be set before calling this. The code was written this way as passing variables appears to affect performance.
    Parameters:
        - None
    Outputs:
        - None
    """

    # Get offset for scrolling based on (kinda) random modulus and scroll every second
    stringScrollOffset = int(time.time()) % 5

    # Slice string to get only 4 chars
    subStringToDisplay = stringToDisplay[stringScrollOffset:min(stringScrollOffset+4,5)]
    if stringScrollOffset != 0 and stringScrollOffset != 1:
        subStringToDisplay = subStringToDisplay + stringToDisplay[0:(stringScrollOffset-1)]

    # For correcting indexes if the string has a period
    dotOffset = 0

    # Stabilise outputs by waiting this value
    subWait = 0.0007 # <------ Experimentally derived!!

    # Display each digit 
    for i in range(len(subStringToDisplay)):
        sSegControlOut = [1,1,1,1,0,0,0,0]
        sSegControlOut[i] = 0
        if setup.curStage == 4: # Turn on buzzer if current stage is 4
            sSegControlOut[5] = 1
        # Skip seven segment related code if the string character we're on is .
        if subStringToDisplay[i] == ".":
            dotOffset += 1
            for i in lightsInputArray[::-1]:
                setup.board.digital_write(setup.lightSer,i)
                time.sleep(subWait)
                setup.board.digital_write(setup.srclk,1)
                setup.board.digital_write(setup.srclk,0)
            setup.board.digital_write(setup.rclk,1)
            setup.board.digital_write(setup.rclk,0)
            continue 
        
        # Writing our decimal place bit to shift register
        if subStringToDisplay[(i+1) % 4] == ".":
            setup.board.digital_write(setup.sevenSegSer,1)
            time.sleep(subWait)
            setup.board.digital_write(setup.sevenSegSer,1)
        else:
            setup.board.digital_write(setup.sevenSegSer,0)
            time.sleep(subWait)
            setup.board.digital_write(setup.sevenSegSer,0)
        time.sleep(subWait)
        setup.board.digital_write(setup.lightSer,lightsInputArray[7])
        time.sleep(subWait)
        setup.board.digital_write(setup.lightSer,lightsInputArray[7])
        time.sleep(subWait)
        setup.board.digital_write(setup.srclk,1)
        time.sleep(subWait)
        setup.board.digital_write(setup.srclk,1)
        time.sleep(subWait)
        setup.board.digital_write(setup.srclk,0)
        time.sleep(subWait)
        setup.board.digital_write(setup.srclk,0)
        time.sleep(subWait)
        
        # Write remaining bits to shift register. Write commands repeated to make sure they're sent. 
        for i2 in range(7)[::-1]:
            setup.board.digital_write(setup.sevenSegSer,int(setup.sevenSegLookupDict[subStringToDisplay[i]][i2]))
            time.sleep(subWait)
            setup.board.digital_write(setup.sevenSegSer,int(setup.sevenSegLookupDict[subStringToDisplay[i]][i2]))
            time.sleep(subWait)
            setup.board.digital_write(setup.lightSer,lightsInputArray[i2])
            time.sleep(subWait)
            setup.board.digital_write(setup.lightSer,lightsInputArray[i2])
            time.sleep(subWait)
            setup.board.digital_write(setup.sSegControl,sSegControlOut[i2])
            time.sleep(subWait)
            setup.board.digital_write(setup.sSegControl,sSegControlOut[i2])
            time.sleep(subWait)
            setup.board.digital_write(setup.srclk,1)
            time.sleep(subWait)
            setup.board.digital_write(setup.srclk,1)
            time.sleep(subWait)
            setup.board.digital_write(setup.srclk,0)
            time.sleep(subWait)
            setup.board.digital_write(setup.srclk,0)
            time.sleep(subWait)

        # Push to shift register outputs
        setup.board.digital_write(setup.rclk,1)
        time.sleep(subWait)
        setup.board.digital_write(setup.rclk,1)
        time.sleep(subWait)
        # Reset rclk
        setup.board.digital_write(setup.rclk,0)
        time.sleep(subWait)
        setup.board.digital_write(setup.rclk,0)
        time.sleep(subWait)

def light_control():
    """
    Function which controls shift registers only the for traffic lights. 
    lightsInputArray must be set before calling this. The code was written this way as passing variables appears to affect performance.
    Parameters:
        - None
    Outputs:
        - None
    """

    # Write bits to shift register
    for i2 in range(8)[::-1]:
        setup.board.digital_write(setup.lightSer,lightsInputArray[i2])
        setup.board.digital_write(setup.srclk,1)
        setup.board.digital_write(setup.srclk,0)

    # Push to shift register outputs
    setup.board.digital_write(setup.rclk,1)
    # Reset rclk
    setup.board.digital_write(setup.rclk,0)

    time.sleep(0.001)

def stage_tracker():
    """
    Function which manages and controls main normal operation output functions (traffic light and 7 seg) and tracks current stage. 
    Parameters:
        - None
    Outputs:
        - None
    """

    global lightsInputArray # [red main, yellow main, green main, red side, yellow side, green side, red pedestrian, green pedestrian]
    global stringToDisplay

    # Check if we need to iterate stage number
    if time.perf_counter() - setup.stageStart > setup.trafficTimings[setup.curStage-1]:
        setup.trafficTimings = setup.trafficTimingsBuffer

        setup.thermistorTimingAdded = False
        setup.LDRTimingAdded = False
        setup.trafficTimingsBuffer = setup.trafficTimingsDefault.copy()

        setup.curStage = (setup.curStage + 1)
        if setup.curStage == 7: # check if it has exceeded total stage number, don't use mod as stage count starts at 1
            setup.curStage = 1
        
        setup.stageStart = time.perf_counter()
        print("\nStage " + str(setup.curStage) + ": ")

    # Check LDR and set new timings if needed
    if setup.dayNightStatus == "night" and setup.LDRTimingAdded != True:
        setup.trafficTimingsBuffer[0] = 45
        setup.trafficTimingsBuffer[3] = 10
        setup.LDRTimingAdded = True

    # Check temperature and set new timings if needed
    if setup.pastThermReading[-1] > 35 and setup.thermistorTimingAdded != True:
        setup.trafficTimingsBuffer[0] = setup.trafficTimingsBuffer[0] + 5
        setup.trafficTimingsBuffer[3] = setup.trafficTimingsBuffer[3] + 5
        setup.thermistorTimingAdded = True

    # Stage 1 check
    if setup.curStage == 1:
        lightsInputArray = [0,0,1,1,0,0,1,0]

        seven_seg_string_set()
        pedestrian_tracker()
        seven_seg_and_lights()
    # Stage 2 check
    elif setup.curStage == 2:
        lightsInputArray = [0,1,0,1,0,0,1,0]

        seven_seg_string_set()
        pedestrian_tracker()
        seven_seg_and_lights()
    # Stage 3 check
    elif setup.curStage == 3:
        lightsInputArray = [1,0,0,1,0,0,1,0]

        seven_seg_string_set()
        pedestrian_tracker()
        seven_seg_and_lights()
    # Stage 4 check
    elif setup.curStage == 4:
        lightsInputArray = [1,0,0,0,0,1,0,1]

        seven_seg_string_set()
        setup.pedButtonCount = 0
        seven_seg_and_lights()
    # Stage 5 check
    elif setup.curStage == 5:
        setup.board.digital_write(setup.s5FlashPin,1) # Turn on flash
        lightsInputArray = [1,0,0,0,1,0,0,0]

        seven_seg_string_set()
        pedestrian_tracker()
        seven_seg_and_lights()
    # Stage 6 check
    elif setup.curStage == 6:
        setup.board.digital_write(setup.s5FlashPin,0) # Turn off flash 
        lightsInputArray = [1,0,0,1,0,0,1,0]

        seven_seg_string_set()
        pedestrian_tracker()
        seven_seg_and_lights()

def seven_seg_string_set():
    """
    Function to check current seven segment mode and thus set the proper string to be displayed.
    Parameters:
        None
    Outputs:
        None
    """

    global stringToDisplay

    # Check which mode the 7 seg is in to have it display the right string
    if setup.sevenSegMode == "custom":
        stringToDisplay = setup.customSevenSegString + " "
    elif setup.sevenSegMode == "stage":
        stringToDisplay = "stg" + str(setup.curStage) + " "
    elif setup.sevenSegMode == "opmode":
        stringToDisplay = "norm" + " "
    elif setup.sevenSegMode == "temp":
        if setup.tempStatus == "hot":
            stringToDisplay = "hot " + " "
        elif setup.tempStatus == "normal":
            stringToDisplay = "norm" + " "
        elif setup.tempStatus == "cold":
            stringToDisplay = "cold" + " "
        else:
            stringToDisplay = "none" + " "
    elif setup.sevenSegMode == "daynight":
        if setup.dayNightStatus == "day":
            stringToDisplay = "day " + " "
        else:
            stringToDisplay = "nght" + " "

def pedestrian_tracker():
    """
    Function which tracks pedestrian button presses. 
    Parameters:
        - None
    Outputs:
        - None
    """

    # Check if button is down and debounce and make sure its not being held
    if setup.board.digital_read(setup.pedButtonPin)[0] == 1 and time.perf_counter() > setup.lastPedButtonPress + 0.5 and setup.pedButtonDown == False:
        setup.lastPedButtonPress = time.perf_counter()
        setup.pedButtonCount += 1
        setup.pedButtonDown = True
        print("\nPedestrian button press count: " + str(setup.pedButtonCount) + ".") # Print to console for feature
    # Or check if its not down and debounce and previously down
    elif setup.board.digital_read(setup.pedButtonPin)[0] == 0 and time.perf_counter() > setup.lastPedButtonPress + 0.1 and setup.pedButtonDown == True:
        setup.pedButtonDown = False

def seven_seg_display():
    """
    Function which manages and controls only the 7 segment display. 
    stringToDisplay must be set before calling this. The code was written this way as passing variables appears to affect performance.
    Parameters:
        - None
    Outputs:
        - None
    """

    # Get offset for scrolling based on (kinda) random modulus and scroll every second
    stringScrollOffset = int(time.time()) % 5

    # Slice string to get only 4 chars
    subStringToDisplay = stringToDisplay[stringScrollOffset:min(stringScrollOffset+4,5)]
    if stringScrollOffset != 0 and stringScrollOffset != 1:
        subStringToDisplay = subStringToDisplay + stringToDisplay[0:(stringScrollOffset-1)]

    # For correcting indexes if the string has a period
    dotOffset = 0

    # Stabilise outputs by waiting this value
    subWait = 0.0020 # <------ Experimentally derived!!

    # Display each digit 
    for i in range(len(subStringToDisplay)):
        sSegControlOut = [1,1,1,1,1,0,0,0]
        sSegControlOut[i] = 0
        # Skip seven segment related code if the string character we're on is .
        if subStringToDisplay[i] == ".":
            dotOffset += 1
            for i in lightsInputArray[::-1]:
                setup.board.digital_write(setup.lightSer,i)
                time.sleep(subWait)
                setup.board.digital_write(setup.srclk,1)
                setup.board.digital_write(setup.srclk,0)
            setup.board.digital_write(setup.rclk,1)
            setup.board.digital_write(setup.rclk,0)
            continue 
        
        # Writing our decimal place bit to shift register
        if subStringToDisplay[(i+1) % 4] == ".":
            setup.board.digital_write(setup.sevenSegSer,1)
            setup.board.digital_write(setup.sevenSegSer,1)
        else:
            setup.board.digital_write(setup.sevenSegSer,0)
            setup.board.digital_write(setup.sevenSegSer,0)
        time.sleep(subWait)
        setup.board.digital_write(setup.srclk,1)
        setup.board.digital_write(setup.srclk,1)
        setup.board.digital_write(setup.srclk,0)
        setup.board.digital_write(setup.srclk,0)
        time.sleep(subWait)
        
        # Write remaining bits to shift register. Write commands repeated to make sure they're sent. 
        for i2 in range(7)[::-1]:
            setup.board.digital_write(setup.sevenSegSer,int(setup.sevenSegLookupDict[subStringToDisplay[i]][i2]))
            setup.board.digital_write(setup.sevenSegSer,int(setup.sevenSegLookupDict[subStringToDisplay[i]][i2]))
            time.sleep(subWait)
            setup.board.digital_write(setup.sSegControl,sSegControlOut[i2])
            setup.board.digital_write(setup.sSegControl,sSegControlOut[i2])
            time.sleep(subWait)
            setup.board.digital_write(setup.srclk,1)
            setup.board.digital_write(setup.srclk,1)
            time.sleep(subWait)
            setup.board.digital_write(setup.srclk,0)
            setup.board.digital_write(setup.srclk,0)

        time.sleep(subWait)
        # Push to shift register outputs
        setup.board.digital_write(setup.rclk,1)
        setup.board.digital_write(setup.rclk,1)
        time.sleep(subWait)
        # Reset rclk
        setup.board.digital_write(setup.rclk,0)
        setup.board.digital_write(setup.rclk,0)