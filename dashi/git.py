import aiohttp
import asyncio
import base64
import dateutil
import json
import logging
import os
import subprocess

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

    @asyncio.coroutine
    def get_commits(self):
        url = 'https://bitbucket.org/api/2.0/repositories/{}/{}/commits'.format(self.config['owner'], self.name)
        data = yield from self.request(url)
        commits = data['values']
        LOGGER.debug("Got %s commits for %s", data['pagelen'], self.name)
        while 'next' in data:
            data = yield from self.request(data['next'])
            LOGGER.debug("Got %s more commits for %s", data['pagelen'], self.name)
            commits += data['values']
        return commits

@asyncio.coroutine
def get_all_commits(config):
    results = {}
    for repo in config['respositories']:
        commits = yield from get_commits(config, repo)
        results[repo] = commits
    return results

@asyncio.coroutine
def get_commits(config, repoconfig):
    _repo = repo(config, repoconfig)
    commits = yield from _repo.get_commits()
    return commits

@asyncio.coroutine
def get_all_commits_simultaneously(config):
    results = {}
    def _on_done(name, future):
        exc = future.exception()
        if exc:
            raise Exception("Failed to get information for {}: {}".format(name, exc))
        results[name] = future.result()

    coroutines = []
    for repo in config['respositories']:
        coro = asyncio.async(get_commits(config, repo))
        coro.add_done_callback(functools.partial(_on_done, repo))
        coroutines.append(coro)
    yield from asyncio.wait(coroutines)
    return results

def get_commits_after(path, start):
    os.chdir(path)
    command = [
        'git',
        'log',
        '--pretty=format:"%h %aI %aE"',
        '--after={}'.format(start.isoformat())
    ]
    output = subprocess.check_output(command)
    output = output.decode('utf-8')
    lines = output.split('\n')
    lines = [line[1:-1] for line in lines]
    lines = [line.split(' ') for line in lines]
    lines = [line for line in lines if len(line) == 3]
    return [{
        'author'    : _author,
        'datetime'  : dateutil.parser.parse(_datetime),
        'hash'      : _hash,
        'repo'      : path,
    } for _hash, _datetime, _author in lines]

def get_all_commits(config, timepoint):
    all_commits = []
    for repo in config['repositories']:
        path = os.path.join(config['repositoryroot'], repo['name'])
        commits = get_commits_after(path, timepoint)
        all_commits += commits
    return all_commits

def commits_between(start, end, all_commits):
    return [commit for commit in all_commits if end > commit['datetime'] > start]

