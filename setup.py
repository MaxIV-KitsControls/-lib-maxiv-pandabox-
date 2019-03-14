#!/usr/bin/env python
from setuptools import setup

 
setup(name = "python-pandaboxlib",
      version = "0.0.2",
      description = ("Library for communication with PandABox." 
                     "This communication is based in TCP/IP sockets."),
      author = "Jens Sundberg/Juliano Murari",
      author_email = "kitscontrols@maxiv.lu.se",
      license = "GPLv3",
      url = "http://www.maxlab.lu.se",
      packages =['pandaboxlib'],
      package_dir = {'':'src'},
     )
