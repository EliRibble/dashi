import logging

from jenkinsapi.custom_exceptions import NoResults, UnknownJob
from jenkinsapi.jenkins import Jenkins

LOGGER = logging.getLogger(__name__)

def _add_build(results, build):
    timestamp = build.get_timestamp()
    for r in results:
        if timestamp < r['end'] and timestamp > r['start']:
            resultset = build.get_resultset()
            r['tests'] = max(r['tests'], len(resultset))
            LOGGER.debug("Added %s with %s tests", build.name, len(resultset))

def get_jenkins_stats(config):
    jenkins = connect(config)
    return {job : get_latest_build(jenkins, job) for job in config['jenkins']['jobs']}

def connect(config):
    return Jenkins(
        config['jenkins']['url'],
        username=config['jenkins']['username'],
        password=config['jenkins']['password'],
    )

def get_test_results_by_time_periods(config, repos):
    jenkins = connect(config)
    return {
            repo['name']    : get_test_results_for_repo(jenkins, repo)
        for repo in repos}

def get_latest_build(jenkins, jobname):
    try:
        job = jenkins[jobname]
    except UnknownJob:
        LOGGER.warning("Unable to get data on Jenkins job %s", jobname)
        return
    build_ids = job.get_build_ids()
    latest_build = max(build_ids)
    for build_id in range(latest_build)[::-1]:
        build = job.get_build(build_id)
        try:
            resultset = build.get_resultset()
            return {
                    'build'     : build.buildno,
                    'timestamp' : build.get_timestamp(),
                    'tests'     : len(resultset),
                    }
        except NoResults:
            pass

def get_test_results_for_repo(jenkins, repo):
    try:
        job = jenkins[repo['name']]
    except UnknownJob:
        LOGGER.warning("Unable to get data on Jenkins job %s", repo['name'])
        return []

    results = []
    build_ids = job.get_build_ids()
    for build_id in build_ids:
        build = job.get_build(build_id)
        try:
            resultset = build.get_resultset()
            results.append({
                'name'  : repo['name'],
                'date'  : build.get_timestamp(),
                'build' : build.buildno,
                'tests' : len(resultset),
            })
        except NoResults:
            pass
    return results
