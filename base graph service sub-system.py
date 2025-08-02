#case 1:
print("Loading ultrasonic sensor 1's data...")
xAxis = [-19,-18,-17,-16,-15,-14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0]
yAxis = pastSonarReading
if sonarReadCount < 20:
    print("The normal operation mode has not been run long enough to collect 20s of data. Displaying plot of available data...")
plt.plot(xAxis, yAxis)
plt.xlabel ("Time before epoch (s)")
plt.ylabel("Distance (cm)")
plt.title("Ultrasonic Sensor 1 Distance Graph")
plt.show()
plt.savefig("Ultrasonic Graph.jpg")
    
#case 2:
print("Loading LDR sensor 1's data...")
xAxis = [-19,-18,-17,-16,-15,-14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0]
yAxis = pastLdrReading
if ldrReadCount < 20:
    print("The normal operation mode has not been run long enough to collect 20s of data. Displaying plot of available data...")
plt.plot(xAxis, yAxis)
plt.xlabel ("Time before epoch (s)")
plt.ylabel("Lux")
plt.title("Light Intensity")
plt.show()
plt.savefig("Lux Graph.jpg")

#case 3:
print("Loading LDR sensor 1's data...")
xAxis = [-19,-18,-17,-16,-15,-14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0]
yAxis = pastTemperatureReading
if temperatureCount < 20:
    print("The normal operation mode has not been run long enough to collect 20s of data. Displaying plot of available data...")
plt.plot(xAxis, yAxis)
plt.xlabel ("Time before epoch (s)")
plt.ylabel("Temperature")
plt.title("Temperature Graph")
plt.show()
plt.savefig("Temperature Graph.jpg")

#reference: https://www.geeksforgeeks.org/ (to make the base graph)