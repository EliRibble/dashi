import asyncio
import base64
import json
import logging
import os
import re
import subprocess

import aiohttp
import dateutil
import dateutil.parser

LOGGER = logging.getLogger(__name__)

def repo(config, repoconfig):
    if repoconfig['host'] == 'bitbucket':
        return Bitbucket(config, repoconfig)
    elif repoconfig['host'] == 'github':
        return Github(config, repoconfig)
    else:
        raise Exception("Invalid repository host '{}'".format(repoconfig['host']))

def basic_auth(username, password):
    value = '{}:{}'.format(username, password)
    encoded = base64.b64encode(value.encode('utf-8')).decode('utf-8')
    auth = 'Basic {}'.format(encoded)
    return {'Authorization': auth}

class Repo():
    def __init__(self, config, repoconfig):
        self.config = repoconfig

    def commits(self):
        raise NotImplementedError

class Github(Repo):
    @asyncio.coroutine
    def get_commits(self):
        return []

class ThrottleError(Exception):
    pass

class Bitbucket(Repo):
    def __init__(self, config, repoconfig):
        super().__init__(config, repoconfig)
        self.auth = (config['bitbucket']['username'], config['bitbucket']['password'])


    @property
    def name(self):
        return self.config['name']

    @asyncio.coroutine
    def request(self, url):
        backoff = 1
        while backoff < 30:
            response = yield from aiohttp.get(url, headers=basic_auth(*self.auth))
            text = yield from response.read()
            text = text.decode('utf-8')
            if response.status == 429:
                LOGGER.debug("Being throttled GETing %s, waiting %s seconds", url, backoff)
                yield from asyncio.sleep(backoff)
                backoff = backoff * 1.5
            elif response.status in (200, 201, 204):
                return json.loads(text)
            else:
                import pdb;pdb.set_trace()
                raise Exception("Failed to get commits at {}: {} {}".format(url, response.status, text))
        raise Exception("Giving up on {}, too throttled".format(url))

FILE_PATTERN = re.compile(r"(?P<files>\d+) file(s)? changed")
INSERT_PATTERN = re.compile(r"(?P<inserts>\d+) insertion(s)?\(\+\)")
DELETE_PATTERN = re.compile(r"(?P<deletes>\d+) deletion(s)?\(\-\)")
def _add_stats(commit, line):
    matches = [
        FILE_PATTERN.search(line),
        INSERT_PATTERN.search(line),
        DELETE_PATTERN.search(line),
    ]
    if not any(matches):
        raise Exception("Can't get stats from {}".format(line))
    commit['files']   = int(matches[0].group('files'))
    commit['inserts'] = int(matches[1].group('inserts')) if matches[1] else 0
    commit['deletes'] = int(matches[2].group('deletes')) if matches[2] else 0


def _parse_commits(output):
    lines = output.split('\n')
    commits = []
    commit = {}
    for line in lines:
        if not line:
            if commit:
                commits.append(commit)
                commit = {}
        elif line.startswith(' '):
            _add_stats(commit, line)
        elif line.startswith('"') and line.endswith('"'):
            if commit:
                commits.append(commit)

            line = line[1:-1]
            _hash, _datetime, _author = line.split(' ')
            commit = {
                'author'    : _author,
                'datetime'  : dateutil.parser.parse(_datetime),
                'hash'      : _hash,
                'files'     : 0,
                'inserts'   : 0,
                'deletes'   : 0,
            }
        else:
            raise Exception("Unrecognized line {}".format(line))
    if commit:
        commits.append(commit)
    return commits

@asyncio.coroutine
def get_commits(config, repo, start, end=None):
    path = repo['path']
    command = [
            'git',
            'log',
            '--pretty=format:"%h %aI %aE"',
            '--shortstat',
            '--all',
            '--after={}'.format(start.isoformat())]
    if end is not None:
        command.append('--before={}'.format(end.isoformat()))
    stdout, stderr = yield from run_process(command, chdir=path)
    output = subprocess.check_output(command)
    output = output.decode('utf-8')
    commits = _parse_commits(output)
    for commit in commits:
        commit['repo'] = repo['name']
    return commits

def sort_commits(user, commits):
    def _key(commit):
        return ':'.join([commit['repo'], commit['datetime'].isoformat(), commit['hash']])
    my_commits = [commit for commit in commits if commit['author'] in user.aliases]
    return sorted(my_commits, key=_key)

def collate_commits(users, commits):
    return {user.name: sort_commits(user, commits) for user in users}

@asyncio.coroutine
def get_all_commits(config, timepoint):
    all_commits = []
    for repo in config['repositories']:
        commits = yield from get_commits(config, repo, timepoint)
        all_commits += commits
    _check_unrecognized_commiters(config['users'], all_commits)
    all_commits = collate_commits(config['users'], all_commits)
    return all_commits

def _check_unrecognized_commiters(users, commits):
    for commit in commits:
        if not any([commit['author'] in user.aliases for user in users]):
            LOGGER.warning("Commit %s did not match any known users", commit)

def commits_between(start, end, all_commits):
    return [commit for commit in all_commits if end > commit['datetime'] > start]

@asyncio.coroutine
def run_process(command, chdir=None):
    if chdir:
        os.chdir(chdir)
        LOGGER.debug("Executing %s in %s", " ".join(command), chdir)
    process = yield from asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE)
    (stdout, stderr) = yield from process.communicate()
    if process.returncode != 0:
        raise Exception("Failed to update git repository %s", repo)
    return stdout, stderr

@asyncio.coroutine
def update_repo(config, repo):
    command = ['git', 'pull']
    stdout, stderr = yield from run_process(command, repo['path'])
    LOGGER.debug("Updated data in repo %s", repo['name'])
