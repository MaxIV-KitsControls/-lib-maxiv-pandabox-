#!/usr/bin/env python
from setuptools import setup


setup(name = "pandaboxlib",
      use_scm_version=True,
      setup_requires=["setuptools_scm"],
      description = ("Library for communication with PandABox."
                     "This communication is based in TCP/IP sockets."),
      author = "Jens Sundberg/Juliano Murari",
      author_email = "kitscontrols@maxiv.lu.se",
      license = "LGPLv3",
      url = "https://github.com/MaxIV-KitsControls/lib-maxiv-pandaboxlib",
      packages =['pandaboxlib'],
      package_dir = {'':'src'},
      extras_require={"tests": ["pytest", "mock"]},
     )
