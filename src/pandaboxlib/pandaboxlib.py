"""
Class for the Pandabox communication.
Class has no Tango dependence.
KITS @ MAX-IV 2018-05-25.
"""

import socket
import sys


class _Design:
    """Helper class for saving/loading a PandABox block-design

    Based on example client in `PandABlocks-server <https://github.com/PandABlocks/PandABlocks-server/blob/master/python/save-state>`_

    """

    def __init__(self, sock):
        self.sock = sock
        self.buf = ''
        self.lines = []

    def __iter__(self):
        return self

    def __read_lines(self, buf):
        while True:
            bufsize = 2**16
            rx = str(self.sock.recv(bufsize).decode())
            if not rx:
                raise StopIteration
            buf += rx

            lines = buf.split('\n')
            if len(lines) > 1:
                break

        return lines[0], lines[1:-1], lines[-1]

    def __next__(self):
        if self.lines:
            line = self.lines[0]
            del self.lines[0]
        else:
            line, self.lines, self.buf = self.__read_lines(self.buf)
        return line

    def _read_response(self, command):
        self.sock.sendall((command + '\n').encode())
        for line in self:
            if line[0] == '!':
                yield line[1:]
            elif line[0] == '.':
                break
            else:
                assert False, 'Malformed response: "{line}"'.format(line)

    def _save_state(self, file, command):
        for line in self._read_response(command):
            print(line, file=file)

    def _save_table(self, file, table):
        assert table[-1] == '<'
        print(table + 'B', file=file)
        for line in self._read_response(table[:-1] + '.B?'):
            print(line, file=file)
        print('', file=file)

    def _save_metatable(self, file, table):
        print(table, file=file)
        for line in self._read_response(table[:-1] + '?'):
            print(line, file=file)
        print('', file=file)

    def _save_metadata(self, file, line):
        if line[-1] == '<':
            self._save_metatable(file, line)
        else:
            print(line, file=file)

    def save(self, path):
        with open(path, "wt") as file:

            # First save the CONFIG state
            self._save_state(file, '*CHANGES.ATTR?')
            self._save_state(file, '*CHANGES.CONFIG?')

            # Now save the individual tables.
            # Note that we must read the complete table response before processing!
            tables = list(self._read_response('*CHANGES.TABLE?'))
            for table in tables:
                self._save_table(file, table)

            # Finally the metadata is a bit more tricky, because the table and value results
            # are mixed together.
            metadata = list(self._read_response('*CHANGES.METADATA?'))
            for line in metadata:
                self._save_metadata(file, line)

    def load(self, path):
        with open(path,"rt") as file:
            for line in file:
                self.sock.sendall(line.encode())

class PandA:

    sock = None

    def __init__(self, host, port=8888):
        self.host = host
        self.port = port

    def __del__(self):
        if self.sock is not None:
            self.disconnect_from_panda()

    def connect_to_panda(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(
            socket.SOL_TCP,          # Disable Nagle algorithm
            socket.TCP_NODELAY,      # (https://linux.die.net/man/7/tcp)
            1                        # Is this really necessary?
        )
        self.sock.settimeout(1)
        self.sock.connect((self.host, self.port))

    def disconnect_from_panda(self):
        self.sock.shutdown(socket.SHUT_WR)
        self.sock.close()
        self.sock = None

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

    def save_config(self, path):
        _Design(self.sock).save(path)

    def load_config(self, load_file):
        _Design(self.sock).load(path)

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
        repeats_b = '{0:016b}'.format(repeats)  # 16 bits
        trigger_b = '{0:04b}'.format(trigger_options[trigger])  # 4 bits (17-20)
        phase1_b = ""
        for key, value in sorted(phase1.items()):  # 6 bits (a-f)
            phase1_b = "1" + phase1_b if value else "0" + phase1_b
        phase2_b = ""
        for key, value in sorted(phase2.items()):  # 6 bits (a-f)
            phase2_b = "1" + phase2_b if value else "0" + phase2_b
        code_b = phase2_b + phase1_b + trigger_b + repeats_b  # 32 bits code
        code = int(code_b, 2)

        # table < code position time1 time2
        pos_cmd = ['%d %d %d %d\n' % (code, pos, time1, time2) for pos in positions]

        # < overwirte; << append
        # self.query('SEQ%d.TABLE<<\n'%(block_id)+''.join(pos_cmd))
        self.query('SEQ%d.TABLE<\n' % (block_id) + ''.join(pos_cmd))

    def get_number_channels(self):
        """
        Returns the number of channels enabled in the capture.
        """
        capture_str = self.query('*CAPTURE?')
        capture_str = capture_str.split('\n')
        num_chan = (len(capture_str) - 2)  # -2 because of . and ""
        return num_chan
