# Put main module on path from `tests` directory
import os
import sys
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..'
        )
    )
)

# Start imports proper
import pandaboxlib
import unittest
import unittest.mock
import mocksocket
import filecmp
import os


class MockSocketFactory:
    """Mock socket factory class"""

    responses = None

    def __init__(self, responses=None):
        """Factory instance initalization
        
        Initialize factory instance with attributes for subsequent 
        MockSocket instance production.
        
        """
        self.responses = responses

    def __call__(self, responses=None):
        """Produce MockSocket instances"""
        if responses is None:
            responses = self.responses
        return mocksocket.MockSocket(responses=responses)


class PandAFactory:
    """pandaboxlib.PandA factory class"""

    host = None
    port = None

    def __init__(self, host="localhost", port=8888, mock=True):
        """Factory instance initalization
        
        Initialize factory instance with attributes for subsequent 
        pandaboxlib.PandA instance production.
        
        """
        self.host = host
        self.port = port

    def __call__(self, host=None, port=None, mock=None):
        """Produce pandaboxlib.PandA instances"""
        if host is None:
            host = self.host
        if port is None:
            port = self.port
        return pandaboxlib.PandA(host=host, port=port)


mock_socket_responses = {
    None: b"ERR Unknown command\n",
    b"*IDN?\n": b"OK =PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server\n",
    b"*BLOCKS?\n": (
        b"!TTLIN 6\n"
        b"!SFP 1\n"
        b"!OUTENC 4\n"
        b"!PCAP 1\n"
        b"!PCOMP 4\n"
        b"!SFP_TX 1\n"
        b"!TTLOUT 10\n"
        b"!ADC 8\n"
        b"!DIV 4\n"
        b"!INENC 4\n"
        b"!SLOW 1\n"
        b"!PGEN 2\n"
        b"!SFP_RX 1\n"
        b"!LVDSIN 2\n"
        b"!POSENC 4\n"
        b"!SEQ 4\n"
        b"!PULSE 4\n"
        b"!SRGATE 4\n"
        b"!FMC 1\n"
        b"!LUT 8\n"
        b"!LVDSOUT 2\n"
        b"!COUNTER 8\n"
        b"!ADDER 2\n"
        b"!CLOCKS 1\n"
        b"!SYSTEM 1\n"
        b"!BITS 1\n"
        b"!QDEC 4\n"
        b".\n"
    ),
    b"*CHANGES.ATTR?\n": (
        b"!QDEC1.B.DELAY=0\n"
        b"!QDEC2.B.DELAY=0\n"
        b"!QDEC3.B.DELAY=0\n"
        b"!QDEC4.B.DELAY=0\n"
        b".\n"
    ),
    b"*CHANGES.CONFIG?\n": (
        b"!QDEC1.B=ZERO\n"
        b"!QDEC2.B=ZERO\n"
        b"!QDEC3.B=ZERO\n"
        b"!QDEC4.B=ZERO\n"
        b".\n"
    ),
    b"*CHANGES.TABLE?\n": (
        b"!PCOMP4.TABLE<\n"
        b"!PGEN1.TABLE<\n"
        b".\n"
    ),
    b"PCOMP4.TABLE.B?\n": (
        b".\n"
    ),
    b"PGEN1.TABLE.B?\n": (
        b"!AQAAAAIAAAADAAAA\n"
        b".\n"
    ),
    b"*CHANGES.METADATA?\n": (
        b"!*METADATA.YAML<\n"
        b"!*METADATA.LABEL_BLAH1=\n"
        b".\n"
    ),
    b"*METADATA.YAML?\n": (
        b".\n"
    ),
    b"ADC.*?\n": (
        b"!OUT 0 pos_out\n"
        b".\n"
    ),
    b"TTLIN1.TERM=50-Ohm\n": b"OK\n",
    b"TTLIN1.TERM=100-Ohm\n": b"ERR Invalid enumeration value\n",
    b"PGEN1.TABLE<\n1\n2\n3\n\n": b"OK\n",
    b"PGEN1.TABLE<<\n1\n2\n3\n\n": b"OK\n",
    b"PGEN1.TABLE<B\nAQAAAAIAAAADAAAA\nAQAAAAIAAAADAAAA\n\n": b"OK\n",
    b"PGEN1.TABLE<<B\nAQAAAAIAAAADAAAA\nAQAAAAIAAAADAAAA\n\n": b"OK\n",
    b"PGEN1.TABLE<\nfoo\nbar\nbaz\n\n": b"ERR Number missing\n",
    b"PULSE1.QUEUE?\n": b"OK =3\n",
    b"PULSE1.DELAY?\n": b"OK =2.5\n",
    b"PULSE1.DELAY.UNITS?\n": b"OK =s\n",
    b"PULSE1.DELAY=3.5\n": b"OK\n",
    b"FOO.*?\n": b"ERR No such block\n"
}
mock_socket_factory = MockSocketFactory(responses=mock_socket_responses)


@unittest.mock.patch(
    "pandaboxlib.socket.socket",
    new_callable=mock_socket_factory
)
class TestPandA(unittest.TestCase):
    """Tests for public interface provided by pandaboxlib.PandA class"""

    @classmethod
    def setUpClass(cls):
        cls.panda_factory = PandAFactory()

    def test_init_assign_host(self, mocksock):
        """Host assignment at initialization"""
        host = self.panda_factory.host
        panda = pandaboxlib.PandA(host)
        self.assertEqual(panda.host, host)

    def test_init_assign_port(self, mocksock):
        """Port assignment at initialization"""
        host = self.panda_factory.host
        port = 8080
        assert port != pandaboxlib.PandA(host).port         # Not default port
        panda = pandaboxlib.PandA(host, port=port)
        self.assertEqual(panda.port, port)

    def test_init_default_port(self, mocksock):
        """Default port assignment at initialization"""
        host = self.panda_factory.host
        panda = pandaboxlib.PandA(host)
        self.assertIsInstance(panda.port, int)

    def test_connect(self, mocksock):
        """Connection succeeds"""
        panda = self.panda_factory()
        panda.connect()
        mocksock.connect.assert_called()

    def test_disconnect(self, mocksock):
        """Disconnection succeeds"""
        panda = self.panda_factory()
        panda.connect()
        panda.disconnect()
        mocksock.close.assert_called()

    def test_query_returns(self, mocksock):
        """Query returns expected values"""
        panda = self.panda_factory()
        panda.connect()
        returns = {

            # Single value return
            #
            #   * Returned as string
            #   * Stripped of "OK =" prefix
            #   * Stripped of "\n" suffix
            #   * "?" suffix appended if necessary
            #
            "*IDN?": "PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server",
            "*IDN": "PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server",

            # Multiple value return
            #
            #   * Returned as iterable of strings
            #   * Stripped of "!" prefix
            #   * Stripped of "\n" suffix
            #   * Stripped of "." suffix
            #   * Zero-length responses return empty iterable
            #   * "?" suffix appended if necessary
            #
            "*CHANGES.ATTR?": [
                "QDEC1.B.DELAY=0",
                "QDEC2.B.DELAY=0",
                "QDEC3.B.DELAY=0",
                "QDEC4.B.DELAY=0"
            ],
            "*CHANGES.ATTR": [
                "QDEC1.B.DELAY=0",
                "QDEC2.B.DELAY=0",
                "QDEC3.B.DELAY=0",
                "QDEC4.B.DELAY=0"
            ],
            "PCOMP4.TABLE.B?": []

        }
        for cmd, return_ in returns.items():
            with self.subTest(cmd=cmd):
                returned = panda.query_(cmd)
                self.assertEqual(returned, return_)

    def test_query_exceptions(self, mocksock):
        """Query raises expected exceptions"""
        panda = self.panda_factory()
        panda.connect()
        exceptions = {

            # Bad query
            "FOO.*?": RuntimeError,

            # Assignment attempt
            "TTLIN1.TERM=50-Ohm": RuntimeError,

            # Table assignment attempt
            "PGEN1.TABLE<\n1\n2\n3\n\n": RuntimeError

        }
        for cmd, exception in exceptions.items():
            with self.subTest(cmd=cmd):
                with self.assertRaises(exception):
                    panda.query_(cmd)

    def test_assign_returns(self, mocksock):
        """Assignment returns expected values"""
        panda = self.panda_factory()
        panda.connect()
        returns = {

            # Successful assignment
            #
            #   * Returns None
            #   * "=" operator optional
            #   * Numeric values accepted
            #
            ("TTLIN1.TERM", "50-Ohm"): None,
            ("TTLIN1.TERM", "50-Ohm", "="): None,
            ("PULSE1.DELAY", 3.5): None

        }    
        for args, return_ in returns.items():
            with self.subTest(args=args):
                returned = panda.assign(*args)
                self.assertEqual(returned, return_)

    def test_assign_exceptions(self, mocksock):
        """Assignment raises expected exceptions"""
        panda = self.panda_factory()
        panda.connect()
        exceptions = {

            # Failed assignment
            ("TTLIN1.TERM", "100-Ohm"): RuntimeError,

            # Bad operator
            ("TTLIN1.TERM", "50-Ohm", "+"): ValueError

        }
        for args, exception in exceptions.items():
            with self.subTest(args=args):
                with self.assertRaises(exception):
                    panda.assign(*args)

    def test_assign_table_returns(self, mocksock):
        """Table assignment returns expected values"""
        panda = self.panda_factory()
        panda.connect()
        returns = {

            # Successful assignment
            #
            #   * Returns None
            #   * Defaults to "<" operator
            #   * "<<", "<B", "<<B" operators supported
            #   * Numeric values accepted
            #
            ("PGEN1.TABLE", ("1","2","3")): None,
            ("PGEN1.TABLE", ("1","2","3"), "<"): None,
            ("PGEN1.TABLE", ("1","2","3"), "<<"): None,
            ("PGEN1.TABLE", ("AQAAAAIAAAADAAAA","AQAAAAIAAAADAAAA"), "<B"): None,
            ("PGEN1.TABLE", ("AQAAAAIAAAADAAAA","AQAAAAIAAAADAAAA"), "<<B"): None,
            ("PGEN1.TABLE", (1,2,3)): None,

        }    
        for args, return_ in returns.items():
            with self.subTest(args=args):
                returned = panda.assign_table(*args)
                self.assertEqual(returned, return_)

    def test_assign_table_exceptions(self, mocksock):
        """Table assignment raises expected exceptions"""
        panda = self.panda_factory()
        panda.connect()
        exceptions = {

            # Failed assignment
            ("PGEN1.TABLE",("foo","bar","baz")): RuntimeError,

            # Bad operator
            ("PGEN1.TABLE", ("1","2","3"), "+"): ValueError

        }
        for args, exception in exceptions.items():
            with self.subTest(args=args):
                with self.assertRaises(exception):
                    panda.assign_table(*args)


@unittest.mock.patch(
    "pandaboxlib.socket.socket",
    new_callable=mock_socket_factory
)
class TestPandALegacy(unittest.TestCase):
    """Tests for legacy public interface provided by pandaboxlib.PandA class"""

    @classmethod
    def setUpClass(cls):
        cls.panda_factory = PandAFactory()
        cls.design = (
            "*ECHO PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server?\n"
            "QDEC1.B.DELAY=0\n"
            "QDEC2.B.DELAY=0\n"
            "QDEC3.B.DELAY=0\n"
            "QDEC4.B.DELAY=0\n"
            "QDEC1.B=ZERO\n"
            "QDEC2.B=ZERO\n"
            "QDEC3.B=ZERO\n"
            "QDEC4.B=ZERO\n"
            "PCOMP4.TABLE<B\n"
            "\n"
            "PGEN1.TABLE<B\n"
            "AQAAAAIAAAADAAAA\n"
            "\n"
            "*METADATA.YAML<\n"
            "\n"
            "*METADATA.LABEL_BLAH1=\n"
        )

    def test_connect_to_panda(self, mocksock):
        """Connection succeeds"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        mocksock.connect.assert_called()

    def test_disconnect_from_panda(self, mocksock):
        """Disconnection succeeds"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        panda.disconnect_from_panda()
        mocksock.close.assert_called()

    def test_query_returns(self, mocksock):
        """Query returns expected values"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        returns = {

            # Query -> Single value
            "*IDN?": "OK =PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server\n",

            # Query -> Error
            "FOO.*?": "ERR No such block\n",

            # Query -> Multiple values
            "ADC.*?": (
                "!OUT 0 pos_out\n"
                ".\n"
            ),

            # Assignment -> Success
            "TTLIN1.TERM=50-Ohm": "OK\n",

            # Assignment -> Error
            "TTLIN1.TERM=100-Ohm": "ERR Invalid enumeration value\n",
            
            # Table assignment -> Success
            "PGEN1.TABLE<\n1\n2\n3\n": "OK\n",

            # Table assignment -> Error
            "PGEN1.TABLE<\nfoo\nbar\nbaz\n": "ERR Number missing\n"
        }
        for cmd, return_ in returns.items():
            with self.subTest(cmd=cmd):
                returned = panda.query(cmd)
                self.assertEqual(returned, return_)

    def test_query_value_returns(self, mocksock):
        """Float query returns expected values"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        returns = {
            "PULSE1.QUEUE?": float(3.0),            # Query -> Integer
            "PULSE1.DELAY?": float(2.5)             # Query -> Float
        }
        for cmd, return_ in returns.items():
            with self.subTest(cmd=cmd):
                returned = panda.query_value(cmd)
                self.assertEqual(returned, return_)         # Assert return value
                self.assertIsInstance(returned, float)      # Assert return type

    def test_query_value_exceptions(self, mocksock):
        """Float query raises expected exceptions"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        exceptions = {
            "PULSE1.DELAY.UNITS?": ValueError,      # Query -> Non-numeric
            "FOO.*?": IndexError                    # Query -> Error
        }
        for cmd, exception in exceptions.items():
            with self.subTest(cmd=cmd):
                with self.assertRaises(exception):
                    panda.query_value(cmd)

    def test_numquery_returns(self, mocksock):
        """Numeric (int else float) query returns expected values"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        returns = {
            "PULSE1.QUEUE?": int(3),                # Query -> Integer
            "PULSE1.DELAY?": float(2.5),            # Query -> Float
        }
        for cmd, return_ in returns.items():
            with self.subTest(cmd=cmd):
                returned = panda.numquery(cmd)
                self.assertEqual(returned, return_)     # Assert return value
                self.assertIsInstance(                  # Assert return type
                    returned,
                    return_.__class__
                )

    def test_numquery_exceptions(self, mocksock):
        """Numeric (int else float) query raises expected exceptions"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        exceptions = {
            "PULSE1.DELAY.UNITS?": ValueError,      # Query -> Non-numeric
            "FOO.*?": ValueError                    # Query -> Error
        }
        for cmd, exception in exceptions.items():
            with self.subTest(cmd=cmd):
                with self.assertRaises(exception):
                    panda.numquery(cmd)             # Assert exception

    def test_save_config(self, mocksock):
        """Save design produces expected output"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        path = "test_save_config"
        path_design = f"{path}.design.txt"
        path_output = f"{path}.output.txt"
        with open(path_design,"wt") as file:
            file.write(self.design)
        panda.save_config(path_output)
        self.assertTrue(filecmp.cmp(path_output, path_design))
        os.remove(path_design)
        os.remove(path_output)

    def test_load_config(self, mocksock):
        """Load design succeeds"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        path = "test_load_design.txt"
        with open(path,"wt") as file:
            file.write(self.design)
        panda.load_config(path)
        #
        # Ideally, would check pandabox state here to assert design load,
        # but this would require more stateful mock socket.
        #
        # Instead assert the data sent over mock socket. Must check all
        # possible socket send methods to cover all possible implementations.
        #
        calls = mocksock.method_calls
        send_calls = filter(lambda call: "send" in call[0], calls)
        send_bytes = b"".join(
            [ call[1][0] for call in send_calls ]       # Call first arguments
        )
        self.assertIn(self.design.encode(), send_bytes)
        os.remove(path)

    def test_send_seq_table_assignment(self, mocksock):
        """Sequencer table assignment succeeds"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        default_args = {
            "block_id": 1,
            "repeats": 1,
            "trigger": "Immediate",
            "positions": (0,1,2),
            "time1": 1,
            "phase1": {
                "a": True,
                "b": False,
                "c": False,
                "d": False,
                "e": False,
                "f": False
             },
            "time2": 2,
            "phase2": {
                "a": False,
                "b": False,
                "c": False,
                "d": False,
                "e": False,
                "f": False
             },
        }
        cmds = {
            ("block_id", 1): (
                b"SEQ1.TABLE<\n"
                b"1048577 0 1 2\n"
                b"1048577 1 1 2\n"
                b"1048577 2 1 2\n"
                b"\n"
            ),                          # Success
            ("block_id", 0): (
                b"SEQ0.TABLE<\n"
                b"1048577 0 1 2\n"
                b"1048577 1 1 2\n"
                b"1048577 2 1 2\n"
                b"\n"
            ),                          # Error
            ("positions", tuple()): (
                b"SEQ1.TABLE<\n"
                b"\n"
            )                           # Success (no positions)
        }
        for (key, value), cmd in cmds.items():
            with self.subTest(key=key, value=value):
                args = default_args.copy()
                args[key] = value
                panda.send_seq_table(*tuple(args.values()))
                #
                # Ideally, would check sequencer block state here to assert 
                # assignment, but this would require more stateful mock socket.
                #
                # Alternative would be to check response over mock socket, but
                # this is read and discarded by ``pandaboxlib.PandA``` instance.
                #
                # As such only possible test is to assert the data sent over
                # over mock socket. Must check all possible socket send methods
                # to cover all possible implementations.
                #
                calls = mocksock.method_calls
                send_calls = filter(lambda call: "send" in call[0], calls)
                send_bytes = filter(
                    lambda call: call[1][0] == cmd,    # Call first argument
                    send_calls
                )
                self.assertGreater(
                    len(list(send_bytes)),
                    0
                )                   # At least one send call with matching bytes

    def test_send_seq_table_exceptions(self, mocksock):
        """Sequencer table assignment raises expected exceptions"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        default_args = {
            "block_id": 1,
            "repeats": 1,
            "trigger": "Immediate",
            "positions": (0,1,2),
            "time1": 1,
            "phase1": {
                "a": True,
                "b": False,
                "c": False,
                "d": False,
                "e": False,
                "f": False
             },
            "time2": 2,
            "phase2": {
                "a": False,
                "b": False,
                "c": False,
                "d": False,
                "e": False,
                "f": False
             },
        }
        exceptions = {
            ("repeats", -1): ValueError,                # Invalid repeats
            ("trigger", "foobar"): KeyError,            # Invalid trigger
            ("positions", 3): TypeError,                # Invalid positions
            ("time1", "foobar"): TypeError,             # Invalid time
            ("phase1", 0): AttributeError,              # Invalid phase
            ("phase1", "foobar"): AttributeError,       # Invalid phase
            ("phase1", (0,1,2)): AttributeError         # Invalid phase
        }
        for (key, value), exception in exceptions.items():
            with self.subTest(key=key, value=value):
                with self.assertRaises(exception):
                    args = default_args.copy()
                    args[key] = value
                    panda.send_seq_table(*tuple(args.values()))

    def test_get_number_channels_returns(self, mocksock):
        """Enabled capture channel query returns expected values"""
        panda = self.panda_factory()
        panda.connect_to_panda()
        returns = {
            b"!PGEN1.OUT\n!PGEN2.OUT\n.\n": 2,
            b".\n": 0
        }
        assert b"*CAPTURE?\n" not in mocksock._responses    # No response clobber
        for response, return_ in returns.items():
            with self.subTest(response=response):
                mocksock._responses[b"*CAPTURE?\n"] = response
                returned = panda.get_number_channels()
                self.assertEqual(returned, return_)
        del mocksock._responses[b"*CAPTURE?\n"]             # Reset responses


if __name__ == "__main__":
    unittest.main(verbosity=1, buffer=True)