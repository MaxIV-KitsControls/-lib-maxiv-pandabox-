from pandaboxlib import PandA
import numpy as np 
import time 

host = 'pandabox'

panda = PandA(host)
panda.connect_to_panda()

# trigger source (how fast to acquire)
panda.query('CLOCKS.B_PERIOD=.01')
panda.query('CLOCKS.B_PERIOD.UNITS=s')

# gate signal to PCAP, how long acquiring
acq_time = 2
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
panda.query('FMC_ACQ427_IN.VAL1.CAPTURE=No')
panda.query('FMC_ACQ427_IN.VAL2.CAPTURE=Value')

# prepare acquisition
# reset values
panda.query('BITS.B=0')
panda.query('*PCAP.DISARM=')

# arm and send gate pulse
panda.query('*PCAP.ARM=')
panda.query('BITS.B=1')

acq_status = panda.query('*PCAP.STATUS?')
#print panda.numquery('*PCAP.STATUS?')
print "PandA is acquiring data."
while "Busy" in acq_status:
   acq_status = panda.query('*PCAP.STATUS?')
   time.sleep(0.2)

points_acquired = panda.numquery('*PCAP.CAPTURED?')
print "Points acquired: ", points_acquired
