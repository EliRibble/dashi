import asyncio
import dashi.config
import dashi.git
import logging
import os
import sqlite3

LOGGER = logging.getLogger(__name__)

def connection():
    return sqlite3.connect('dashi.db')

@asyncio.coroutine
def load():
    config = dashi.config.parse()

    if os.path.exists('dashi.db'):
        os.remove('dashi.db')

    conn = connection()

    _create_tables(conn)

    commits = yield from dashi.git.get_all_commits(config)
    cursor = conn.cursor()
    for repo, commits in commits.items():
        simplified = [(
            commit['date'],
            commit['hash'],
            commit['author']['user']['display_name'] if 'user' in commit['author'] else commit['author']['raw'],
            repo)
        for commit in commits]
        cursor.executemany("INSERT INTO commits VALUES (?,?,?,?)", simplified)
        conn.commit()
        LOGGER.debug("Inserted %s rows into commits for %s", len(simplified), repo)

def get_all_authors(connection):
    cursor = connection.cursor()
    result = cursor.execute("SELECT DISTINCT author FROM commits")
    return [r[0] for r in result]

def _create_tables(conn):
    c = conn.cursor()
    c.execute("""CREATE TABLE commits
        (date TEXT, hash TEXT, author TEXT, repository TEXT)""")

    conn.commit()

def _commits_by_author(commits):
    result = collections.defaultdict(lambda: [])
    for commit in commits:
        result[commit['author']['user']['display_name']].append(commit)
    return result

def _commit_counts_by_week(commits):
    start = datetime.datetime(2015, 8, 1, 0, 0, 0, 1)
    periods = dashi.time.checkpoints_since(start)
    authors = {commit['author']['user']['display_name'] for commit in commits}
    result = [{
        'start'     : start,
        'end'       : end,
        'counts'    : [{author: 0 for author in authors}],
    } for start, end in periods]
    for commit in commits:
        date = datetime.datetime.strptime(commit['date'], "%Y-%m-%dT%H:%M:%S+00:00")
        for period in result:
            if period['start'] < date and period['end'] > date:
                author = commit['author']['user']['display_name']
                period['counts'][author] += 1
    return result

