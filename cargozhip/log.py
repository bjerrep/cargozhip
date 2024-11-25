# This is a minimal logging module without external dependencies as if that was a quality
# in itself. Otherwise check out 'coloredlogs' which is the real thing.
#
import logging, sys

indent = ''


class Indent():
    def __init__(self):
        global indent
        indent += '   '


class Unindent():
    def __init__(self):
        global indent
        indent = indent[:-3]


GREY = '\033[0;37m'
WHITE = '\033[0;37m'
WHITEBOLD = '\033[1;37m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
RED = '\033[1;31m'
LIGHT_BLUE = '\033[1;34m'
REDINVERSE = '\033[1;37;41m'
RESET = '\033[0m'

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(f'{indent}%(levelname)s %(message)s{RESET}')
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def set_log_colors():
    if True:
        logging.addLevelName(logging.DEBUG, f'{WHITE}{logging.getLevelName(logging.DEBUG):.3}')
        logging.addLevelName(logging.INFO, f'{GREEN}{logging.getLevelName(logging.INFO):.3}')
        logging.addLevelName(logging.WARNING, f'{YELLOW}{logging.getLevelName(logging.WARNING):.3}')
        logging.addLevelName(logging.ERROR, f'{RED}{logging.getLevelName(logging.ERROR):.3}')
        logging.addLevelName(logging.CRITICAL, f'{REDINVERSE}{logging.getLevelName(logging.CRITICAL):.3}')
    else:
        logging.addLevelName(logging.DEBUG, f'{logging.getLevelName(logging.DEBUG):.3}')
        logging.addLevelName(logging.INFO, f'{logging.getLevelName(logging.INFO):.3}')
        logging.addLevelName(logging.WARNING, f'{logging.getLevelName(logging.WARNING):.3}')
        logging.addLevelName(logging.ERROR, f'{logging.getLevelName(logging.ERROR):.3}')
        logging.addLevelName(logging.CRITICAL, f'{logging.getLevelName(logging.CRITICAL):.3}')


def deb(msg, newline=True):
    if not newline:
        handler.terminator = ''
    logger.debug('%s%s',indent, msg)
    if not newline:
        handler.terminator = '\n'


def inf(msg, newline=True):
    if not newline:
        handler.terminator = ''
    logger.info('%s%s',indent, msg)
    if not newline:
        handler.terminator = '\n'


def war(msg):
    logger.warning('%s%s%s%s', REDINVERSE, indent, msg, RESET)


def err(msg):
    raise Exception(msg)
