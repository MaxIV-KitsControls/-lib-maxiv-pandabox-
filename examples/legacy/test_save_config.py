from pandaboxlib import PandA
import numpy as np
import time
import socket
from multiprocessing.pool import ThreadPool

host = 'w-kitslab-pandabox-0'

panda = PandA(host)
panda.connect_to_panda()

panda.save_config("test.dat")

panda.load_config("test.dat")
