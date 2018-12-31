import logging

from pttui.printers import LogHandler

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
#
_handler = LogHandler()
logger.addHandler(_handler)
# #
LOGGER=logging.getLogger(__name__)

LOGGER.debug("test")