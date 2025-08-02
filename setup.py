# Init functions for ENG1013 Project
# Created by Emrys Pham, Isyaya Zahir, Ruby Simpfendorfer, Pranjal Menariya, Chee Yong
# Creation date: 06/09/2024
# Version: 1.3

# Imports
from pymata4 import pymata4
import time
import math

# Board init at 500k baud
board = pymata4.Pymata4(baud_rate=500000)

def initialise():
    """
    Primary initialisation function of the whole project. Inits and stores global variables to be accessed by different functions across different files.
    Parameters:
        None
    Returns:
        None
    """
    global maintenancePass
    global wrongPINCount
    global PINLockout
    global PINLockoutTime
    global maintLockoutPin
    global maintPIN
    global sevenSegMode
    global customSevenSegString
    global board
    global normOpLoopTime
    global adminTimeoutTime
    global adminPassTime

    # Globals functions may need to use/edit
    maintenancePass = False # Needs to be True for maintenance mode to be enterable
    wrongPINCount = 0
    PINLockout = False # This is for the maintenance entry PIN code, not the Arduino pin.
    PINLockoutTime = -1 # Set to the current time when user gets locked out for failing to enter the correct pin
    maintLockoutPin = 3 # This is the Arduino pin for maintenance lockout
    normOpLoopTime = 0.1 # Minimum loop time
    adminTimeoutTime = 30 # Time in seconds before admin perms are removed for inactivity
    adminPassTime = 0 # Init time at which admin was gained/last time activity was performed as admin

    # Editable parameters
    maintPIN = "1234"
    sevenSegMode = "stage" # Out of [stage, custom]
    customSevenSegString = "abcd" # This is a placeholder for before the user chooses to switch the 7 seg mode. 

    # Init maintenance lockout pin
    board.set_pin_mode_digital_input(maintLockoutPin)


    # Outputstage init
    # Globals
    global sevenSegSer
    global rclk
    global srclk
    global sSegControl
    global lightSer
    global stringToDisplay
    global loopStart
    global sevenSegLookupDict
    global s5FlashPin
    global pedButtonCount
    global pedButtonPin
    global lastPedButtonPress
    global sonar1Trig
    global sonar1Echo
    global sonar2Trig
    global thermPin
    global steinHartA
    global steinHartB
    global steinHartC
    global pastSonarReading
    global sonarReadCount
    global pastSonarReading2
    global sonarReadCount2
    global pedButtonDown
    global lastS5Flash
    global s5FlashState
    global trafficTimings
    global stageStart
    global curStage
    global trafficTimingsDefault
    global trafficTimingsBuffer
    global thermistorTimingAdded
    global LDRTimingAdded
    global dayNightStatus
    global lastThermistor
    global lastLDR
    global LDRPin
    global tempStatus
    global lastCloseDistPrint
    global pastThermReading
    global pastLDRReading
    global thermReadCount
    global LDRReadCount

    # Digital pins
    sevenSegSer = 9
    rclk = 8
    srclk = 7
    sSegControl = 10 
    lightSer = 6
    s5FlashPin = 2
    pedButtonPin = 11
    sonar1Trig = 5
    sonar1Echo = 4
    thermPin = 1
    LDRPin = 0
    sonar2Trig = 13
    sonar2Echo = 12

    # Config digital outputs 
    board.set_pin_mode_digital_output(sevenSegSer)
    board.set_pin_mode_digital_output(rclk)
    board.set_pin_mode_digital_output(srclk)
    board.set_pin_mode_digital_output(sSegControl)
    board.set_pin_mode_digital_output(lightSer)
    board.set_pin_mode_digital_output(s5FlashPin)
    board.set_pin_mode_digital_input(pedButtonPin)
    board.set_pin_mode_analog_input(thermPin)
    board.set_pin_mode_sonar(sonar1Trig,sonar1Echo,timeout=80000)
    board.set_pin_mode_sonar(sonar2Trig,sonar2Echo,timeout=80000)
    board.set_pin_mode_analog_input(LDRPin)

    # Init value for string to display on 7 seg
    stringToDisplay = "     "

    # Initialise shift register, buzzer, and mosfet inputs
    board.digital_write(sSegControl,0)
    board.digital_write(srclk,0)
    board.digital_write(rclk,0)
    board.digital_write(s5FlashPin,0)

    # Get start time of program for calculating current stage
    loopStart = time.perf_counter()

    # Pedestrian button variables
    pedButtonCount = 0
    lastPedButtonPress = -1
    pedButtonDown = False

    # Dictionary for getting bits for seven segment display
    sevenSegLookupDict = {
        "0": "1111110",
        "1": "0110000",
        "2": "1101101",
        "3": "1111001",
        "4": "0110011",
        "5": "1011011",
        "6": "1011111",
        "7": "1110000",
        "8": "1111111",
        "9": "1111011",
        "a": "1110111",
        "b": "0011111",
        "c": "1001110",
        "d": "0111101",
        "e": "1001111",
        "f": "1000111",
        "g": "1011110",
        "h": "0110111",
        "i": "0000110",
        "j": "0111000",
        "k": "1010111",
        "l": "0001110",
        "m": "1010101",
        "n": "1110110",
        "o": "0011101",
        "p": "1100111",
        "q": "1110011",
        "r": "0000101",
        "s": "1011011",
        "t": "0001111",
        "u": "0011100",
        "v": "0111010",
        "w": "1011100",
        "y": "0111011",
        "z": "1101101",
        " ": "0000000",
        "-": "0000001",
        "'": "0000010",
        "_": "0001000"
    }

    steinHartA = float(1.009249522e-03) #constant for Steinhart-Hart 
    steinHartB = float(2.378405444e-04) #constant for Steinhart-Hart
    steinHartC = float(2.019202697e-07) #constant for Steinhart-Hart

    pastSonarReading = [0] * 40 # init sonar reading list for dist sensor
    sonarReadCount = 0 # init sonar read count for dist sensor
    pastSonarReading2 = [0] * 40 # init sonar reading list for height sensor
    sonarReadCount2 = 0 # init sonar read count for height sensor
    pastThermReading = [0] * 40 # init sonar reading list for thermistor
    thermReadCount = 0 # init sonar read count for thermistor
    pastLDRReading = [0] * 40 # init sonar reading list for LDR
    LDRReadCount = 0 # init sonar read count for LDR

    lastS5Flash = 0 # init stage 5 led flash time keeping variable
    s5FlashState = 0 # init stage 5 led state

    trafficTimingsDefault = [15,5,3,15,5,3] # Default traffic timings to copy from
    trafficTimings = [15,5,3,15,5,3] # Init to default traffic timings in seconds
    trafficTimingsBuffer = [15,5,3,15,5,3] # Init buffer for storing uncommitted changes to main timing array

    stageStart = 0 # Init time the current stage started
    curStage = 1 # Init current stage

    thermistorTimingAdded = False # Init flag for whether timings were edited due to thermistor temp
    lastThermistor = 20 # Previous loop's thermistor reading
    LDRTimingAdded = False # Init flag for whether timings were edited due to LDR readings
    lastLDR = 0 # Previous loop's LDR reading

    dayNightStatus = "day" # Whether it is day or night right now

    tempStatus = "normal" # Init temperature status
    
    lastCloseDistPrint = 0 # Last time closest distance from approach ultrasonic was printed

    shift_reg_reset()

def shift_reg_reset():
    """
    Short function to turn off all shift register outputs and turn off the buzzer. Useful when changing modes.
    Parameters:
        None
    Returns:
        None
    """
    # Set shift register outputs off
    sSegControlOutput = [1,1,1,1,1,0,0,0]
    for i in range(8)[::-1]:
        board.digital_write(sevenSegSer,0)
        board.digital_write(lightSer,0)
        board.digital_write(sSegControl,sSegControlOutput[i])
        board.digital_write(srclk,1)
        board.digital_write(srclk,0)
    board.digital_write(rclk,1)
    board.digital_write(rclk,0)

    # Also reset light flash
    board.digital_write(s5FlashPin,0)

def thermistor_read():
    """
    Function to get the current thermistor temperature reading. 
    Parameters:
        None
    Returns:
        curTemp (current temperature, in celsius)
    """
    thermVoltage = board.analog_read(thermPin)[0]*(5.0/1023.0) # Get voltage at divider junction
    thermResistor2 = (100000*thermVoltage)/(5-thermVoltage) # Then get the resistance of the thermistor
    curTemp = (1/(steinHartA + steinHartB*math.log(thermResistor2) + steinHartC*(math.log(thermResistor2)**3)))-273.15 # From https://en.wikipedia.org/wiki/Steinhart%E2%80%93Hart_equation
    return curTemp

def LDR_read():
    """
    Function to get the current LDR resistance.
    Parameters:
        None
    Returns:
        LDRVoltage (Voltage at voltage divider junction, in V)
    """
    LDRVoltage = board.analog_read(LDRPin)[0]*(5.0/1023.0) # Get voltage at divider junction
    return LDRVoltage