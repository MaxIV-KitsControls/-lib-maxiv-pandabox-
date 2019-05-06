from pandaboxlib import PandA
import numpy as np 

#host = 'pandabox'
host = 'b308a-cab04-pandabox-temp-0'

panda = PandA(host)
panda.connect_to_panda()

# max_length = 128 row
positions = np.arange(1,129,1) 
#positions = np.array((1000,1100,1500,1600,1700,1800)) 

print positions

# repeat=1 POSA<=position outA1=true outA2=False
t1 = 1
t2 = 1
trigger_dic = {'Immediate': 0, 'bita=0': 1, 'bita=1': 2, 'bitb=0': 3, 'bitb=1': 4,
           'bitc=0': 5, 'bitc=1': 6, 'posa>=position': 7, 'posa<=position': 8,
           'posb>=position': 9, 'posb<=position': 10, 'posc>=position': 11,
           'posc<=position': 12}

# user options
repeats = 1
trigger = 'posa>=position'
phase1 = {'a': True,'b': False, 'c': False,'d': False, 'e': False, 'f': False}
phase2 = {'a': False,'b': False, 'c': False,'d': False, 'e': False, 'f': False}


repeats_b = '{0:016b}'.format(repeats)             # 16 bits
trigger_b = '{0:04b}'.format(trigger_dic[trigger]) # 4 bits (17-20)
phase1_b = ""
for key,value in sorted(phase1.iteritems()):       # 6 bits (a-f)
    phase1_b = "1"+phase1_b if value else "0"+phase1_b
phase2_b = ""
for key,value in sorted(phase2.iteritems()):       # 6 bits (a-f)
    phase2_b = "1"+phase2_b if value else "0"+phase2_b
 
code =  phase2_b+phase1_b+trigger_b+repeats_b      # 32 bits code
code = int(code,2)

# table < config position time1 time2
pos_cmd = ['%d %d %d %d\n' % (code, p, t1, t2) for p in positions]
#print pos_cmd

# < overwirte; << append
#panda.query('SEQ1.TABLE<<\n'+''.join(pos_cmd))
panda.query('SEQ1.TABLE<\n'+''.join(pos_cmd))


