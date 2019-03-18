from pandaboxlib import PandA
import numpy as np 
import time 
import socket
from multiprocessing.pool import ThreadPool

def get_data(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall('\n')
    data = s.recv(1024)
    raw_data = ""
    while True:
#        print 'data:', repr(data)
        data = s.recv(1024)
        raw_data += data 
        if "END" in repr(data):
            break
    s.close()
#    print 'Received data:', repr(raw_data)
    return raw_data

host = 'pandabox'

panda = PandA(host)
panda.connect_to_panda()

# trigger source (how fast to acquire)
panda.query('CLOCKS.B_PERIOD=0.001')
panda.query('CLOCKS.B_PERIOD.UNITS=s')

# gate signal to PCAP, how long acquiring
acq_time = 1 
acq_time_units = "s"
panda.query('PULSE1.WIDTH=%f' % (acq_time))
panda.query('PULSE1.WIDTH.UNITS=%s' % (acq_time_units))

# linking blocks
# PCAP
panda.query('PCAP.TRIG=CLOCKS.OUTB')
panda.query('PCAP.ENABLE=PULSE1.OUT')
# PULSE1
panda.query('PULSE1.TRIG=BITS.OUTB')

# set values to be acquired by PCAP
panda.query('FMC_ACQ427_IN.VAL1.CAPTURE=Value')
panda.query('FMC_ACQ427_IN.VAL2.CAPTURE=Value')

# prepare acquisition
# reset values
panda.query('BITS.B=0')
panda.query('*PCAP.DISARM=')

# arm and send gate pulse
panda.query('*PCAP.ARM=')
panda.query('BITS.B=1')

# start data acquisition thread
pool = ThreadPool(processes=1)
async_result = pool.apply_async(get_data, args = (host, 8889))

acq_status = panda.query('*PCAP.STATUS?')
#print panda.numquery('*PCAP.STATUS?')
print "PandA is acquiring data."
while "Busy" in acq_status:
   acq_status = panda.query('*PCAP.STATUS?')
   time.sleep(0.2)

points_acquired = panda.numquery('*PCAP.CAPTURED?')
print "Points acquired: ", points_acquired

data_acquired = async_result.get()

#print "Data received: ", data_acquired

# comment last line
data_acquired_split = data_acquired.split("END")
data_acquired = data_acquired_split[0] + "#END " + data_acquired_split[1]

# save file
data_file = open("data_file.dat", "w")
data_file.write(data_acquired)
data_file.close()


