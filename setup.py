#!/usr/bin/env python
from setuptools import setup


setup(name = "pandaboxlib",
      version = "2.0.0",
      description = ("Library for socket-based communication with PandABox."),
      author = "KITS, MAX IV Laboratory",
      author_email = "kitscontrols@maxiv.lu.se",
      license = "GPLv3",
      url = "https://github.com/MaxIV-KitsControls/lib-maxiv-pandaboxlib",
      packages =['pandaboxlib'],
      package_dir = {'':'pandaboxlib'}
     )
