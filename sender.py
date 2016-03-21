# some imports
import sys
import socket, sys
from struct import *
from sys import argv
import os
from datetime import datetime
script, filename, remoteip, remoteport, ack_portno, log_file, window_size = argv
remoteport = int(remoteport)
ack_portno = int(ack_portno)
window_size = int(window_size)
#Obtaining IP
si = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
si.connect(('8.8.8.8', 0))  # connecting to a UDP address doesn't send packets
source_ip = si.getsockname()[0]
# checksum to include in the header
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
 #Slicing the whole data into packets
def getdata(msg, val):
    if val + 556 <= len(msg):
        return msg[val:val+556]
    else:
        return msg[val:]
#create a socket
try:
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
except socket.error , msg:
    print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()
s.bind(('', ack_portno))

#Calculating the estimated RTT
estimatedrtt = 0
samplertt = 8
alpha = 0.125

# Constructing the packet
packet = ''
 

dest_ip = remoteip 

# tcp header fields
tcp_source = ack_portno   # source port
tcp_dest = remoteport   # destination port
tcp_seq = 0
tcp_ack_seq = 0
tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
#tcp flags
tcp_fin = 0
tcp_syn = 1
tcp_rst = 0
tcp_psh = 0
tcp_ack = 0
tcp_urg = 0
tcp_window = socket.htons (1)    #   maximum allowed window size
tcp_check = 0
tcp_urg_ptr = 0
 
tcp_offset_res = (tcp_doff << 4) + 0
tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh <<3) + (tcp_ack << 4) + (tcp_urg << 5)
 
# the ! in the pack format string means network order
tcp_header = pack('!HHLLBBHHH' , tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window, tcp_check, tcp_urg_ptr)

txt = open(filename,'rb')
user_data = txt.read()
txt.close()

# pseudo header fields
val = 0
data1 = getdata(user_data,val)

source_address = socket.inet_aton( source_ip )
dest_address = socket.inet_aton(dest_ip)
placeholder = 0
protocol = socket.IPPROTO_TCP
tcp_length = len(tcp_header) + len(data1)
 

psh = tcp_header + data1;
 
tcp_check = checksum(psh)

 
# make the tcp header again and fill the correct checksum - remember checksum is NOT in network byte order
tcp_header = pack('!HHLLBBH' , tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window) + pack('!H' , tcp_check) + pack('!H' , tcp_urg_ptr)
 
# final full packet - syn packets dont have any data
packet = tcp_header + data1
flag = 1
count = 1
rcount = 0
timestamp = str(datetime.now())
stats = ""
 
estimatedrtt = ((1-alpha) * estimatedrtt) + (alpha * samplertt)

while flag:

    s.sendto(packet, (remoteip , remoteport ))    # Send data to the receiver
    print "Waiting for acknowledgement"
    ack, addr = s.recvfrom(1024)    #receiving acknowledgement
    stats = stats + timestamp+ ' ' +str(tcp_source)+ ' ' + str(tcp_dest)+  ' ' +str(tcp_seq)+  ' ' + ack+ ' '+ str(estimatedrtt)+ '\n'
    print ack, val, addr
    estimatedrtt = ((1-alpha) * estimatedrtt) + (alpha * samplertt)
    if int(ack) == val: #Checking if packet was received successfully and corruptfree
        if len(user_data)-val<556:
            
            fin = 'fin'
            s.sendto(fin, (remoteip, remoteport))
            flag = 0

        else:
            
            count = count + 1
            val = val + 556
            #tcp_seq = val
            tcp_source = ack_portno   # source port
            tcp_dest = remoteport   # destination port
            tcp_seq = val
            tcp_ack_seq = 0
            tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
            #tcp flags
            tcp_fin = 0
            tcp_syn = 1
            tcp_rst = 0
            tcp_psh = 0
            tcp_ack = 0
            tcp_urg = 0
            tcp_window = socket.htons (1)    #   maximum allowed window size
            tcp_check = 0
            tcp_urg_ptr = 0
             
            tcp_offset_res = (tcp_doff << 4) + 0
            tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh <<3) + (tcp_ack << 4) + (tcp_urg << 5)
            tcp_header = pack('!HHLLBBHHH' , tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window, tcp_check, tcp_urg_ptr)
            udata = getdata(user_data,val)
            source_address = socket.inet_aton( source_ip )
            dest_address = socket.inet_aton(dest_ip)
            placeholder = 0
            protocol = socket.IPPROTO_TCP
            tcp_length = len(tcp_header) + len(udata)
             
            psh = tcp_header + udata;
             
            tcp_check = checksum(psh)
            
            tcp_header = pack('!HHLLBBH' , tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window) + pack('!H' , tcp_check) + pack('!H' , tcp_urg_ptr)
             
            
            packet = tcp_header + udata
            
            
    else:
        s.sendto(packet, (remoteip , remoteport ))
        stats = stats + timestamp+ ' ' +str(tcp_source)+ ' ' + str(tcp_dest)+  ' ' +str(tcp_seq)+  ' ' + ack+ ' '+ str(estimatedrtt)+ '\n'
        rcount = rcount + 1
statinfo = os.stat(filename)
print "Total bytes sent", statinfo.st_size
print "segments sent", count
print "Retransmitted segments", rcount

t = open(log_file,'wb')
t.write(stats)
t.close()
        
