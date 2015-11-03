import asyncio
import datetime
import logging
import os
import pickle

import jinja2

import dashi.config
import dashi.db
import dashi.jenkins
import dashi.jira
import dashi.json
import dashi.sentry
import dashi.time
import dashi.upload

LOGGER = logging.getLogger(__name__)

class Environment():
    def __init__(self, config, end):
        self.config               = config
        self.end                  = end
        self.template_loader      = jinja2.FileSystemLoader(searchpath=self.config['paths']['template'])
        self.template_environment = jinja2.Environment(loader=self.template_loader)

        self.output_path = self.config['paths']['output']
        self.archive_path = self.end.date().isoformat()

    def setup_output(self):
        try:
            os.mkdir(self.output_path)
            LOGGER.info("Created %s", self.output_path)
        except OSError:
            pass

    def write_file(self, templatename, context, path=None):
        template = self.template_environment.get_template(templatename)
        output = template.render(**context)

        path = path or os.path.join(self.archive_path, templatename)
        path = os.path.join(self.output_path, path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(output)
            LOGGER.debug("Wrote %s", path)

    def archives(self):
        for f in os.listdir(self.output_path):
            basename = os.path.basename(f)
            if os.path.isdir(os.path.join(self.output_path, f)) and not basename.startswith('.'):
                yield f

    def write_files(self, context):
        context['path'] = "/{}/".format(self.end.date().isoformat())

        context['archives'] = self.archives()
        for templatepath, outputpath in self.output():
            if templatepath:
                self.write_file(templatepath, context, path=outputpath)

        # upload raw data
        del context['archives']
        path = os.path.join(self.output_path, self.archive_path, 'data.json')
        with open(path, 'w') as f:
            dashi.json.dump(context, f)

    def output(self):
        yield 'root.html', 'index.html'
        for template in ('index', 'commits', 'jenkins', 'jira', 'sentry'):
            templatename = template + '.html'
            yield templatename, os.path.join(self.archive_path, templatename)
        yield None, os.path.join(self.archive_path, 'data.json')

@asyncio.coroutine
def update_data(config):
    LOGGER.info("Updating data...")
    coros = [dashi.git.update_repo(repo) for repo in config['repositories']]
    yield from asyncio.wait(coros)
    LOGGER.info("Gathing data...")

@asyncio.coroutine
def get_context(config, args):
    try:
        with open(cache_path(), 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        pass

    if not args.no_update:
        yield from update_data(config)

    start, end = dashi.time.get_checkpoint(datetime.datetime.utcnow() - datetime.timedelta(days=7))
    all_commits = yield from dashi.git.get_all_commits(config, start)
    LOGGER.debug("%d commits", len(all_commits))

    jenkins = dashi.jenkins.get_jenkins_stats(config)

    jira = dashi.jira.get_statistics(config, start, end)

    sentry = dashi.sentry.get_statistics(config, start, end)
    LOGGER.info("Gather complete")

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
    with open(cache_path(), 'wb') as f:
        pickle.dump(context, f)
    return context

@asyncio.coroutine
def go(config, args):
    context = yield from get_context(config, args)

    env = Environment(config, context['end'])
    env.setup_output()

    env.write_files(context)

    if args.upload:
        dashi.upload.go(config, env)

def cache_path():
    return os.path.join(os.environ['HOME'], '.dashi', 'cache.pickle')
