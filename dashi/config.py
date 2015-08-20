import configargparse

def parse():
    parser = configargparse.ArgParser(default_config_files=['dashi.conf', '~/.dashi', '/etc/dashi.conf'], allow_unknown_config_file_keys=False)

    parser.add('jenkins-url', help='The URL to the jenkins instance')
    parser.add('jenkins-user', help='The user to connect to jenkins with')
    parser.add('jenkins-password', help='The password or API key of the jenkins user')

    parsed = parser.parse_args()
    return parsed
