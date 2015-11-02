import logging
import os

import yaml

LOGGER = logging.getLogger(__name__)

class User():
    def __init__(self, name, config):
        self.name = name
        self.config = config

    @property
    def aliases(self):
        return [self.email] + self.config.get('aliases', [])

    @property
    def email(self):
        return self.config['email']

    @property
    def first_name(self):
        return self.name.partition(' ')[0]

    def __str__(self):
        return 'User {}'.format(self.name)

    def __repr__(self):
        return str(self)

class Repository(): # pylint: disable=too-few-public-methods
    def __init__(self, name, config):
        self.name = name
        self.config = config

    @property
    def path(self):
        return self.config['path']

def _load_config():
    for path in ['dashi.conf', os.path.join(os.environ['HOME'], '.dashi', 'config'), '/etc/dashi.conf']:
        try:
            with open(path, 'r') as f:
                return yaml.load(f)
        except FileNotFoundError as e:
            LOGGER.info("Unable to read config file at %s: %s", path, e)
        except ValueError as e:
            LOGGER.warning("Failed to parse config file %s: %s", path, e)
    raise Exception("Unable to load any configuration files")

def parse():
    config = _load_config()

    config['users'] = [User(name, c) for name, c in config['users'].items()]
    config['repositories'] = [Repository(name, c) for name, c in config['repositories'].items()]

    return config

def get_user(config, username):
    matches = []
    for user in config['users']:
        for alias in user.aliases:
            if username in alias and user not in matches:
                matches.append(user)
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        raise Exception("Username '{}' matched {}".format(username, ', '.join([m['name'] for m in matches])))
    else:
        raise Exception("Unable to match user '{}'".format(username))
