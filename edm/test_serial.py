import serial
import time

serialcom = serial.Serial()

serialcom.port = 'COM12'
serialcom.baudrate = 1200
serialcom.parity = 'E'
serialcom.stopbits = 1
serialcom.bytesize = 7
serialcom.timeout = 30

serialcom.open()

#serialcom.write(b"SET/41/0\r\n")
#time.sleep(0.1) 
#a = serialcom.readline()
#print(a)

#serialcom.write(b"SET/149/2\r\n")
#time.sleep(0.1) 
#a = serialcom.readline()
#print(a)

serialcom.write(b"GET/M/WI21/WI22/WI31/WI51\r\n")
time.sleep(0.1) 

a = serialcom.readline()
print('shooting....', a.decode())


#serial_io = io.TextIOWrapper(io.BufferedRWPair(self.serialcom, self.serialcom))