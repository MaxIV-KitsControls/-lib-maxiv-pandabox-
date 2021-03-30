"""
Class for the Pandabox communication.
Class has no Tango dependence.
KITS @ MAX-IV 2018-05-25.
"""

import socket
import sys
import typing
import re
import warnings

# Use standard python logging for debug output.
import logging
logger = logging.getLogger(__name__)


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

    _response_success = "OK"
    _response_value = "OK ="
    _response_error = "ERR "
    _response_multivalue = ("!",".")
    _operator_query = "?"
    _operator_assign = "="
    _operator_assign_table = ("<", "<<", "<B", "<<B")

    def __init__(self, host, port=8888):
        """Initializer"""

        # Connection attributes
        self.host = host
        self.port = port
        self._sock = None
        self._recv_buffer = ""

    def __del__(self):
        """Finalizer/destructor

        Actions:

          * Close socket gracefully

        """
        if self._sock is not None:
            self.disconnect_from_panda()

    def connect(self):
        """Create socket connection to host"""
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setsockopt(
                socket.SOL_TCP,          # Disable Nagle algorithm
                socket.TCP_NODELAY,      # (https://linux.die.net/man/7/tcp)
                1                        # Is this really necessary?
            )
            timeout = 5                  # 5 second socket timeout
            self._sock.settimeout(timeout)
            self._sock.connect((self.host, self.port))

    def disconnect(self):
        """Close socket connection to host"""
        if self._sock is not None:
            self._sock.shutdown(socket.SHUT_WR)
            self._sock.close()
            self._sock = None

    def _send(self, cmd):
        """Send generic command

        Appends newline

        """
        return self._sock.sendall(       # Should return None
            f"{cmd}\n".encode()
        )

    def _recv(self):
        r"""Iterate over response lines

        tl;dr: Generator for iteration over reponses

        As so eloquantly put by Gordon McMillan;

            Now if you think about that a bit, you’ll come to realize
            a fundamental truth of sockets: messages must either be
            fixed length (yuck), or be delimited (shrug), or indicate
            how long they are (much better), or end by shutting down
            the connection. The choice is entirely yours, (but some
            ways are righter than others).
            
            --- https://docs.python.org/3/howto/sockets.html

        Whilst the PandABlocks-server protocol opts for ('\n') delimited
        messages, multi-value responses share the same delimiter. As such,
        simple tokenization on the delimiter will be insufficient, and
        instead partial multi-value responses must be detected and handled.

        This method receives data from the socket until the data ends with
        the delimiter _and_ the received response is confirmed not to be a
        partial multi-value response. The tokenized responses are periodically
        yielded as generator elements.

        N.b.

          * Delimiters are always stripped
          * Multi-value responses are returned value-by-value (no grouping)

        """
        delimiter = "\n"
        line = self._response_multivalue[0]
        while (
            self._recv_buffer                         # Partial response in buffer
        ) or (
            line[0] == self._response_multivalue[0]   # Partial multi-value response
        ):

            # Read from socket
            while delimiter not in self._recv_buffer:
                bufsize = 2**12
                try:
                    byte_buffer = self._sock.recv(bufsize).decode()
                except socket.timeout as err:       # Network issues…
                    self.disconnect_from_panda()    # …close and abort!
                    raise err
                self._recv_buffer += str(byte_buffer)

            # Tokenize
            lines = self._recv_buffer.split(delimiter)
            self._recv_buffer = lines[-1]
            lines = lines[:-1]
            for line in lines:
                yield line

    @property
    def _responses(self):
        """Response iterator"""
        return self._recv()

    def _response_is_success(self, response):
        """Test for success response"""
        return response == self._response_success

    def _response_is_value(self, response):
        """Test for value response"""
        return response.startswith(self._response_value)

    def _response_is_error(self, response):
        """Test for error response"""
        return response.startswith(self._response_error)

    def _response_is_multivalue(self, response):
        """Test for multi value response"""
        return response.startswith(self._response_multivalue)

    def query_(self, target: str) -> typing.Union[str, list]:
        r"""Query target value

        Interrogate ``target`` and returns current value.

        Single value responses are returned as a string stripped of ``OK =``
        prefix and final ``\n`` delimiter.

        Multiple value responses are returned as an iterable of strings. Each 
        string is stripped of ``!`` prefix and final ``\n`` and `.` delimiters.

        Error responses raise ``RuntimeError``.

        :param str target: Target, with or without ``?`` suffix
        :return: Target value
        :rtype: str or list
        :raises RuntimeError: On error response

        """
        if target[-1] != "?":
            target += "?"
        self._send(target)
        responses = self._responses
        response = next(responses)
        if self._response_is_error(response):
            raise RuntimeError(response.lstrip(self._response_error))
        elif self._response_is_value(response):
            return response.lstrip(self._response_value)
        elif self._response_is_multivalue(response):
            strip = lambda r: r.lstrip(self._response_multivalue[0])
            response = [ strip(response) ]
            response += [ strip(r) for r in responses ]
            assert response[-1] == "."
            return response[:-1]
        elif self._response_is_success(response):
            raise ValueError("Queries should not return success")
        else:
            raise ValueError(f"Unknown response ('{response}')")

    def assign(self, target: str, value: str, operator: str="=") -> typing.NoReturn:
        """Assign value to target

        Assign ``value`` to ``target``. ``target`` is a valid block field of
        attribute. ``value`` is a string or numeric.

        Successful assignment returns ``None``. Failed assignment raises
        ``RuntimeError``.

        :param str target: Target field or attribute
        :param value: Value to assign
        :rtype: None
        :raises RuntimeError: On failed assignment

        """
        operators = (
            self._operator_assign,
            *self._operator_assign_table
        )
        if operator not in operators:
            raise ValueError(f"Unknown operator ('{operator}')")
        self._send(f"{target}{operator}{value}")
        responses = self._responses
        response = next(responses)
        if self._response_is_error(response):
            raise RuntimeError(response.lstrip(self._response_error))
        elif self._response_is_value(response):
            raise ValueError("Assignments should not return values")
        elif self._response_is_multivalue(response):
            raise ValueError("Assignments should not return multi values")
        elif self._response_is_success(response):
            pass
        else:
            raise ValueError(f"Unknown response ('{response}')")

    def assign_table(self, target: str, values: typing.Sequence, operator: str="<") -> typing.NoReturn:
        """Assign table values to target

        Assign table values ``values`` to table ``target``. ``target``
        is a valid block field or attribute of table type. ``values`` is an 
        iterable of table values.

        The optional ``operator`` keyword argument specifies the table value
        assignment operator;

        * ``<``: Normal table write, overwrite table
        * ``<<``: Normal table write, append table
        * ``<B``: Normal table write, overwrite table
        * ``<<B``: Normal table write, append table

        If not supplied, the default operator is ``<``.

        Successful assignment returns ``None``. Failed assignment raises
        ``RuntimeError``.

        :param str target: Target field or attribute
        :param values: Table values to assign
        :type values: iterable of str or numeric
        :param str operator: Assignment operator
        :rtype: None
        :raises RuntimeError: On failed assignment

        """
        
        value = "\n"                     # Newline after operator
        value += "".join((f"{value}\n" for value in values))
        return self.assign(target, value, operator)

    def _dump_value(self, value: str) -> str:
        """Format value responses for dump"""
        return f"{value}\n"

    def _dump_table(self, target: str, encoding="base64") -> str:
        """Format table for dump
        
        :param str table: Table field target
        
        """
        output = ""
        operators = {
            "base64": "<B",
            "ascii": "<"
        }
        if encoding not in operators:
            raise ValueError(f"Unknown table value encoding('{encoding}')")
        output += f"{target}{operators[encoding]}\n"
        attributes = {
            "base64": ".B",
            "ascii": ""
        }
        rows = self.query_(f"{target}{attributes[encoding]}?")
        for row in rows:
            output += f"{row}\n"
        output += "\n"                      # Blank line termination
        return output

    def dump_design(self, file: typing.TextIO) -> typing.NoReturn:
        """Dump current design to file

        Dump current design to the writable text file ``file``. The contents of
        the output file are simply the assignment commands required to recover
        the current design.

        The design is considered to consist of;

        * Block field values
        * Block field attribute values which contribute to ``*CHANGES.ATTR?`` [#]_
        * Block and system metadata field values

        N.b. Current bits, position and polled read values are _not_ considered
        part of the design, and are thus not included in the dump.

        .. [#] See https://pandablocks-server.readthedocs.io/en/latest/fields.html#summary-of-attributes

        :param TextIO file: Ouput file
        :rtype: None
        
        """

        # Declare output
        output = ""              # Write at end to avoid partial design dumps
        
        # Dump identification string
        #
        #   Dumped designs are defined within the context of the currently
        #   running firmware; i.e. they depend on the blocks exposed by the
        #   installed PandABlocks-FPGA app. Designs cannot therefore be
        #   guaraneteed to load correctly on PandABox units running different
        #   firmware as different blocks may be exposed.
        #
        #   The system identification string — containing the current firmware
        #   version — is therefore dumped in order to provide context for the 
        #   design. It is envisaged that design loading routines may use this
        #   to evaluate compatibility before attemping to load a design.
        #
        #   The identification string is dumped as an ``*ECHO?``` query to be
        #   a valid, albeit transparent, commad.
        #
        idn = self.query_("*IDN?")
        echo = f"*ECHO {idn}?"
        output += self._dump_value(echo)

        # Reset changes
        #
        #   ``*CHANGES?`` queries only return the changes since last
        #   ``*CHANGES?`` query on the connection, _or_ all values for the first
        #   query on the connection. To ensure full design is dumped, must
        #   reset the changes state so as to effectly be first ``*CHANGES?``
        #   query.
        #
        self.assign("*CHANGES","S")

        # Dump field attributes
        attrs = self.query_("*CHANGES.ATTR?")
        for attr in attrs:
            output += self._dump_value(attr)

        # Dump field values
        fields = self.query_("*CHANGES.CONFIG?")
        for field in fields:
            output += self._dump_value(field)

        # Dump table field values (base64 encoded)
        #
        #   N.b. ``*CHANGES.TABLE?`` only returns table fields which have
        #   changed. Table values must be retrieved separately.
        #
        tables = self.query_("*CHANGES.TABLE?")
        for table in tables:
            output += self._dump_table(table.rstrip("<"))

        # Dump metadata
        #
        #   N.b. Both single value and table fields are returned
        #   N.b.b. Metadata table values are always ASCII encoded
        #
        metadata = self.query_("*CHANGES.METADATA?")
        for metadatum in metadata:
            if metadatum.endswith("<"):
                output += self._dump_table(
                    metadatum.rstrip("<"),
                    encoding="ascii"  
                )
            else:
                output += self._dump_value(metadatum)

        # Write output
        file.write(output)

    def _assert_firmware_versions(self, fw1: dict, fw2: dict) -> typing.NoReturn:
        """Assert firmware compatibility
        
        :param dict fw*: Firmware versions as dict of strings
        :rtype: None
        :raises: ValueError on mismatch of required versions
        
        """
        exceptions = (
            "fpga_major",
            "fpga_minor",
            "fpga_patch",
            "fpga_build",
            "fpga_supporting"
        )
        warnings_ = (
            "server_major",
            "server_minor",
            "server_patch",
            "rootfs"
        )
        for key in fw1:
            if (fw1[key] != fw2[key]):
                if key in exceptions:
                    raise ValueError(
                        "Incompatible firmware versions"
                        f" ({key}: {fw1[key]} != {fw2[key]})"
                    )
                elif key in warnings_:
                    warnings.warn(
                        Warning(
                            "Firmware versions differ"
                            f" ({key}: {fw1[key]} != {fw2[key]})"
                        )
                    )

    def _parse_firmware_versions(self, idn: str) -> dict:
        """Parse firmware versions from system identification string
        
        :param str idn: Identification string
        :return: Firmware version numbers
        :rtype: dict
        
        """
        pattern = (
            r"PandA SW: (?P<server_major>\d+)\.(?P<server_minor>\d+)\.(?P<server_patch>\d+) "
            r"FPGA: (?P<fpga_major>\d+)\.(?P<fpga_minor>\d+)\.(?P<fpga_patch>\w+)"
            r" (?P<fpga_build>\w{8}) (?P<fpga_supporting>\w{8}) "
            r"rootfs: (?P<rootfs>[^?=<\n]*)"
        )
        return re.search(pattern, idn).groupdict()

    def _command_is_query(self, cmd: str) -> bool:
        """Test for query command"""
        return self._operator_query in cmd

    def _command_is_assign(self, cmd: str) -> bool:
        """Test for assignment command"""
        return self._operator_assign in cmd

    def _command_is_assign_table(self, cmd: str) -> bool:
        """Test for table assignment command"""
        return self._operator_assign_table[0] in cmd

    def _parse_query(self, cmd: str) -> str:
        """Parse target from query command"""
        return cmd.split(self._operator_query)[0]

    def _parse_assign(self, cmd: str) -> typing.Tuple[str, str]:
        """Parse target and value from assignment command"""
        return cmd.split(self._operator_assign)

    def _parse_assign_table(self, cmd: str) -> typing.Tuple[str, list, str]:
        """Parse target, operator and values from table assignment command"""
        lines = cmd.splitlines()
        target, op0, op1 = lines[0].partition(self._operator_assign_table[0])
        operator = op0 + op1
        values = lines[1:-1]          # 1 is target & op, -1 is blank terminator
        return (target, values, operator)

    def load_design(self, file: typing.TextIO, force: bool=False) -> typing.NoReturn:
        """Load design from file

        Load the design in the readable text file ``file``. The contents of the
        file should be the assignment commands required to implement the design.
        It is recommended that the contents be generated using
        :py:meth:`PandA.dump_design`.

        Designs are defined within the context of a specific firmware version;
        i.e. they depend on the blocks exposed by the PandABlocks-FPGA app.
        Designs cannot therefore be guaraneteed to load correctly on PandABox
        units running different firmware versions as different blocks may be
        exposed.

        To mitigate this, :py:meth:`PandA.load_design` attempts to validate the
        firmware version of the design described in ``file`` against the
        firmware version deployed on the PandABox. The firmware version required
        by the design is defined by an identification string (in the same format
        as returned by the ``*IDN?`` query) contained in the first line of
        ``file``. The firmware version deployed on the PandABox is queried with
        an ``*IDN?`` query.
        
        A ``ValueError`` is raised and loading is aborted if any of the
        following firmware versions differ:

        * FPGA major version
        * FPGA minor version
        * FPGA patch version
        * FPGA build version
        * FPGA supporting version

        Warnings are instead issued if any of the following firmware versions
        differ:

        * Software major version
        * Software minor version
        * Software patch version
        * Root filesystem description

        As these firmware packages do not directly affect the blocks exposed,
        design loading will still be attempted.

        Firmware validation can be disabled using the ``force=True`` keyword
        argument. Do not be surprised however if the design fails to load
        successfully…
        
        :param TextIO file: Design file
        :param bool force: Disable firmware validation
        :rtype: None

        """

        # Assert firmware versions
        if not force:
            fw_design = self._parse_firmware_versions(file.readline())
            fw_panda = self._parse_firmware_versions(self.query_("*IDN?"))
            self._assert_firmware_versions(fw_design, fw_panda)

        # Load design
        #
        #   Whilst in principle could send commands in design file directly over
        #   socket, this bypasses the comms methods (``query_``, ``assign``,
        #   ``assign_table```) and their response validations, thereby
        #   effectively opening a second comms channel to potentially debug.
        #
        #   Instead, probably better practice to parse design file and use the
        #   existing comms methods.
        #
        file.seek(0)                            # Send firmware echo for logging
        for line in file:
            if self._command_is_query(line):
                target = self._parse_query(line.rstrip())
                self.query_(target)
            elif self._command_is_assign(line):
                target, value = self._parse_assign(line.rstrip())
                self.assign(target, value)
            elif self._command_is_assign_table(line):
                lines = line
                while line.rstrip():
                    line = next(file)
                    lines += line
                target, values, operator = self._parse_assign_table(lines)
                self.assign_table(target, values, operator)
            else:
                raise ValueError(f"Unknown command type ('{line}')")

    # Legacy interface

    def connect_to_panda(self):
        return self.connect()

    def disconnect_from_panda(self):
        return self.disconnect()

    def query(self, cmd):
        """Send command to host and return response"""
        self._sock.sendall((cmd + '\n').encode())
        val = str(self._sock.recv(4096).decode())
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
        logger.debug("numquery %s returned %s" % (cmd, str(val).strip()))
        return val

    def save_config(self, path):
        """Save design to file"""
        if self._sock is not None:
            self.disconnect_from_panda()
        self.connect_to_panda()              # Ensure first `*CHANGES` request on connection
        _Design(self._sock).save(path)

    def load_config(self, path):
        """Load design from file"""
        _Design(self._sock).load(path)

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
