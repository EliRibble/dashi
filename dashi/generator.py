import asyncio
import collections
import datetime
import functools
import logging
import os
import pprint

import jinja2

import dashi.config
import dashi.db
import dashi.time

LOGGER = logging.getLogger(__name__)

class Environment():
    def __init__(self, config):
        self.config = config
        self.template_loader = jinja2.FileSystemLoader(searchpath=self.config['paths']['template'])
        self.template_environment = jinja2.Environment(loader=self.template_loader)

        self.output_path = self.config['paths']['output']

    def setup_output(self):
        try:
            os.mkdir(self.output_path)
            LOGGER.info("Created %s", self.output_path)
        except OSError:
            pass

    def write_file(self, templatename, context):
        template = self.template_environment.get_template(templatename)
        output = template.render(**context)

        path = os.path.join(self.output_path, templatename)
        with open(path, 'w') as f:
            f.write(output)
            LOGGER.debug("Wrote %s", path)

@asyncio.coroutine
def update_data(config):
    LOGGER.info("Updating data...")
    yield from asyncio.wait([dashi.git.update_repo(config, repo) for repo in config['repositories']])
    LOGGER.info("Gathing data...")

@asyncio.coroutine
def go(config, args):
    if not args.no_update:
        yield from update_data(config)

    start, end = dashi.time.get_checkpoint(datetime.datetime.utcnow() - datetime.timedelta(days=14))
    all_commits = yield from dashi.git.get_all_commits(config, start)
    LOGGER.debug("%d commits", len(all_commits))
    LOGGER.info("Gather complete")

    env = Environment(config)
    env.setup_output()

    context = {
        'commits'   : all_commits,
        'end'       : end,
        'start'     : start,
        'users'     : config['users'],
    }
    LOGGER.debug(all_commits['Eli Ribble'][0])
    env.write_file('index.html', context)
    env.write_file('commits.html', context)
