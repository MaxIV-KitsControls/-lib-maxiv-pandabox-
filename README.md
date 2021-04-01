# lib-maxiv-pandaboxlib

A python library for communication with the [PandABox](https://ohwr.org/project/pandabox) platform.

## About

The primary interface to the FPGA block-based functionality of a PandABox is via the [PandABlocks-server](https://pandablocks-server.readthedocs.io/en/latest/index.html) TCP socket server. `lib-maxiv-pandaboxlib` is a synchronous, 'Avec-IO' python client library for this interface. If you are looking for a more modern 'Sans-IO' client library providing  asynchronous functionality, you may be interested in [PandABlock-client](https://pandablocks.github.io/PandABlocks-client/master/index.html) which is designed and maintained by the PandABlock-server developers.

## Installation

Installation is currently only from source. Simply clone the repository and add the package to your python path;

```shell
$ git clone https://github.com/MaxIV-KitsControls/lib-maxiv-pandaboxlib.git
$ PYTHONPATH=lib-maxiv-pandaboxlib python3
```

The library is contained in the main `pandaboxlib` module, which provides the core `PandA` class handling all interactions with PandABox units;

```python
>>> import pandaboxlib
>>> panda = pandaboxlib.PandA("pandabox.maxiv.lu.se", 8888)
>>> panda.query_("*IDN?")
"OK =PandA SW: 2.0.2 FPGA: 0.0.0 00000000 00000000 rootfs: Test Server"
>>> panda.assign("TTLIN1.TERM", "50-Ohm")
>>> panda.assign_table("PGEN1.TABLE", (1,2,3), "<<")
```

## Documentation

_WIP_

## Tests

Units tests are provided in the `tests` directory. To run the tests from the package root;

```shell
$ PYTHONPATH=tests python3 -m unittest --buffer tests/test_*.py
```

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
