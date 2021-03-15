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
        """Initializer"""
        self.sock = sock
        self.buf = ''
        self.lines = []

    def __iter__(self):
        """Iterator (self)"""
        return self

    def __read_lines(self, buf):
        """Read multiple response lines from host as sequence

        N.b. Only returns on _multiline_ responses!

        """
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
        """Iterate over response lines"""
        if self.lines:
            line = self.lines[0]
            del self.lines[0]
        else:
            line, self.lines, self.buf = self.__read_lines(self.buf)
        return line

    def _read_response(self, command):
        """Send command to host and read multi-value response

        N.b. Raises error on single reponses!

        """
        self.sock.sendall((command + '\n').encode())
        for line in self:
            if line[0] == '!':
                yield line[1:]
            elif line[0] == '.':
                break
            else:
                assert False, 'Malformed response: "{line}"'.format(line)

    def _read_idn(self):
        """Return identifcation string"""
        command = "*IDN?"
        self.sock.sendall(f"{command}\n".encode())
        bufsize = 2**16
        idn = str(self.sock.recv(bufsize).decode())
        if not idn.startswith("OK ="):
            raise ValueError(f"'{command}' did not return OK")
        response = idn.split("=")[1].rstrip("\n")
        return response

    def _save_state(self, file, command):
        """Save multi-value response from command to file"""
        for line in self._read_response(command):
            print(line, file=file)

    def _save_table(self, file, table):
        """Save table field to file

        N.b. Table values are base64 encoded

        """
        assert table[-1] == '<'
        print(table + 'B', file=file)
        for line in self._read_response(table[:-1] + '.B?'):
            print(line, file=file)
        print('', file=file)

    def _save_metatable(self, file, table):
        """Save table field to file

        N.b. Table values are ASCII encoded

        """
        print(table, file=file)
        for line in self._read_response(table[:-1] + '?'):
            print(line, file=file)
        print('', file=file)

    def _save_metadata(self, file, line):
        """Save metadata to file

        Metadata fields can be single or table types

        """
        if line[-1] == '<':
            self._save_metatable(file, line)
        else:
            print(line, file=file)

    def _save_fw_version(self, file):
        """Save firmware version

        The blocks referenced in a design must be available in the currently
        installed FPGA app. This can be ensured in a semi-automatic fashion by
        specifying the required FW version in the saved design and subsequently
        validating it when loading a design (see ``_validate_fw_version``).

        N.b. Whilst the entire system identification string is saved, only the
        FPGA field (i.e. installed FPGA app) is likely of interest.

        """
        idn = self._read_idn()
        file.write(f"*ECHO {idn}?\n")      # Save as ECHO to avoid attempted assignment on load

    def _validate_fw_version(self, file):
        """Validate firmware version

        The blocks referenced in a design must be available in the currently
        installed FPGA app. This can be ensured in a semi-automatic fashion by
        specifying the required FW version in the saved design (see
        ``_save_fw_version``) and subsequently validating it when loading a
        design.

        N.b. Whilst the entire system identification string is saved, only the
        FPGA field (i.e. installed FPGA app) is likely of interest.

        """

        def parse_fpga_from_idn(idn):
            return idn.split(": ")[2]

        # Read installed FPGA FW version
        fpga_installed = parse_fpga_from_idn(self._read_idn())

        # Read design FPGA FW version
        offset = file.tell()
        file.seek(0)
        fpga_design = parse_fpga_from_idn(file.readline())
        file.seek(offset)

        # Validate
        return fpga_design == fpga_installed

    def save(self, path):
        """Save design to file"""
        with open(path, "wt") as file:

            # Save firmware version
            self._save_fw_version(file)

            # Save the CONFIG state
            self._save_state(file, '*CHANGES.ATTR?')
            self._save_state(file, '*CHANGES.CONFIG?')

            # Save individual tables
            #
            #   N.b. Must read complete table response before processing!
            #
            tables = list(self._read_response('*CHANGES.TABLE?'))
            for table in tables:
                self._save_table(file, table)

            # Save metadata
            #
            #   N.b. Table and value results are mixed together
            #
            metadata = list(self._read_response('*CHANGES.METADATA?'))
            for line in metadata:
                self._save_metadata(file, line)

    def load(self, path):
        """Load design from file"""
        with open(path,"rt") as file:

            # Validate FPGA firmware version
            if not self._validate_fw_version(file):
                raise ValueError("Design and installed FPGA FW versions do not match")

            # Apply design
            for line in file:
                self.sock.sendall(line.encode())


class PandA:

    sock = None

    def __init__(self, host, port=8888):
        """Initializer"""
        self.host = host
        self.port = port

    def __del__(self):
        """Finalizer/destructor

        Actions:

          * Close socket gracefully

        """
        if self.sock is not None:
            self.disconnect_from_panda()

    def connect_to_panda(self):
        """Create socket connection to host"""
        if self.socket is None
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(
                socket.SOL_TCP,          # Disable Nagle algorithm
                socket.TCP_NODELAY,      # (https://linux.die.net/man/7/tcp)
                1                        # Is this really necessary?
            )
            self.sock.settimeout(1)
            self.sock.connect((self.host, self.port))

    def disconnect_from_panda(self):
        """Close socket connection to host"""
        if self.socket is not None
            self.sock.shutdown(socket.SHUT_WR)
            self.sock.close()
            self.sock = None

    def query(self, cmd):
        """Send command to host and return response"""
        self.sock.sendall((cmd + '\n').encode())
        val = str(self.sock.recv(4096).decode())
        print(val)
        return val

    def query_value(self, cmd):
        """Send command to host and return response as float"""
        val = self.query(cmd)
        return float(val.strip("\n").split("=")[1])

    def _num(self, s):
        """Cast value to int, else float"""
        try:
            return int(s)
        except ValueError:
            return float(s)

    def numquery(self, cmd):
        """Send command to host and return response as int or float"""
        val = self.query(cmd)
        val = val.split("=")[-1]
        val = self._num(val)
        print(str(val))
        return val

    def save_config(self, path):
        """Save design to file"""
        if self.sock is not None:
            self.disconnect_from_panda()
        self.connect_to_panda()              # Ensure first `*CHANGES` request on connection
        _Design(self.sock).save(path)

    def load_config(self, path):
        """Load design from file"""
        _Design(self.sock).load(path)

    def send_seq_table(self, block_id, repeats, trigger,
                       positions, time1, phase1, time2, phase2):
        """Send array of positions to sequencer (SEQ) table"""
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
        """Return number of enabled capture channels"""
        capture_str = self.query('*CAPTURE?')
        capture_str = capture_str.split('\n')
        num_chan = (len(capture_str) - 2)  # -2 because of . and ""
        return num_chan
