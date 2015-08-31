import asyncio
import dashi.config
import dashi.git
import dashi.jenkins
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

    cursor = conn.cursor()
    for repo in config['repositories']:
        commits = yield from dashi.git.get_commits(config, repo)
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

def get_commit_counts_by_time_periods(connection, periods, user):
    return [{
        'start' : period[0],
        'end'   : period[1],
        'total' : _total_commits(connection, period[0], period[1]),
        'mine'  : _commits_for(connection, period[0], period[1], user),
    } for period in periods]

def _total_commits(connection, start, end):
    cursor = connection.cursor()
    result = cursor.execute(
        "SELECT hash FROM commits WHERE datetime(date) > datetime(?) AND datetime(date) < (?)",
        (start.isoformat(), end.isoformat())
    )
    return len(result.fetchall())

def _as_list(l):
    items = ["'{}'".format(i) for i in l]
    return "({})".format(','.join(items))

def _commits_for(connection, start, end, user):
    cursor = connection.cursor()
    result = cursor.execute(
        "SELECT hash FROM commits WHERE datetime(date) > datetime(?) AND datetime(date) < (?) AND author IN {}".format(_as_list(user.aliases)),
        (start.isoformat(), end.isoformat())
    )
    return len(result.fetchall())

def _create_tables(conn):
    c = conn.cursor()
    c.execute("""CREATE TABLE commits
        (date TEXT, hash TEXT, author TEXT, repository TEXT)""")

    conn.commit()
