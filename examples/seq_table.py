from pandaboxlib import PandA
import numpy as np 

host = 'pandabox'
#host = 'b308a-cab04-pandabox-temp-0'

panda = PandA(host)
panda.connect_to_panda()

# max_length = 128 row
positions = np.arange(1,129,1) 
#positions = np.array((1000,1100,1500,1600,1700,1800)) 

print positions

# repeat=1 POSA<=position outA1=true outA2=false
trigger_config_code = 1507329
t1 = 1
t2 = 1

# table < config position time1 time2
pos_cmd = ['%d %d %d %d\n' % (trigger_config_code, p, t1, t2) for p in positions]
print pos_cmd

# < overwirte; << append
#panda.query('SEQ1.TABLE<<\n'+''.join(pos_cmd))
panda.query('SEQ1.TABLE<\n'+''.join(pos_cmd))


