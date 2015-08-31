import collections
import dashi.config
import dashi.db
import dashi.jenkins
import dashi.time
import datetime
import functools
import jinja2
import logging
import os
import pprint

LOGGER = logging.getLogger(__name__)

def show_stats_for(user):
    connection = dashi.db.connection()

    print(dashi.db.get_all_authors(connection))
    return
    periods = dashi.time.checkpoints_since(datetime.datetime(2015, 1, 1, 0, 0, 0, 1))
    commits = dashi.db.get_commit_counts_by_time_periods(connection, periods, user)
    print("\t".join(["Start", "End", "Total", "Mine"]))
    for stat in commits:
        print('\t'.join(map(str, [stat['start'].date(), stat['end'].date(), stat['total'], stat['mine']])))

def show_jenkins_stats(config):
    periods = dashi.time.checkpoints_since(datetime.datetime(2015, 1, 1, 0, 0, 0, 1))
    test_results = dashi.jenkins.get_test_results_by_time_periods(config, config['repositories'], periods)
    for repo in test_results.keys():
        for result in test_results[repo]:
            if result['tests'] > 0:
                print("{}\t{}\t{}".format(
                    result['start'].isoformat(),
                    result['end'].isoformat(),
                    result['tests']))
