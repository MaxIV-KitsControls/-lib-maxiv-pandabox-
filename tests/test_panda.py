import pandaboxlib
import unittest
import unittest.mock
import mocksocket
import socket
import filecmp
import os
import io
import re


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
    b"QDEC1.B.DELAY=0\n": b"OK\n",
    b"QDEC2.B.DELAY=0\n": b"OK\n",
    b"QDEC3.B.DELAY=0\n": b"OK\n",
    b"QDEC4.B.DELAY=0\n": b"OK\n",
    b"*CHANGES.CONFIG?\n": (
        b"!QDEC1.B=ZERO\n"
        b"!QDEC2.B=ZERO\n"
        b"!QDEC3.B=ZERO\n"
        b"!QDEC4.B=ZERO\n"
        b".\n"
    ),
    b"QDEC1.B=ZERO\n": b"OK\n",
    b"QDEC2.B=ZERO\n": b"OK\n",
    b"QDEC3.B=ZERO\n": b"OK\n",
    b"QDEC4.B=ZERO\n": b"OK\n",
    b"*CHANGES.TABLE?\n": (
        b"!PCOMP4.TABLE<\n"
        b"!PGEN1.TABLE<\n"
        b".\n"
    ),
    b"PCOMP4.TABLE.B?\n": (
        b".\n"
    ),
    b"PCOMP4.TABLE<B\n\n": b"OK\n",
    b"PGEN1.TABLE.B?\n": (
        b"!AQAAAAIAAAADAAAA\n"
        b".\n"
    ),
    b"PGEN1.TABLE<B\nAQAAAAIAAAADAAAA\n\n": b"OK\n",
    b"*CHANGES.METADATA?\n": (
        b"!*METADATA.YAML<\n"
        b"!*METADATA.LABEL_BLAH1=\n"
        b".\n"
    ),
    b"*METADATA.YAML?\n": (
        b".\n"
    ),
    b"*METADATA.YAML<\n\n": b"OK\n",
    b"*METADATA.LABEL_BLAH1=\n": b"OK\n",
    b"*CHANGES=S\n": b"OK\n",
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
    b"INENC1.VAL.UNITS=\n": b"OK\n",
    (
        b"*ECHO"
        b" PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server?\n"
    ): (
        b"OK ="
        b" PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server\n"
    ),
    (
        b"*ECHO"
        b" PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000001 rootfs: Test Server?\n"
    ): (
        b"OK ="
        b" PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000001 rootfs: Test Server\n"
    ),
    (
        b"*ECHO"
        b" PandA SW: 2.0.2 FPGA: 0.0.0 00000001 00000000 rootfs: Test Server?\n"
    ): (
        b"OK ="
        b" PandA SW: 2.0.2 FPGA: 0.0.0 00000001 00000000 rootfs: Test Server\n"
    ),
    (
        b"*ECHO"
        b" PandA SW: 2.0.2 FPGA: 0.0.1 00000000 00000000 rootfs: Test Server?\n"
    ): (
        b"OK ="
        b" PandA SW: 2.0.2 FPGA: 0.0.1 00000000 00000000 rootfs: Test Server\n"
    ),
    (
        b"*ECHO"
        b" PandA SW: 2.0.2 FPGA: 0.1.0 00000000 00000000 rootfs: Test Server?\n"
    ): (
        b"OK ="
        b" PandA SW: 2.0.2 FPGA: 0.1.0 00000000 00000000 rootfs: Test Server\n"
    ),
    (
        b"*ECHO"
        b" PandA SW: 2.0.2 FPGA: 1.0.0 00000000 00000000 rootfs: Test Server?\n"
    ): (
        b"OK ="
        b" PandA SW: 2.0.2 FPGA: 1.0.0 00000000 00000000 rootfs: Test Server\n"
    ),
    (
        b"*ECHO"
        b" PandA SW: 2.0.3 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server?\n"
    ): (
        b"OK ="
        b" PandA SW: 2.0.3 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server\n"
    ),
    (
        b"*ECHO"
        b" PandA SW: 2.1.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server?\n"
    ): (
        b"OK ="
        b" PandA SW: 2.1.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server\n"
    ),
    (
        b"*ECHO"
        b" PandA SW: 3.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server?\n"
    ): (
        b"OK ="
        b" PandA SW: 3.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server\n"
    ),
    (
        b"*ECHO"
        b" PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Foo Server?\n"
    ): (
        b"OK ="
        b" PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Foo Server\n"
    ),
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

            # Returns None
            ("TTLIN1.TERM", "50-Ohm", "="): None,

            # Optional operator
            ("TTLIN1.TERM", "50-Ohm"): None,

            # Numeric value
            ("PULSE1.DELAY", 3.5, "="): None,

            # Empty value
            ("INENC1.VAL.UNITS", "", "="): None

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

            # Returns None
            ("PGEN1.TABLE", ("1","2","3"), "<"): None,

            # Defaults to "<" operator
            ("PGEN1.TABLE", ("1","2","3")): None,

            # Append operator
            ("PGEN1.TABLE", ("1","2","3"), "<<"): None,

            # Base64 operator
            ("PGEN1.TABLE", ("AQAAAAIAAAADAAAA","AQAAAAIAAAADAAAA"), "<B"): None,

            # Append base64 operator
            ("PGEN1.TABLE", ("AQAAAAIAAAADAAAA","AQAAAAIAAAADAAAA"), "<<B"): None,

            # Numeric values
            ("PGEN1.TABLE", (1,2,3)): None,

            # Empty values
            ("PCOMP4.TABLE", (), "<B"): None

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

    def test_dump_design_output(self, mocksock):
        """Dump design produces expected output"""
        panda = self.panda_factory()
        panda.connect()
        with io.StringIO() as file:
            panda.dump_design(file)
            self.assertEqual(
                file.getvalue(),
                self.design
            )

    def test_dump_design_reproducibility(self, mocksock):
        """Dump design produces reproducible output"""
        panda = self.panda_factory()
        panda.connect()
        dumps = ["", ""]
        for i_dump in range(len(dumps)):
            mocksock.reset_mock()
            with self.subTest(i_dump=i_dump):
                with io.StringIO() as file:
                    panda.dump_design(file)
                    dumps[i_dump] = file.getvalue()
                    # 
                    # Dumping the PandABox design typically involves sending 
                    # ``*CHANGES`` queries. Repeated ``*CHANGES`` queries will 
                    # however likely not produce the same response. As such, 
                    # dump implementations relying on ``*CHANGES`` queries risk
                    # producing incomplete dumps.
                    # 
                    # In order to ensure a full design dump, should test that 
                    # repeated dumps produce the same response. This is however 
                    # difficult to mock due to the stateless nature of the mock 
                    # socket.
                    # 
                    # As such, only option for testing is to detect ``*CHANGES``
                    # queries sent over the socket, and assert subsequent 
                    # resetting commands (e.g. ``*CHANGES=S`` or reconnect).
                    #
                    calls = mocksock.method_calls
                    sent = [call[1][0] for call in calls if "send" in call[0]]
                    sent = (b"".join(sent)).decode()
                    changes_query_sent = re.search(r"\*CHANGES[^=\?]*\?", sent)
                    if changes_query_sent:
                        changes_reset = re.search(r"\*CHANGES[^=\?]*=S", sent)
                        connection_calls = [
                            call[0] for call in calls
                            if ("connect" in call[0])
                            or ("close" in call[0])
                        ]
                        reconnected = (
                            ("close" in connection_calls) and 
                            ("connect" in connection_calls) and 
                            bool(
                                connection_calls.index(
                                    "connect",
                                    connection_calls.index("close")
                                )
                            )
                        )
                        self.assertTrue(changes_reset or reconnected)
        self.assertEqual(*dumps)     # Meaningless due to stateless mock socket

    def test_load_design(self, mocksock):
        """Load design succeeds"""
        panda = self.panda_factory()
        panda.connect()
        with io.StringIO(self.design) as file:
            panda.load_design(file)
        #
        # Ideally, would check PandABox state here to assert design load,
        # but this would require stateful mock socket.
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

    def test_load_design_fw_validation_exceptions(self, mocksock):
        """Load design firmware validation raises expected exceptions"""
        panda = self.panda_factory()
        panda.connect()
        exceptions = {
            (
                "FPGA: 0.0.0 00000000 00000000",
                "FPGA: 0.0.0 00000000 00000001"
            ): ValueError,                      # Different FPGA support version
            (
                "FPGA: 0.0.0 00000000 00000000",
                "FPGA: 0.0.0 00000001 00000000"
            ): ValueError,                      # Different FPGA build version
            (
                "FPGA: 0.0.0 00000000 00000000",
                "FPGA: 0.0.1 00000000 00000000"
            ): ValueError,                      # Different FPGA patch version
            (
                "FPGA: 0.0.0 00000000 00000000",
                "FPGA: 0.1.0 00000000 00000000"
            ): ValueError,                      # Different FPGA minor version
            (
                "FPGA: 0.0.0 00000000 00000000",
                "FPGA: 1.0.0 00000000 00000000"
            ): ValueError                      # Different FPGA major version
        }
        for (old, new), exception in exceptions.items():
            with self.subTest(new=new):
                with io.StringIO(self.design.replace(old,new)) as file:
                    with self.assertRaises(exception):
                        panda.load_design(file)
                    #
                    # Can envisage situation in which wish to force design
                    # load attempt despite mismatched firmware versions.
                    #
                    # No guarantee that forced design load will succeed, so
                    # simply assert the data sent over mock socket. Must check 
                    # all possible socket send methods to cover all possible
                    # implementations.
                    #
                    mocksock.reset_mock()
                    panda.load_design(file, force=True)
                    calls = mocksock.method_calls
                    send_calls = filter(lambda call: "send" in call[0], calls)
                    send_bytes = b"".join(
                        [ call[1][0] for call in send_calls ]       # First args
                    )
                    self.assertIn(file.getvalue().encode(), send_bytes)

    def test_load_design_fw_validation_warnings(self, mocksock):
        """Load design firmware validation raises expected warnings"""
        panda = self.panda_factory()
        panda.connect()
        warnings = {
            (
                "SW: 2.0.2",
                "SW: 2.0.3"
            ): Warning,                     # Different server patch version
            (
                "SW: 2.0.2",
                "SW: 2.1.2"
            ): Warning,                     # Different server minor version
            (
                "SW: 2.0.2",
                "SW: 3.0.2"
            ): Warning,                     # Different server major version
            (
                "rootfs: Test Server",
                "rootfs: Foo Server"
            ): Warning                      # Different rootfs version
        }
        for (old, new), warning in warnings.items():
            with self.subTest(new=new):
                with io.StringIO(self.design.replace(old,new)) as file:
                    with self.assertWarns(warning):
                        panda.load_design(file)

    def test_remote_disconnect_exceptions(self, mocksock):
        """Remote disconnection raises expected exceptions"""
        panda = self.panda_factory()
        calls = {
            panda.query_: ("*IDN?",),
            panda.assign: ("TTLIN1.TERM", "50-Ohm"),
            panda.assign_table: ("PGEN1.TABLE", ("AQAAAAIAAAADAAAA",) , "<B")
        }
        for call, args in calls.items():
            with self.subTest(call=str(call),args=args):
                panda.connect()
                mocksock._connected_remote = False  # Mock remote disconnection
                with self.assertRaises(BrokenPipeError):
                    call(*args)
                mocksock.close.assert_called()      # Assert system resources released
                mocksock.reset_mock()

    def test_local_disconnect_exceptions(self, mocksock):
        """Local disconnection raises expected exceptions"""
        panda = self.panda_factory()
        calls = {
            panda.query_: ("*IDN?",),
            panda.assign: ("TTLIN1.TERM", "50-Ohm"),
            panda.assign_table: ("PGEN1.TABLE", ("AQAAAAIAAAADAAAA",) , "<B")
        }
        for call, args in calls.items():
            with self.subTest(call=str(call),args=args):
                panda.connect()
                panda.disconnect()
                with self.assertRaises((AttributeError, BrokenPipeError, OSError)):
                    call(*args)

    def test_network_exceptions(self, mocksock):
        """Network interrupt raises expected exceptions"""
        panda = self.panda_factory()
        panda.connect()
        mocksock._network = False
        calls = {
            panda.query_: ("*IDN?",),
            panda.assign: ("TTLIN1.TERM", "50-Ohm"),
            panda.assign_table: ("PGEN1.TABLE", ("AQAAAAIAAAADAAAA",) , "<B")
        }
        for call, args in calls.items():
            with self.subTest(call=str(call),args=args):
                with self.assertRaises(socket.timeout):
                    call(*args)


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
        # Ideally, would check PandABox state here to assert design load,
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
