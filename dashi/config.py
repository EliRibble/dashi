import json
import logging
import os

LOGGER = logging.getLogger(__name__)

class User():
    def __init__(self, config):
        self.config = config

    @property
    def aliases(self):
        return [self.config['name']] + self.config.get('aliases', [])

def _load_config():
    for path in ['dashi.conf', os.path.join(os.environ['HOME'], '.dashi'), '/etc/dashi.conf']:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            LOGGER.info("Unable to read config file at %s", path)
        except ValueError as e:
            LOGGER.warning("Failed to parse config file %s: %s", path, e)
    raise Exception("Unable to load any configuration files")

def parse():
    config = _load_config()

    config['users'] = [User(c) for c in config['users']]

    return config
