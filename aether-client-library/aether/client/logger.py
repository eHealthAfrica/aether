import logging

LOG = logging.getLogger(__name__)
handler = logging.StreamHandler()
LOG.addHandler(handler)
handler.setFormatter(logging.Formatter(
    '%(asctime)s [Client] %(levelname)-8s %(message)s'))
