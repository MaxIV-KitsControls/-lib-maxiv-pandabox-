"""
Class for the Pandabox communication.
Class has no Tango dependence.
KITS @ MAX-IV 2018-05-25.
"""


import socket
import sys
from .save_config import get_lines, read_response, save_state, save_table
from .save_config import save_metatable, save_metadata

class PandA:
   
 
    def __init__(self, host):
        self.host = host
        self.port = 8888
         
        # Create a TCP socket 
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.sock.settimeout(1)
        
    def connect_to_panda(self):
        self.sock.connect((self.host, self.port))

    def disconnect_from_panda(self):
        self.sock.shutdown(socket.SHUT_WR)
        self.sock.close()
        
    def query(self, cmd):
        self.sock.sendall((cmd + '\n').encode())
        val = str(self.sock.recv(4096).decode())
        print(val)
        return val

    def query_value(self, cmd):
        val = self.query(cmd)
        return float(val.strip("\n").split("=")[1])
        
    def _num(self, s):
        try:
            return int(s)
        except ValueError:
            return float(s)

    def numquery(self, cmd):
        val = self.query(cmd)
        val = val.split("=")[-1]
        val = self._num(val)
        print(str(val))
        return val    
    
    def save_config(self, save_file):
        input = get_lines(self.sock)
        output = file(save_file, 'w')
        
        # First save the CONFIG state
        save_state(input, output, '*CHANGES.ATTR?', self.sock)
        save_state(input, output, '*CHANGES.CONFIG?', self.sock)
        # Now save the individual tables.
        # Note that we must read the complete table response before processing!
        tables = list(read_response(input, '*CHANGES.TABLE?', self.sock))
        for table in tables:
            save_table(input, output, table, self.sock)
         
        # Finally the metadata is a bit more tricky, because the table and value results
        # are mixed together.
        metadata = list(read_response(input, '*CHANGES.METADATA?', self.sock))
        for line in metadata:
            save_metadata(input, output, line, self.sock)

    def load_config(self, load_file):
        for line in open(load_file):
            self.sock.sendall(line)

    def send_seq_table(self, block_id, repeats, trigger, 
                       positions, time1, phase1, time2, phase2):
        """
          Function to send an array of positions to the sequencer (SEQ)
          table.
        """
        trigger_options = {'Immediate': 0, 'bita=0': 1, 'bita=1': 2, 'bitb=0': 3, 
            'bitb=1': 4, 'bitc=0': 5, 'bitc=1': 6, 'posa>=position': 7,
            'posa<=position': 8, 'posb>=position': 9, 'posb<=position': 10,
            'posc>=position': 11, 'posc<=position': 12}

        # _b binary code
        repeats_b = '{0:016b}'.format(repeats)                 # 16 bits
        trigger_b = '{0:04b}'.format(trigger_options[trigger]) # 4 bits (17-20)
        phase1_b = ""
        for key,value in sorted(phase1.iteritems()):           # 6 bits (a-f)
            phase1_b = "1"+phase1_b if value else "0"+phase1_b
        phase2_b = ""
        for key,value in sorted(phase2.iteritems()):           # 6 bits (a-f)
            phase2_b = "1"+phase2_b if value else "0"+phase2_b
        code_b =  phase2_b+phase1_b+trigger_b+repeats_b          # 32 bits code
        code = int(code_b,2)
        
        # table < code position time1 time2
        pos_cmd = ['%d %d %d %d\n' % (code, pos, time1, time2) for pos in positions]
        
        # < overwirte; << append
        #self.query('SEQ%d.TABLE<<\n'%(block_id)+''.join(pos_cmd))
        self.query('SEQ%d.TABLE<\n'%(block_id)+''.join(pos_cmd))

    def get_number_channels(self):
        """
        Returns the number of channels enabled in the capture.
        """
        capture_str = self.query('*CAPTURE?')
        capture_str = capture_str.split('\n')
        num_chan = (len(capture_str)-2) #-2 because of . and ""
        return num_chan
