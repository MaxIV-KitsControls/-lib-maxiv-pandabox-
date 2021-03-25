#!/usr/bin/env python
from setuptools import setup


setup(name = "pandaboxlib",
      version = "1.0.2",
      description = ("Library for communication with PandABox."
                     "This communication is based in TCP/IP sockets."),
      author = "Jens Sundberg/Juliano Murari",
      author_email = "kitscontrols@maxiv.lu.se",
      license = "GPLv3",
      url = "https://gitlab.maxiv.lu.se/kits-maxiv/lib-maxiv-pandabox",
      packages =['pandaboxlib'],
      package_dir = {'':'src'},
     )
