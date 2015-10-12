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

@asyncio.coroutine
def go():
    config = dashi.config.parse()
    template_loader = jinja2.FileSystemLoader(searchpath=config['paths']['template'])
    template_environment = jinja2.Environment(loader=template_loader)

    output_path = config['paths']['output']
    try:
        os.mkdir(output_path)
        LOGGER.info("Created %s", output_path)
    except OSError:
        pass

    template = template_environment.get_template('index.html')
    output = template.render()

    path = os.path.join(output_path, 'index.html')
    with open(path, 'w') as f:
        f.write(output)
        LOGGER.debug("Wrote %s", path)
