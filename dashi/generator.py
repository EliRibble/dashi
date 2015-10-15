import asyncio
import datetime
import logging
import os

import jinja2

import dashi.config
import dashi.db
import dashi.jenkins
import dashi.jira
import dashi.sentry
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

    start, end = dashi.time.get_checkpoint(datetime.datetime.utcnow() - datetime.timedelta(days=7))
    all_commits = yield from dashi.git.get_all_commits(config, start)
    LOGGER.debug("%d commits", len(all_commits))

    jenkins = dashi.jenkins.get_jenkins_stats(config)

    jira = dashi.jira.get_statistics(config, start, end)

    sentry = dashi.sentry.get_statistics(config, start, end)
    LOGGER.info("Gather complete")

    env = Environment(config)
    env.setup_output()

    context = {
        'commit_count'  : sum([len(info['commits']) for info in all_commits.values()]),
        'commits'       : all_commits,
        'end'           : end,
        'jenkins'       : jenkins,
        'jira'          : jira,
        'sentry'        : sentry,
        'start'         : start,
        'users'         : config['users'],
    }

    LOGGER.debug(context['commit_count'])
    env.write_file('index.html', context)
    env.write_file('commits.html', context)
    env.write_file('jenkins.html', context)
    env.write_file('jira.html', context)
    env.write_file('sentry.html', context)
