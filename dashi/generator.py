import asyncio
import collections
import dashi.config
import dashi.db
import dashi.time
import datetime
import functools
import jinja2
import logging
import os
import pprint

LOGGER = logging.getLogger(__name__)

@asyncio.coroutine
def go():
    config = dashi.config.parse()
    template_loader = jinja2.FileSystemLoader(searchpath=config.template_path)
    template_environment = jinja2.Environment(loader=template_loader)

    connection = dashi.db.connection()
    authors = dashi.db.get_all_authors(connection)
    print(authors)
    return 
    LOGGER.debug(repo_stats)
    try:
        os.mkdir(config.output_path)
    except OSError:
        pass

    template = template_environment.get_template('index.html')
    output = template.render(repo_stats=repo_stats)

    path = os.path.join(config.output_path, 'index.html')
    with open(path, 'w') as f:
        f.write(output)

