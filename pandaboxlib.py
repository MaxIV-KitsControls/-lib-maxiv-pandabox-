"""
Class for the Pandabox communication.
Class has no Tango dependence.
KITS @ MAX-IV 2018-05-25.
"""


import socket
import sys
from save_config import get_lines, read_response, save_state, save_table
from save_config import save_metatable, save_metadata

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
        self.sock.sendall(cmd + '\n')
        val = str(self.sock.recv(4096))
        print(val)
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
