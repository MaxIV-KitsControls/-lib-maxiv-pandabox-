from pandaboxlib import PandA
import numpy as np 

host = 'pandabox'

panda = PandA(host)
panda.connect_to_panda()

panda.query('CLOCKS.A_PERIOD=.1')
panda.query('CLOCKS.A_PERIOD.UNITS=s')

panda.query('PGEN1.TRIG=CLOCKS.OUTA')
panda.query('PGEN1.CYCLES=1')

num_pts = 201
pos_i = 0
pos_f = 1000
pos = np.linspace(pos_i, pos_f, num=num_pts)

pos_cmd = ['%d\n' % p for p in pos]
print pos_cmd

panda.query('PGEN1.TABLE<\n'+''.join(pos_cmd))
panda.query('PCOMP1.INP=PGEN1.OUT')
panda.query('PCOMP1.START=0')
step_size = 10 
pnum = (pos_f - pos_i) / step_size
panda.query('PCOMP1.STEP=%d' % (step_size))
print 'pnum: ', pnum
panda.query('PCOMP1.PNUM=%d' % (pnum))
panda.query('PCOMP1.RELATIVE=Absolute')
panda.query('PCOMP1.DIR=Positive')

panda.query('TTLOUT1.VAL=PCOMP1.OUT')


panda.query('PCOMP1.ENABLE=BITS.ZERO')
panda.query('PCOMP1.ENABLE=BITS.ONE')
panda.query('PGEN1.ENABLE=BITS.ONE')

