#!/usr/bin/env python3

from nwlib import nwtel, nwdb
import sys

chlen = nwdb(sys.argv[1])
ipswitch = chlen.base('switchP')
port = chlen.base('PortP')
ip = chlen.base('IP')
switch = nwtel(ipswitch)

print ('Number:\x1b[1m {}\x1b[0m    Vznos:\x1b[1m {}\x1b[0m'.format(chlen.base('Number',), chlen.base('Vznos',)))
print ('Number_net: \x1b[1m {}\x1b[0m    Number_serv: \x1b[1m {}\x1b[0m    dhcp_type: \x1b[1m {}\x1b[0m'.format(chlen.base('Number_net',),chlen.base('Number_serv',),chlen.base('dhcp_type',)))
print ('IP:\x1b[1m {}\x1b[0m    Add_IP:\x1b[1m {}\x1b[0m'.format(ip, chlen.base('Add_IP')))
print ('Mask:\x1b[1m {}\x1b[0m    Gate:\x1b[1m {}\x1b[0m    vlan:\x1b[1m {}\x1b[0m'.format(chlen.base('Masck'), chlen.base('Gate'), chlen.base('vlan')))
print ('Switch: \x1b[4m{}\x1b[0m    Port: \x1b[4m{}\x1b[0m'.format(ipswitch, port))

if switch == 0 or switch == 1: print ("\x1b[31mCan't connect to switchP. Can't get Gate.\x1b[0m"); sys.exit()
if chlen.base('Gate').split('.')[0] == '10': ipgate = chlen.base('Gate')
else:
	ipgate = switch.extgate(ip)
	switch = nwtel(ipswitch)
if ipgate == None: print ("\x1b[31mCheck gate yourself\x1b[0m")
else:
	print ('RealGate:\x1b[1m {}\x1b[0m'.format(ipgate))
	gate = nwtel(ipgate)

print ('=======================================')

#block for realgate
if gate == 0:
	print ("\x1b[31mThere\'s no gate\x1b[0m"); sys.exit()
elif gate == 1:
	print ("\x1b[31m\x1b[1mTHE GATE IS DOWN!!!\x1b[0m"); sys.exit()

#block for gate arpentry
arp = gate.arpbyip(ip) + gate.arpbyip_3630(ip)
if len(arp) == 0:
	print ("\x1b[31mThere\'s no ARP. Check acl and vlan\x1b[0m")
else:
	print ('\x1b[1m\x1b[31mARP: \x1b[0mIP:\x1b[1m {}\x1b[0m    Mac:\x1b[1m {}\x1b[0m'.format(arp[0][0], arp[0][1]))
del gate

#block for MAC
if switch == 0:
	print ("\x1b[31mWhere is his switch?\x1b[0m"); sys.exit()
elif switch == 1:
	print ("\x1b[31mSwitch is down. Check japan already\x1b[0m"); sys.exit()
mac = switch.fdbbyport(port)
if len(mac) == 0:
	print ("\x1b[31mThere\'s no MAC. Check link and vlan\x1b[0m")
else:
	for i in mac: print ('\x1b[1m\x1b[31mFDB: \x1b[0mVlan ID:\x1b[1m {}\x1b[0m    Mac:\x1b[1m {}\x1b[0m    Port:\x1b[1m {}\x1b[0m'.format(i[0], i[1], port))

switch.expint() #interact
sys.exit()