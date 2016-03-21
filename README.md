# TCP-protocol
1. The link emulator must be invoked first. (Not provided here. Any sniffer can be used)
2. The Receiver must be invoked first in the following form:
			<filename> <listening port> <sender IP> <sender port> <logfilename>

3. The receiver waits for the sender to start sending. 

4. The sender must be invoked as:
			<filename>  <remote IP> <remote port> <ack_port_num> <log filename> <window size> 

5. Here, remote IP and remote port must be of the link emulator.

6. ack_port_num must be the port to which the sender binds

7. When the receiver detects corrupted data, it transmits the previous ack to indicate to the sender that the packet is corrupted.

8. The timer is placed on the receiver end since the packets could be lost only on the way to the receiver (since the acks are sent over tcp). If the receiver doesn't receive until timeout value, it transmits the previous ack to indicate the sender to retransmit. Similarly, it handles packet delay.

9. The receiver temporarily stores the packet and checks if the new packet is the same as the old. If that is the case, it rejects the new packet and transmits the previous ack to indicate the sender to retransmit data.

10. Logs of the required values are maintained in strings on both ends and is finally written on a file.
