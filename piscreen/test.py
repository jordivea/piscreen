import configparser
import logging
import os

# config = configparser.ConfigParser()
# config.read('piscreen.cfg')
# print(config.sections())
# cfg_logfile = config.get('log', 'logfile')
# cfg_loglevel = config.get('log', 'level')
# logging.basicConfig(filename=cfg_logfile, level=eval('logging.' + cfg_loglevel))
# logging.warning('this is me')
# logging.debug('hhhhe')
#
# settings = config['config']
# print(settings['image_history_max'])


f = os.path.splitext(os.path.realpath(__file__))[0] + '.cfg'
print(f)
