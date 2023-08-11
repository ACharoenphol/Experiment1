import socket
import time
from scapy.all import *
from threading import Thread
from queue import Queue

load_contrib('lldp')

def myPacketProcess(x,queue):
    #print(x.summary())
    queue.put(bytes(x))
    
def producer(queue):
    counter = 0
    while True:
        pack = sniff(iface="h3-eth0",
                     filter="ether proto 0x8942 or ether proto 35020",
                     prn = lambda x:myPacketProcess(x,queue),store=False)
        time.sleep(1000)
        #queue.put(bytes(pack[0]))

        print("I never get here!")
        counter = counter + 1

# Create a UDP socket at client side
def consumer(queue):
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    captureIndex=0
    while True:
        item = queue.get()
        pack=Ether(item)
        print("Caputure packet number:" + str(captureIndex))
        captureIndex = captureIndex + 1
        #pack.show()
        bytesToSend = item
        serverAddressPort   = ("10.0.0.1", 20001)
        bufferSize          = 1024
        # Send to server using created UDP socket
        UDPClientSocket.sendto(bytesToSend , serverAddressPort)
        #msgFromServer = UDPClientSocket.recvfrom(bufferSize)
        #msg = "Message length from server {}".format(len(msgFromServer[0]))
        #print(msg)
        time.sleep(5)

# create the shared queue
queue = Queue()

# start the consumer
consumer = Thread(target=consumer, args=(queue,))
consumer.start()

# start the producer
producer = Thread(target=producer, args=(queue,))
producer.start()

# wait for all threads to finish
producer.join()
consumer.join()

