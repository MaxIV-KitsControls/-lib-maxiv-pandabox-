import pandaboxlib

host = 'pandabox'

panda = pandaboxlib.PandA(host)
panda.connect_to_panda()

panda.query('FMC_ACQ427_OUT.VAL4=FMC_ACQ427_IN.VAL2')
panda.query('SEQ1.POSA=FMC_ACQ427_IN.VAL2')
panda.query('SEQ1.ENABLE=ONE')
panda.query('SEQ1.PRESCALE.UNITS=ms')
panda.query('SEQ1.PRESCALE=100')
panda.query('SEQ1.REPEATS=1')
panda.query('SEQ1.TABLE<B\nAAAXAAAAAAABAAAAAQAAAA==\n')

panda.query('TTLOUT1.VAL=SEQ1.OUTA')

panda.disconnect_from_panda()


