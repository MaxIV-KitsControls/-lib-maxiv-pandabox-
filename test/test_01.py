from mock import patch, Mock
import unittest
from mock import MagicMock
import pandaboxlib.pandaboxlib



# substituting original query(cmd) in order to avoid network com.

def my_query(cmd):
    if cmd == '*PCAP.STATUS?':
        return '1.23'
    if cmd == 'TEMP?':
        return ''  # to test invalid response

    return None


class Test_01(unittest.TestCase):

    def test_connect(self):
        mocksock = MagicMock(name='socket')
        pandaboxlib.socket.socket = MagicMock(return_value=mocksock)
        panda = pandaboxlib.PandA('localhost')
        panda.connect_to_panda()

        panda.disconnect_from_panda()

        panda.sock.connect.assert_called_with(('localhost', 8888))
        panda.sock.shutdown.assert_called()
        panda.sock.close.assert_called()

    def test_query(self):
        panda = pandaboxlib.PandA('localhost')
        panda.query = MagicMock(side_effect=my_query)
        panda.query('CLOCKS.B_PERIOD=0.001')

    def test_numquery(self):
        panda = pandaboxlib.PandA('localhost')
        panda.query = MagicMock(side_effect=my_query)
        value = panda.numquery('*PCAP.STATUS?')
        assert value == 1.23

    # Some examples from Henrik https://gitlab.maxiv.lu.se/kits-maxiv/lib-maxiv-lakeshore335gpiblan
    # def test_get_range_1(self):
    #     panda = ls335.LakeShore335Connection('localhost', 1234, 1)
    #     panda.query = MagicMock(side_effect=my_query)
    #     heatrange = panda.get_heater_range(1)
    #     self.assertEqual(1, heatrange, "heater range 1")

    # def test_get_range_2(self):
    #     panda = ls335.LakeShore335Connection('localhost', 1234, 1)
    #     panda.query = MagicMock(side_effect=my_query)
    #     heatrange = panda.get_heater_range(2)
    #     self.assertEqual(2, heatrange, "heater range 2")

    # def test_set_range(self):
    #     panda = ls335.LakeShore335Connection('localhost', 1234, 1)
    #     panda.sock=MagicMock()
    #     panda.set_heater_range(2, 1)
    #     panda.sock.send.assert_called_with('RANGE 2,1\r\n')

    # def test_set_setpoint(self):
    #     panda = ls335.LakeShore335Connection('localhost', 1234, 1)
    #     panda.sock = MagicMock()
    #     panda.set_setpoint(2, 123.4567)
    #     panda.sock.send.assert_called_with('SETP 2,+123.457\r\n')

    # def test_invalid_response(self):
    #     panda = ls335.LakeShore335Connection('localhost', 1234, 1)
    #     panda.query = MagicMock(side_effect=my_query)
    #     with self.assertRaises(ls335.InvalidResponseError):
    #         panda.get_temperature()




if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(LS335libTestCase)
    unittest.TextTestRunner(verbosity=3).run(suite)
    # unittest.main()
