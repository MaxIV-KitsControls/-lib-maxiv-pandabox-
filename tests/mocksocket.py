import unittest.mock
import socket
import warnings


class MockSocket(unittest.mock.MagicMock):
    """Mock socket class

    General purpose mock socket class for mocking out socket based
    communication (e.g. over TCP/IP).

    """

    _buffer = None
    _connected_local = False
    _connected_remote = False

    _side_effect_methods = (
        "connect",
        "close",
        "send",
        "sendall",
        "recv",
        "shutdown"
    )

    _responses = None
    """Mock socket responses

    Specific responses to data sent over the socket are mocked by the
    looking up the appropriate response in ``MockSocket._responses`` using the 
    data passed to ``MockSocket.send`` as a key. The special key ``None``
    is reserved for defining a response upon lookup failure. The reponses are
    queued in ``MockSocket._buffer`` for subsequent readout by calls to
    ``MockSocket.recv``.

    """


    def __init__(self, responses=None, *args, **kwargs):

        # Fence mock configuration
        #
        #   Configuration of ``unittest.mock.Mock`` subclasses is complicated
        #   by the recursive nature of the parent class — configuration of
        #   methods instantiates new mocks, causing recursive calls to
        #   ``__init__``. As such, configuration must be fenced to only
        #   top-level calls by checking for the ``parent`` keyword argument.
        #
        if ("parent" not in kwargs) or (kwargs["parent"] is None):

            # Mock socket methods
            #
            #   Do not want to override ``MockSocket`` methods (i.e. 
            #   child ``MockSocket`` instances) as wish to maintain their assert
            #   methods. Instead, set child mock instance side-effects to
            #   corresponding private methods of parent ``MockSocket``, e.g.
            #   ``MockSocket().send.side_effect = MockSocket()._send``
            #
            for method in self._side_effect_methods:
                key = f"{method}.side_effect" 
                if key in kwargs:
                    warnings.warn(f"Overriding '{key}' argument")
                kwargs[key] = getattr(self, f"_{method}")


            # Mock constructor call
            #
            #   As socket instances are usually private and created dynamically,
            #   will likely mock out socket *class* rather than *instance* 
            #   during testing (i.e. `socket.socket` rather than the returned 
            #   socket instance). As replacing socket *class* with 
            #   ``MockSocket`` *instance*, must ensure ``MockSocket`` instance
            #   returns itself when called to simulate socket class constructor
            #   call; i.e. ``socket.socket()`` returns ``socket.socket``
            #   instance, ``MockSocket()()`` returns ``MockSocket``` instance.
            #
            key = "return_value"
            if key in kwargs:
                warnings.warn(f"Overriding '{key}' argument")
            kwargs[key] = self

            # Set default name
            kwargs.setdefault("name","MockSocket")

        # Call superclass constructor
        super().__init__(*args, **kwargs)

        # Assign attributes
        if responses is None:
            responses = {None: b""}         # Default responses — do nothing
        self._responses = responses
        self._buffer = bytearray()

    def _connect(self, address):
        """Mock socket connect method"""
        self._connected_local = True
        self._connected_remote = True

    def _close(self):
        """Mock socket close method"""
        self._connected_local = False
        self._connected_remote = False

    def _send(self, bytes_, *args, **kwargs):
        """Mock socket send method"""
        if not (self._connected_local and self._connected_remote):
            raise BrokenPipeError("[Errno 32] Broken pipe")
        if bytes_ in self._responses:
            self._buffer += self._responses[bytes_]
        else:
            self._buffer += self._responses[None]
        return len(bytes_)                                  # All bytes sent

    def _sendall(self, bytes_, *args, **kwargs):
        """Mock socket sendall method"""
        self._send(bytes_, *args, **kwargs)
        return None                                         # All bytes sent

    def _recv(self, bufsize, *args, **kwargs):
        """Mock socket recv method"""
        if not self._connected_local:
            raise OSError("[Errno 107] Transport endpoint is not connected")
        elif not self._connected_remote:
            self._buffer = bytearray()                      # Return zero bytes
        ret = self._buffer
        self._buffer = bytearray()
        return ret

    def _shutdown(self, how):
        """Mock socket shutdown method"""
        if not self._connected_local:
            raise OSError(
                "OSError: [Errno 107] Transport endpoint is not connected"
            )
        self._connected_local = False

