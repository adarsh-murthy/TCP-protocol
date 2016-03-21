import socket, sys
from struct import *
import socket
from datetime import datetime
import time
import select
from sys import argv
script, filename, listening_port, sender_ip, sender_port, log_filename = argv
listening_port = int(listening_port)
sender_port = int(sender_port)

#Check sum to check for corrupted data
def checksum(msg):
    s = 0
     
    # loop taking 2 characters at a time
    for i in range(0, len(msg), 2):
        w = ord(msg[i]) + (ord(msg[i+1]) << 8 )
        s = s + w
     
    s = (s>>16) + (s & 0xffff);
    s = s + (s >> 16);
     
    #complement and mask to 4 byte short
    s = ~s & 0xffff
     
    return s

#Creating receiver socket and binding to the listening port
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind((sender_ip, listening_port))
#Estimating the RTT and the safety margin Dev RTT
estimatedrtt = 0
samplertt = 8
alpha = 0.125
beta = 0.25
estimatedrtt = ((1-alpha) * estimatedrtt) + (alpha * samplertt)
devrtt = 0
devrtt = ((1 - beta) * devrtt) + (beta * abs(samplertt - estimatedrtt))

ack = '1'   #Intitializing the value of ack in case the very first packet is lost
flag = 1
log = ""    #This collects the data to put in the log file
chkstr = "" #This string is used to check for duplcate packet
while flag:
    print "Waiting to receive data"
    estimatedrtt = ((1-alpha) * estimatedrtt) + (alpha * samplertt)
    devrtt = ((1 - beta) * devrtt) + (beta * abs(samplertt - estimatedrtt))
    
    
    inputready, outputready,exceptrdy = select.select([sock], [],[], devrtt)    #Waits for input from socket. There's a timeout
                                                                                #which when run out, sends previous ack
    if inputready:
        data, addr = sock.recvfrom(4096) # buffer size is 1024 bytes
        
        if data == 'fin':
            print "Transmission success"
            flag = 0
            break
        header_data = data[:20]
        unpacked_data = unpack('!HHLLBBHHH' , header_data)
        if data[20:] != chkstr: #Ensures not duplicate data
            
            chk = unpacked_data[7]
            tcp_check = 0
            tcp_header = pack('!HHLLBBH' , unpacked_data[0], unpacked_data[1], unpacked_data[2], unpacked_data[3], unpacked_data[4], unpacked_data[5], unpacked_data[6]) + pack('!H' , tcp_check) + pack('!H' , unpacked_data[8])
            psh = tcp_header + data[20:]
            tcp_check1 = checksum(psh)
            #print chk, tcp_check1
            if chk == tcp_check1:   #Checking for corrupted packet
                print "Corrupt-free data"
                
                txt = open(filename, 'ab')
                txt.write(data[20:])    #Writing data to the file
                chkstr = data[20:]
                timestamp = str(datetime.now())
               
                log = log + timestamp+ ' ' +str(sender_port)+ ' ' + str(listening_port)+  ' ' +str(unpacked_data[2])+  ' ' +str(unpacked_data[2])+ '\n'

                
                ack = str(unpacked_data[2])
                sock.sendto(ack,(sender_ip,sender_port))
            else:
                sock.sendto(ack,(sender_ip,sender_port))    #transmit previous ack in case of corrupted packet
                log = log + timestamp+ ' ' +str(sender_port)+ ' ' + str(listening_port)+  ' ' +str(unpacked_data[2])+  ' ' +str(unpacked_data[2])+ '\n'
    else:
        print "Timeout"
        sock.sendto(ack,(sender_ip,sender_port))    #Transmits previous ack in case of timeout
        timestamp = str(datetime.now())
        if ack != '1':
            log = log + timestamp+ ' ' +str(sender_port)+ ' ' + str(listening_port)+  ' ' +str(unpacked_data[2])+  ' ' +str(unpacked_data[2])+ '\n'
txt.close()
txt = open(log_filename, 'wb')  #Writing logged data in the log file
txt.write(log)
txt.close()