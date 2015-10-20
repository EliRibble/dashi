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

    @property
    def name(self):
        return self.config['name']

    @property
    def first_name(self):
        return self.name.partition(' ')[0]

    def __str__(self):
        return 'User {}'.format(self.config['name'])

    def __repr__(self):
        return str(self)

def _load_config():
    for path in ['dashi.conf', os.path.join(os.environ['HOME'], '.dashi', 'config'), '/etc/dashi.conf']:
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
