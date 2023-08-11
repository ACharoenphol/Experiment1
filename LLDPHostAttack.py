import argparse
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost, Controller, RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, output, info
from mininet.cli import CLI
from tempfile import mkstemp
from subprocess import check_output, call
import re
import time
import os

from sys import argv
import socket

import subprocess
import numpy as np
import matplotlib.pyplot as plt
import pickle

class SquareTopo(Topo):
    "Square switch topology with five hosts"
    def __init__(self, qos, **opts):
        Topo.__init__(self, **opts)
        switch1 = self.addSwitch('s1', cls=OVSSwitch, failMode="standalone", protocols="OpenFlow13")
        switch2 = self.addSwitch('s2', cls=OVSSwitch, failMode="standalone", protocols="OpenFlow13")
        switch3 = self.addSwitch('s3', cls=OVSSwitch, failMode="standalone", protocols="OpenFlow13")
        switch4 = self.addSwitch('s4', cls=OVSSwitch, failMode="standalone", protocols="OpenFlow13")
        host1 = self.addHost("h1", mac='0a:00:00:00:00:01')
        host2 = self.addHost("h2", mac='0a:00:00:00:00:02')
        host3 = self.addHost("h3", mac='0a:00:00:00:00:03')
        host4 = self.addHost("h4", mac='0a:00:00:00:00:04')
        host5 = self.addHost("h5", mac='0a:00:00:00:00:05')

        # this is the default
        if qos == False:
            #note in the code HTB seems to be the default but does not work well
            # spent some time trying out these. In practice it may depend upon the TC values
            # put in by mininet/mininet/link.py so this may vary from kernel to kernel
            # and different mininet releases
            # the best results seem to be with the following:
            use_tbf=True
            use_hfsc=False
            # have not tried this, probably not relevant unless the app makes use of ECN
            enable_ecn=False
            # while in theory it makes sense to enable this, the problem is that
            # it might delete some of the essential iperf packets so probably best left off
            enable_red=False
            self.addLink(switch1,host1,bw=20,use_tbf=use_tbf,
                         use_hfsc=use_hfsc,enable_ecn=enable_ecn,enable_red=enable_red)
            self.addLink(switch2,host2,bw=20,use_tbf=use_tbf,
                         use_hfsc=use_hfsc,enable_ecn=enable_ecn,enable_red=enable_red)
            self.addLink(switch3,host3,bw=20,use_tbf=use_tbf,
                        use_hfsc=use_hfsc,enable_ecn=enable_ecn,enable_red=enable_red)
            self.addLink(switch4,host4,bw=20,use_tbf=use_tbf,
                         use_hfsc=use_hfsc,enable_ecn=enable_ecn,enable_red=enable_red)
            
            self.addLink(switch1,switch2,bw=10,use_tbf=use_tbf,
                         use_hfsc=use_hfsc,enable_ecn=enable_ecn,enable_red=enable_red)
            self.addLink(switch2,switch3,bw=10,use_tbf=use_tbf,
                         use_hfsc=use_hfsc,enable_ecn=enable_ecn,enable_red=enable_red)
            self.addLink(switch3,switch4,bw=10,use_tbf=use_tbf,
                         use_hfsc=use_hfsc,enable_ecn=enable_ecn,enable_red=enable_red)
            self.addLink(switch4,switch1,bw=10,use_tbf=use_tbf,
                         use_hfsc=use_hfsc,enable_ecn=enable_ecn,enable_red=enable_red)
            # putting host5 last keeps the port numbers in a nice order
            # ie 1 for primary host, 2,3 for switch links, this
            # one is an odd one out in port 4
            self.addLink(switch1,host5,bw=20,use_tbf=use_tbf,
                         use_hfsc=use_hfsc,enable_ecn=enable_ecn,enable_red=enable_red)
        else:
            self.addLink(switch1,host1)
            self.addLink(switch2,host2)
            self.addLink(switch3,host3)
            self.addLink(switch4,host4)
            
            self.addLink(switch1,switch2)
            self.addLink(switch2,switch3)
            self.addLink(switch3,switch4)
            self.addLink(switch4,switch1)
            # putting host5 last keeps the port numbers in a nice order
            # ie 1 for primary host, 2,3 for switch links, this
            # one is an odd one out in port 4
            self.addLink(switch1,host5)
        
    def afterStartConfig(self, net, sdn, qos):
        """configuration to topo that needs doing after starting"""
        s1=net.getNodeByName('s1')
        s2=net.getNodeByName('s2')
        s3=net.getNodeByName('s3')
        s4=net.getNodeByName('s4')
        # this is fairly manual, we want to make s1-s2 link off in STP
        # so setting S4 to be root and s3 secondary root
        # also enabling rstp for quicker startup
        if sdn == False :
            s4.cmd("ovs-vsctl set Bridge s4 rstp_enable=true ")
            s4.cmd("ovs-vsctl set Bridge s4 other_config:rstp-priority=4096")
            s3.cmd("ovs-vsctl set Bridge s3 rstp_enable=true")
            s3.cmd("ovs-vsctl set Bridge s3 other_config:rstp-priority=28672")
            s1.cmd("ovs-vsctl set Bridge s1 rstp_enable=true")
            s2.cmd("ovs-vsctl set Bridge s2 rstp_enable=true")
        # not the default
        if qos == True:
            setTCcmd=os.path.dirname(os.path.realpath(__file__))+"/set-qos.sh"
            # get the list of interfaces that are between switches only (ie ignore lo and host interfaces)
            tcInterfaces = ''
            for sw in net.switches:
                for intf in sw.intfList():
                    if intf.link:
                        intfName = intf.name
                        # this is brittle, but ok if we keep to our simple switch/host naming
                        intfs = [ intf.link.intf1, intf.link.intf2 ]
                        intfs.remove( intf )
                        linkName = intf.name + ' ' + intfs[0].name
                        if (bool(re.search("^s.*s.*$", linkName))):
                            tcInterfaces = tcInterfaces + " " + intf.name
            info("*** Setting qos externally using TC commands from " + setTCcmd +  "\n")
            info("    on interfaces " + tcInterfaces +  "\n")
            cmd = setTCcmd + " " + tcInterfaces
            retVal = call(cmd, shell=True)
            if retVal != 0:
                info("*** error setting qos" +  "\n")
     
def UDPCS1():
    #load_contrib('lldp')
    h1 = net.getNodeByName("h1")
    h3 = net.getNodeByName("h3")

    # Create a datagram socket
    print("Host-Based attack start")
    h1.cmd('python3 UDPServerH1.py &')
    h3.cmd('python3 UDPServerH3.py &')

    print("Host-Based attack from client")
    h3.cmd('python3 UDPClientH3.py &')
    h1.cmd('python3 UDPClientH1.py &')

def TestRTT1():
    h5 = net.getNodeByName("h5")
    myresults = dict()
    #rounds = input('Please input number of rounds:')
    #create another ip list
    ip_list = []
    for ip1 in range(1,5):
        ip_list.append("10.0.0." + str(ip1))

    print("I have started the ping process")    

    for ip2 in ip_list:
        command = "ping -c 300 -i 0.1 "+ str(ip2)
        print(command)
        p = h5.cmd(command)
        #print("ping process has finished")
 
        rtts = []
        outputLines = p
        for myline in outputLines.splitlines():
            #print("test:" + myline)
            if re.match(r'^.+time=([0-9.]+)\sms',myline):
                mystr = re.sub(r'^.+time=([0-9.]+)\sms.*',r'\1',myline)
                #print(mystr)
                rtts.append(float(mystr))
        #print(rtts, "\n")

        rttsSorted = np.sort(rtts)
        rttsSorted = rttsSorted[0:-4]
        print(rttsSorted,"\n") 
        y = 1. * np.arange(len(rttsSorted)) / (len(rttsSorted) - 1)
        myresults[ip2]=[y,rttsSorted]
        #Tmax = max(rttsSorted)
        #print(Tmax)

    file = open('myresultsnoatt.pickle', 'wb')
    pickle.dump(myresults,file)
    file.close()
    file = open('myresultsnoatt.pickle', 'rb')
    myresults = pickle.load(file)
    file.close()

    for address in ip_list:
        y=myresults[address][0]
        rttsSorted=myresults[address][1]
        plt.step(rttsSorted,y,label="10.0.0.5->%s" %address)
        plt.legend(title='Host-to-Host')

    plt.title('Cumulative step histograms (4SW-Ring Topology)')
    plt.xlabel('RTT (ms)')
    plt.ylabel('Density')    
    plt.savefig("CDF of RTT Normal.png")

def TestRTT2():
    h5 = net.getNodeByName("h5")
    myresults1 = dict()
    #rounds = input('Please input number of rounds:')
    #create another ip list
    ip_list1 = []
    for ip3 in range(1,5):
        ip_list1.append("10.0.0." + str(ip3))

    print("I have started the ping process")    

    for ip4 in ip_list1:
        command1 = "ping -c 300 -i 0.1 "+ str(ip4)
        print(command1)
        p1 = h5.cmd(command1)
        #print("ping process has finished")
 
        rtts1 = []
        outputLines1 = p1
        for myline in outputLines1.splitlines():
            #print("test:" + myline)
            if re.match(r'^.+time=([0-9.]+)\sms',myline):
                mystr = re.sub(r'^.+time=([0-9.]+)\sms.*',r'\1',myline)
                #print(mystr)
                rtts1.append(float(mystr))
        #print(rtts, "\n")

        rttsSorted1 = np.sort(rtts1)
        rttsSorted1 = rttsSorted1[0:-5]
        print(rttsSorted1,"\n") 
        z = 1. * np.arange(len(rttsSorted1)) / (len(rttsSorted1) - 1)
        myresults1[ip4]=[z,rttsSorted1]
        #Tmax = max(rttsSorted)
        #print(Tmax)

    file = open('myresultsWAtt.pickle', 'wb')
    pickle.dump(myresults1,file)
    file.close()
    file = open('myresultsWAtt.pickle', 'rb')
    myresults1 = pickle.load(file)
    file.close()

    for address1 in ip_list1:
        y=myresults1[address1][0]
        rttsSorted1=myresults1[address1][1]
        plt.step(rttsSorted1,y,label="10.0.0.5->%s" %address1)
        plt.legend(title='Host-to-Host')

    plt.title('Cumulative step histograms (4SW-Ring Topology)')
    plt.xlabel('RTT (ms)')
    plt.ylabel('Density')    
    plt.savefig("CDF of RTT W Attack.png")

def HostAttack(self,line):
    TestRTT1()
    UDPCS1()
    TestRTT2()

if __name__ == '__main__':
    # parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c","--controller", help="sdn controller ip [127.0.0.1]", default="127.0.0.1")
    parser.add_argument("-p","--port", type=int, help="sdn controller port [6633]", default=6633)
    parser.add_argument("-t","--tests", action='store_true', help="run tests automatically")
    parser.add_argument("-q","--qos", action='store_true', help="configure qos outside mininet")
    group=parser.add_mutually_exclusive_group()
    group.add_argument("-s", "--sdn", action='store_true', help="enable SDN mode (the default)")
    group.add_argument("-n", "--normal", action='store_true', help="enable STP mode (not the default)")
    args = parser.parse_args()
    if args.normal == False:
        args.sdn = True
    if args.sdn == True:
        info("Running in SDN mode" + "\n" +  "\n")
    else:
        info("Running in STP mode" +  "\n")
        
    # kill any old mininet first
    os.system("mn -c > /dev/null 2>&1")    
    setLogLevel( 'info' )
    topo = SquareTopo(args.qos)
    net = Mininet( topo=topo,
                   link=TCLink,
                   controller=None)
    net.argsSdn=args.sdn
    if args.sdn :
        net.addController( 'c0', controller=RemoteController, ip=args.controller, port=args.port )

    net.start()
    info("Waiting for startup and network to settle (please wait 5 seconds)" +  "\n")
    time.sleep(5)
    
    #topo.afterStartConfig(net,args.sdn,args.qos)
    #print "*** Dumping host connections"
    #dumpNodeConnections(net.hosts)
    #print "*** Dumping switch connections"
    #dumpNodeConnections(net.switches)
   
    #if args.sdn == False:
    #    info("*** STP state of the switches" +  "\n")
    #    printSTP()
    #    info("*** done printing STP state" +  "\n")
    #    info("" +  "\n")
    #if args.qos == True:
    #    info("*** Showing Queues in s1-eth2" +  "\n")
    #    s1 = net.getNodeByName("s1")
    #    s1.cmdPrint("tc -g class show dev s1-eth2")        
    
    #if args.tests == True :
    #    net.pingAll()
    #    info("" +  "\n")
    
    #CLI.do_test1 = test1
    #CLI.do_test2 = test2
    #CLI.do_test3 = test3
    #CLI.do_test4 = test4
    CLI.do_HostAttack = HostAttack
    
    info("enter \"quit\" to exit or issue mininet commands if you know them" +  "\n")
    info("you can run the tests using the commands \"HostAttack\" or \"\" ...." +  "\n")
    CLI(net)
    net.stop()