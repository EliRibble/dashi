import collections
import datetime
import functools
import logging
import os
import pprint

import jinja2

import asyncio
import dashi.config
import dashi.db
import dashi.time

LOGGER = logging.getLogger(__name__)

class Environment():
    def __init__(self):
        self.config = dashi.config.parse()
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
def go():
    env = Environment()
    env.setup_output()
    env.write_file('index.html', {})
    env.write_file('commits.html', {})
