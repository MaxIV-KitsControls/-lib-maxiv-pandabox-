from pandaboxlib import PandA
import numpy as np 

#host = 'pandabox'
host = 'b308a-cab04-pandabox-temp-0'

panda = PandA(host)
panda.connect_to_panda()

# max_length = 4096 rows
positions = np.arange(1,20,1) 
#positions = np.array((1000,1100,1500,1600,1700,1800)) 

print positions

# user options for SEQ table
repeats = 1
trigger = 'posb>=position'
time1= 1
phase1 = {'a': True,'b': False, 'c': False,'d': False, 'e': False, 'f': False}
time2= 1
phase2 = {'a': False,'b': False, 'c': False,'d': False, 'e': False, 'f': False}

panda.send_seq_table(1, repeats, trigger, positions,
                     time1, phase1, time2, phase2)


