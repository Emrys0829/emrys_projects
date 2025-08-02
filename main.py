# Main script for ENG1013 Project
# Created by Emrys Pham, Isyaya Zahir, Ruby Simpfendorfer, Pranjal Menariya
# Creation date: 30/08/2024
# Version: 1.5

# Module import
import time
import matplotlib.pyplot as plt
from pymata4 import pymata4
import numpy as np
import math

# Custom file import
import setup
import outputstage

# Init our required variable, functions, etc
setup.initialise()

def main_menu():
    """
    Serves as the main menu for our program. Allows selection and manages execution of sub-menus and modes (normal, data, maintenance). 
    Parameter: None
    Return: None
    """

    validMainMenuInputs = [0,1,2,3]

    while True:
        try:
            print("========================")
            print("MAIN MENU")
            print("1. Normal operating mode")
            print("2. Data observation mode")
            print("3. Maintenance mode")
            print("0. Exit")
            print("========================")

            # Re-enable polling for thermistor pin
            setup.board.enable_analog_reporting(setup.thermPin)

            setup.shift_reg_reset() # Clear shift register outputs and stop the buzzer.

            try:
                userChoice = int(input("Enter mode of operation: "))
                if userChoice not in validMainMenuInputs:
                    print("Invalid input. Please try again.")
                    time.sleep(1)
                    continue
                    
            except ValueError:
                print("Invalid input. Please try again.")
                time.sleep(1)
                continue

            if userChoice == 1:
                if setup.board.digital_read(setup.maintLockoutPin)[0] == 0:
                    normal_operating_mode()
                else:
                    print("Normal operation is unavailable as the maintenance switch is closed. Returning to the main menu.")
                    time.sleep(1)
                    continue
            
            elif userChoice == 2:
                data_observation_mode()
                
            elif userChoice == 3:
                maintenance_mode_entry()
                if setup.maintenancePass == True:
                    setup.maintenancePass = False
                    maintenance_mode()
                
            elif userChoice == 0:
                # Turn everything off
                sSegControlOut = [1,1,1,1,0,0,0,0]
                for i in range(8)[::-1]:
                    setup.board.digital_write(setup.sevenSegSer,0)
                    setup.board.digital_write(setup.lightSer,0)
                    setup.board.digital_write(setup.sSegControl,sSegControlOut[i])
                    setup.board.digital_write(setup.srclk,1)
                    setup.board.digital_write(setup.srclk,0)
                setup.board.digital_write(setup.rclk,1)
                setup.board.digital_write(setup.rclk,0)
                setup.board.digital_write(setup.s5FlashPin,0)

                setup.board.shutdown()
                quit()

        #System: go back to main menu if user press CTRL C
        except KeyboardInterrupt:
            print("\nGoing back to main menu...")
            setup.shift_reg_reset()
            continue

def normal_operating_mode():
    """
    Entry point into the normal operating mode. Handles initial check of the maintenance switch and then starts the normal operation loop.
    Parameters: None
    Returns: None
    """

    # Init loopStart variable to entry into normal op 
    setup.loopStart = time.perf_counter()
    lastSonarCheck = -1
    sonarCheckFlipFlop = 1
    sonarBuffer1 = []
    sonarBuffer2 = []
    thermBuffer = []
    LDRBuffer = []
    lastLoopTime = 0
    setup.stageStart = time.perf_counter()
    setup.curStage = 1
    setup.thermistorTimingAdded = False
    setup.LDRTimingAdded = False
    setup.trafficTimingsBuffer = setup.trafficTimingsDefault.copy()

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

    print("\nStage 1: ")

    while True:
        if time.perf_counter() > lastLoopTime + setup.normOpLoopTime:
            # Check maintenance switch
            if setup.board.digital_read(setup.maintLockoutPin)[0] == 1:
                print("\nMaintenance lockout switch activated. Returning to main menu...")
                time.sleep(1)
                break

            # Loop time display, print in place so we don't spam the console
            print("Last loop took " + str(round(time.perf_counter()-lastLoopTime,2)) + "s.\r    ",end="")

            # Iterate loop time to track from this loop
            lastLoopTime = time.perf_counter()

            # Do stage tracking functions
            outputstage.stage_tracker()
            
            # Poll and check sonar readings for broken down/speeding vehicles
            if time.process_time() > lastSonarCheck + 0.25:
                sonarCheckFlipFlop = (sonarCheckFlipFlop + 1) % 2 # Run true read every 2 cycles
                lastSonarCheck = time.process_time()
                sonarBuffer1.append(setup.board.sonar_read(setup.sonar1Trig)[0])
                time.sleep(0.0001)
                sonarBuffer2.append(setup.board.sonar_read(setup.sonar2Trig)[0])
                time.sleep(0.0001)
                thermBuffer.append(setup.thermistor_read())
                time.sleep(0.0001)
                LDRBuffer.append(setup.LDR_read())

                if sonarCheckFlipFlop == 1:
                    setup.pastSonarReading.append(np.mean(sonarBuffer1)) # append latest mean reading (filtered)
                    setup.pastSonarReading.pop(0) # and remove the oldest one
                    setup.sonarReadCount += 1
                    sonarBuffer1 = [] # reset buffer

                    setup.pastSonarReading2.append(np.mean(sonarBuffer2)) # append latest mean reading (filtered)
                    setup.pastSonarReading2.pop(0) # and remove the oldest one
                    setup.sonarReadCount2 += 1
                    sonarBuffer2 = [] # reset buffer

                    setup.pastThermReading.append(np.mean(thermBuffer)) # append latest mean reading (filtered)
                    setup.pastThermReading.pop(0) # and remove the oldest one
                    setup.thermReadCount += 1
                    thermBuffer = [] # reset buffer

                    setup.pastLDRReading.append(np.mean(LDRBuffer)) # append latest mean reading (filtered)
                    setup.pastLDRReading.pop(0) # and remove the oldest one
                    setup.LDRReadCount += 1
                    LDRBuffer = [] # reset buffer
                    if setup.pastLDRReading[-1] < 2.5:
                        setup.dayNightStatus = "day"
                    else:
                        setup.dayNightStatus = "night"

                    # Check if we should print the closest vehicle distance
                    if time.process_time() > setup.lastCloseDistPrint + 5:
                        print("\nCurrent closest vehicle at " + '{:.2f}'.format(setup.pastSonarReading[-1]) + "cm. ")
                        setup.lastCloseDistPrint = time.process_time()

                    # Check for fast vehicles (10 cm/s)
                    if (setup.pastSonarReading[-1]-setup.pastSonarReading[-2])/0.5 > 10 and setup.sonarReadCount > 5:
                        print("\nWarning: Speeding vehicle detected.")
                    # Make sure theres enough data to make a judgement...
                    if setup.sonarReadCount > 10:
                        # and check if a vehicle has broken down.
                        if (np.std(setup.pastSonarReading[-6:]) < 1) and setup.curStage == 1 and np.mean(setup.pastSonarReading[-3:]) < 50: # specific case for feature
                            print("\nWarning: Broken down vehicle detected during main road green.")
                        elif (np.std(setup.pastSonarReading[-6:]) < 1) and setup.curStage != 1 and np.mean(setup.pastSonarReading[-3:]) < 50: # general case 
                            print("\nWarning: Broken down vehicle detected.")

        time.sleep(0.0001)
        

def maintenance_mode_entry():
    """
    Entry point for maintenance mode menu. Manages PIN authentication and any lockout periods. 
    Parameter: None
    Returns: None
    """
    
    # Reset one time maintenance entry pass
    setup.maintenancePass = False

    # Check if any outstanding lockout time still needs to be served, if not, set lockout to false. 
    if time.perf_counter() > setup.PINLockoutTime + 120:
        setup.PINLockout = False

    # Check if the user is currently locked out
    if setup.PINLockout == True:
        print("You are currently locked out of maintenance mode.")
        time.sleep(1)
        return 

    # PIN authentication loop. Exitable with keyboard interrupt.
    while True:
        userPINInput = input("Enter the PIN: ")

        # Check if PIN is correct
        if userPINInput == setup.maintPIN:
            setup.wrongPINCount = 0
            setup.maintenancePass = True
            setup.adminPassTime = time.perf_counter()
            return 
        else: # If it isn't iterate wrong pin counter and inform user.
            setup.wrongPINCount += 1
            print("Incorrect PIN. " + str(3-setup.wrongPINCount) + " tries remaining.")
            time.sleep(1)

        # Also check in the same loop if the counter has reached 3 and lockout the user if it has.
        if setup.wrongPINCount >= 3:
            setup.PINLockout = True
            setup.PINLockoutTime = time.perf_counter()
            setup.wrongPINCount = 0
            print("You have been locked out for 3 successive incorrect PIN entries.")
            print("Returning to the main menu...")
            time.sleep(1)
            return 
    
def maintenance_mode():
    """
    The true maintenance menu which allows entry into parameter viewing and editing modes.
    Parameters: None
    Returns: None
    """
    
    # Allow only these inputs here
    validMaintModeInputs = [0,1,2]

    # Main maintenance mode menu loop
    while True:
        print("========================")
        print("MAINTENANCE MODE")
        print("1. Paramteter view")
        print("2. Paramteter edit")
        print("0. Exit")
        print("========================")

        # Get and validate initial mode pick
        try:
            userMaintModeInput = int(input("Select operation to perform: "))

            # Maint mode timeout check
            if time.perf_counter() - setup.adminPassTime > setup.adminTimeoutTime:
                print("User has been inactive for too long. Returning to main menu.")
                time.sleep(1)
                return
            setup.adminPassTime = time.perf_counter()

            if userMaintModeInput not in validMaintModeInputs:
                print("Invalid input. Please try again.")
                time.sleep(1)
                continue
        except ValueError:
            # Maint mode timeout check
            if time.perf_counter() - setup.adminPassTime > setup.adminTimeoutTime:
                return
            setup.adminPassTime = time.perf_counter()

            print("Invalid input. Please try again.")
            time.sleep(1)
            continue

        # Check which mode was picked and act accordingly
        match userMaintModeInput:
            case 0:
                print("Exiting to main menu.")
                time.sleep(1)
                return
            case 1:
                print("Entering parameter view mode.")
                time.sleep(1)
                maintenance_mode_view()
            case 2:
                print("Entering parameter edit mode.")
                time.sleep(1)
                maintenance_mode_edit()

def maintenance_mode_view():
    """
    Function allows viewing of certain operational parameters.
    Parameters: None
    Returns: None
    """

    # Allow only these inputs here.
    validMaintModeViewInputs = [0,1,2]

    # Maintenance viewing mode loop
    while True:
        print("========================")
        print("MAINTENANCE MODE PARAMETER VIEW")
        print("Available parameters to view:")
        print("1. PIN")
        print("2. 7 Segment Display Mode")
        print("0. Exit")
        print("========================")

        # Get and validate input
        try:
            userMaintModeViewInput = int(input("Enter parameter to view: "))

            # Maint mode timeout check
            if time.perf_counter() - setup.adminPassTime > setup.adminTimeoutTime:
                return
            setup.adminPassTime = time.perf_counter()
            
            if userMaintModeViewInput not in validMaintModeViewInputs:
                print("Invalid input. Please try again.")
                time.sleep(1)
                continue
        except ValueError:
            # Maint mode timeout check
            if time.perf_counter() - setup.adminPassTime > setup.adminTimeoutTime:
                return
            setup.adminPassTime = time.perf_counter()

            print("Invalid input. Please try again.")
            time.sleep(1)
            continue

        # Check what was input and act accordingly
        match userMaintModeViewInput:
            case 0:
                print("Exiting to main menu.")
                time.sleep(1)
                return
            case 1:
                print("PIN is currently set to " + setup.maintPIN + ".")
                time.sleep(1)
                continue
            case 2:
                print("The seven segment display is currently in '" + setup.sevenSegMode + "'.")
                time.sleep(1)
                continue

def maintenance_mode_edit():
    """
    Facilitates the editing of certain operational parameters.
    Parameters: None
    Returns: None
    """

    validMaintModeEditInputs = [0,1,2] # Only accept these parameter selections
    validSevenSegModes = ["stage","custom","opmode","temp","daynight"] # Only accept these seven segment modes

    # Main maintenance edit loop
    while True:
        print("========================")
        print("MAINTENANCE MODE PARAMETER EDIT")
        print("Available parameters to edit:")
        print("1. PIN")
        print("2. 7 Segment Display Mode")
        print("0. Exit")
        print("========================")
    
        # Get and validate input
        try:
            userMaintModeEditInput = int(input("Enter parameter to edit: "))

            # Maint mode timeout check
            if time.perf_counter() - setup.adminPassTime > setup.adminTimeoutTime:
                return
            setup.adminPassTime = time.perf_counter()

            if userMaintModeEditInput not in validMaintModeEditInputs:
                print("Invalid input. Please try again.")
                time.sleep(1)
                continue
        except ValueError:
            print("Invalid input. Please try again.")
            time.sleep(1)
            continue

        # Check what was input and act accordingly
        match userMaintModeEditInput:
            case 0:
                print("Exiting to main menu.")
                time.sleep(1)
                return
            case 1:
                while True:
                    try:
                        newPIN = int(input("Enter a new PIN: ")) # Make sure the PIN is numeric

                        # Maint mode timeout check
                        if time.perf_counter() - setup.adminPassTime > setup.adminTimeoutTime:
                            return
                        setup.adminPassTime = time.perf_counter()
                    except ValueError:
                        # Maint mode timeout check
                        if time.perf_counter() - setup.adminPassTime > setup.adminTimeoutTime:
                            return
                        setup.adminPassTime = time.perf_counter()

                        print("Invalid PIN. Please enter a valid PIN.")
                        continue
                    break
                # Push to global pin variable
                setup.maintPIN = str(newPIN)
                print("New PIN has been set.")
                time.sleep(1)
                continue
            case 2:
                while True:
                    # Ask for the desired 7 seg mode
                    newSevenSegMode = input("Enter a new seven segment display mode (stage, custom, opmode, temp, daynight): ")

                    # Maint mode timeout check
                    if time.perf_counter() - setup.adminPassTime > setup.adminTimeoutTime:
                        return
                    setup.adminPassTime = time.perf_counter()

                    # Validate input
                    if newSevenSegMode not in validSevenSegModes:
                        print("Invalid input.")
                        time.sleep(1)
                        continue
                    # If custom was selected, ask for the custom message
                    elif newSevenSegMode == "custom":
                        while True:
                            customSevenSegStringInput = input("Enter the custom message to be displayed on the 7 segment display (max 4 char.): ")

                            # Maint mode timeout check
                            if time.perf_counter() - setup.adminPassTime > setup.adminTimeoutTime:
                                return
                            setup.adminPassTime = time.perf_counter()

                            # Length check. Right now, we only support 4 char long
                            if len(customSevenSegStringInput) > 4 or len(customSevenSegStringInput) < 0:
                                print("Invalid input. Please try again.")
                                time.sleep(1)
                                continue
                            # Change to lowercase since thats what our 7 seg dictionary supports
                            setup.customSevenSegString = customSevenSegStringInput.ljust(4).lower() # from https://docs.python.org/3/library/stdtypes.html#str.ljust , we want to only pass in 4 character strings
                            print("Custom message '" + setup.customSevenSegString + "' set.")
                            break
                    # Push mode to the global variable for 7 seg mode
                    setup.sevenSegMode = newSevenSegMode
                    break
                time.sleep(1)
                continue

def data_observation_mode():
    """
    The true maintenance menu which allows entry into parameter viewing and editing modes.
    Parameters: None
    Returns: None
    """
    
    # Allow only these inputs here
    validObsModeInputs = [0,1,2,3,4,5,6,7]

    # Main observation mode menu loop
    while True:
        print("========================")
        print("DATA OBSERVATION MODE")
        print("1. Ultrasonic sensor 1 graph")
        print("2. Temperature reading")
        print("3. 7 Segment Display")
        print("4. Ultrasonic sensor 2 graph")
        print("5. LDR reading")
        print("6. Temperature graph")
        print("7. LDR graph")
        print("0. Exit")
        print("========================")

        # Make sure these are enabled after turning them off
        setup.board.enable_analog_reporting(setup.pedButtonPin)
        setup.board.enable_analog_reporting(setup.thermPin)

        setup.shift_reg_reset() # Clear shift register outputs and stop the buzzer.

        # Get and validate initial mode pick
        try:
            userObsModeInput = int(input("Enter data number to view: "))
            if userObsModeInput not in validObsModeInputs:
                print("Invalid input. Please try again.")
                time.sleep(1)
                continue
        except ValueError:
            print("Invalid input. Please try again.")
            time.sleep(1)
            continue

        # Check which mode was picked and act accordingly
        match userObsModeInput:
            case 0:
                print("Exiting to main menu.")
                time.sleep(1)
                return
            case 1:
                # source: https://sparkbyexamples.com/python/python-get-the-last-n-elements-of-a-list/#google_vignette (to get the last few element)
                # sources: https://www.tutorialspoint.com/how-to-plot-a-graph-in-python (to make a graph)
                print("Loading ultrasonic sensor 1's data...")
                xAxis = np.linspace(-20,0,40).tolist() # set our x axis for plotting
                yAxis = setup.pastSonarReading # grab our distance values
                if setup.sonarReadCount < 40: # check we have enough real data
                    print("The normal operation mode has not been run long enough to collect 20s of data. Displaying plot of available data...")
                plt.plot(xAxis, yAxis)
                plt.xlabel ("Time before epoch (s)")
                plt.ylabel("Distance (cm)")
                plt.legend("Ultrasonic sensor 1")
                plt.title("Ultrasonic Sensor 1 Distance Graph")
                plt.savefig("Ultrasonic_Sensor_1_Graph_" + time.strftime("%H_%M_%S", time.gmtime())) # save graph on close of plot
                plt.show()
            case 2:
                try:
                    while True:
                        curTherm = (setup.thermistor_read() + setup.lastThermistor)/2.0 # get mean (filtered) thermistor reading
                        setup.lastThermistor = curTherm * 2.0 - setup.lastThermistor
                        if curTherm >= 35:
                            setup.tempStatus = "hot"
                        elif curTherm > 20 and curTherm < 25:
                            setup.tempStatus = "normal"
                        elif curTherm <= 20:
                            setup.tempStatus = "cold"
                        else:
                            setup.tempStatus = "none" 
                        print("Current temperature is " + str(int(round(curTherm,0))) + " degrees celsius (" + setup.tempStatus + ").               \r",end="")
                        time.sleep(0.1) # Doesn't need to be that fast.
                except KeyboardInterrupt:
                    print("\n Returning to data observation menu...")
                    time.sleep(1)
            case 3:
                try:
                    # Extract as much performance as we can
                    setup.board.disable_analog_reporting(setup.thermPin)
                    setup.board.disable_analog_reporting(setup.LDRPin)

                    outputstage.seven_seg_string_set()
                    if setup.sevenSegMode == "opmode":
                        outputstage.stringToDisplay = "data" + " "

                    # Main 7 seg loop
                    while True:
                        outputstage.seven_seg_display()
                        time.sleep(0.0001)

                except KeyboardInterrupt:
                    print("\n Returning to data observation menu...")
                    # Make sure they're enabled
                    setup.board.enable_analog_reporting(setup.thermPin)
                    setup.board.enable_analog_reporting(setup.LDRPin)
                    setup.shift_reg_reset()
                    time.sleep(1)
            case 4:
                # source: https://sparkbyexamples.com/python/python-get-the-last-n-elements-of-a-list/#google_vignette (to get the last few element)
                # sources: https://www.tutorialspoint.com/how-to-plot-a-graph-in-python (to make a graph)
                print("Loading ultrasonic sensor 2's data...")
                xAxis = np.linspace(-20,0,40).tolist() # set our x axis for plotting
                yAxis = setup.pastSonarReading2 # grab our distance values
                if setup.sonarReadCount2 < 40: # check we have enough real data
                    print("The normal operation mode has not been run long enough to collect 20s of data. Displaying plot of available data...")
                plt.plot(xAxis, yAxis)
                plt.xlabel ("Time before epoch (s)")
                plt.ylabel("Height (cm)")
                plt.legend("Ultrasonic sensor 2")
                plt.title("Ultrasonic Sensor 2 Height Graph")
                plt.savefig("Ultrasonic_Sensor_2_Graph_" + time.strftime("%H_%M_%S", time.gmtime())) # save graph on close of plot
                plt.show()
            case 5:
                try:
                    while True:
                        curLDR = (setup.LDR_read() + setup.lastLDR)/2.0 # get mean (filtered) thermistor reading
                        setup.lastLDR = curLDR * 2.0 - setup.lastLDR
                        if curLDR < 2.5:
                            setup.dayNightStatus = "day"
                        else:
                            setup.dayNightStatus = "night"
                        print("It is currently " + setup.dayNightStatus + ".               \r",end="")
                        time.sleep(0.1) # Doesn't need to be that fast.
                except KeyboardInterrupt:
                    print("\n Returning to data observation menu...")
                    time.sleep(1)
            case 6:
                # source: https://sparkbyexamples.com/python/python-get-the-last-n-elements-of-a-list/#google_vignette (to get the last few element)
                # sources: https://www.tutorialspoint.com/how-to-plot-a-graph-in-python (to make a graph)
                print("Loading thermistor's data...")
                xAxis = np.linspace(-20,0,40).tolist() # set our x axis for plotting
                yAxis = setup.pastThermReading # grab our temp values
                if setup.thermReadCount < 40: # check we have enough real data
                    print("The normal operation mode has not been run long enough to collect 20s of data. Displaying plot of available data...")
                plt.plot(xAxis, yAxis)
                plt.xlabel ("Time before epoch (s)")
                plt.ylabel("Temperature (degrees Celsius)")
                plt.legend("Thermistor")
                plt.title("Thermistor temperature graph")
                plt.savefig("Thermistor_Temperature_Graph_" + time.strftime("%H_%M_%S", time.gmtime())) # save graph on close of plot
                plt.show()
            case 7:
                # source: https://sparkbyexamples.com/python/python-get-the-last-n-elements-of-a-list/#google_vignette (to get the last few element)
                # sources: https://www.tutorialspoint.com/how-to-plot-a-graph-in-python (to make a graph)
                print("Loading LDR's data...")
                xAxis = np.linspace(-20,0,40).tolist() # set our x axis for plotting
                yAxis = setup.pastLDRReading # grab our voltage values
                if setup.LDRReadCount < 40: # check we have enough real data
                    print("The normal operation mode has not been run long enough to collect 20s of data. Displaying plot of available data...")
                plt.plot(xAxis, yAxis)
                plt.xlabel ("Time before epoch (s)")
                plt.ylabel("Voltage (V)")
                plt.legend("LDR")
                plt.title("LDR graph of voltage at junction")
                plt.savefig("LDR_Voltage_Graph_" + time.strftime("%H_%M_%S", time.gmtime())) # save graph on close of plot
                plt.show()

# Main program starts from here
main_menu()