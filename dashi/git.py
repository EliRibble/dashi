import aiohttp
import asyncio
import base64
import json
import logging

LOGGER = logging.getLogger(__name__)

def repo(config, repotype, name):
    if repotype == 'bitbucket':
        return Bitbucket(config, name)
    elif repotype == 'github':
        return Github(config, name)

def basic_auth(username, password):
    value = '{}:{}'.format(username, password)
    encoded = base64.b64encode(value.encode('utf-8')).decode('utf-8')
    auth = 'Basic {}'.format(encoded)
    return {'Authorization': auth}

class Repo():
    def __init__(self, config, name):
        self.name = name

    def commits(self):
        raise NotImplementedError

class Github(Repo):
    @asyncio.coroutine
    def get_commits(self):
        return []

class ThrottleError(Exception):
    pass

class Bitbucket(Repo):
    def __init__(self, config, fullname):
        super().__init__(fullname, config)
        owner, _, name = fullname.partition(':')
        if not owner:
            raise Exception("Invalid owner {} for {}".format(owner, fullname))
        if not name:
            raise Exception("Invalid name {} for {}".format(name, fulname))
        self.name    = name
        self.owner   = owner
        self.auth = (config.bitbucket_username, config.bitbucket_password)


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
        url = 'https://bitbucket.org/api/2.0/repositories/{}/{}/commits'.format(self.owner, self.name)
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
    for repo in config.repository:
        commits = yield from get_commits(config, repo)
        results[repo] = commits
    return results

@asyncio.coroutine
def get_commits(config, repo):
    repotype, _, name = repo.partition(':')
    repo = dashi.git.repo(config, repotype, name)
    commits = yield from repo.get_commits()
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
    for repo in config.repository:
        coro = asyncio.async(get_commits(config, repo))
        coro.add_done_callback(functools.partial(_on_done, repo))
        coroutines.append(coro)
    yield from asyncio.wait(coroutines)
    return results
