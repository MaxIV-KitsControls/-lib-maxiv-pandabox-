Library to communicate with PandABox hardware.

It is a python code that send requests to the TCP server running on the PandABox.


More documents and information on github repository:

https://github.com/PandABlocks/PandABlocks-server

## Tests
to run tests: `PYTHONPATH=src python3 -m pytest`

You will need pytest>6 for this.

## Versioning

The version is in two places.
1. setup.py
2. pandaboxlib/version.py

Some client software, such as a Tango device server, will include pandaboxlib's version as part of its report.

Once installed, you can check the version by:
```
python3 -m pandaboxlib.version --json
```

or
```
python3 -m pandaboxlib.version
```


## Change Log
2022-07-06 1.0.4 enable appending lines to SEQ block
2021-04-01 1.0.3 adds version.py, changes print to logger.debug


## TODO
- Document what must be installed to support the import mock in the test.