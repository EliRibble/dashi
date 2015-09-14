from jenkinsapi.jenkins import Jenkins
from jenkinsapi.custom_exceptions import NoResults, UnknownJob
import logging

LOGGER = logging.getLogger(__name__)

def _add_build(results, build):
    timestamp = build.get_timestamp()
    for r in results:
        if timestamp < r['end'] and timestamp > r['start']:
            resultset = build.get_resultset()
            r['tests'] = max(r['tests'], len(resultset))
            LOGGER.debug("Added %s with %s tests", build.name, len(resultset))

def connect(config):
    return Jenkins(
        config['jenkins']['url'],
        username=config['jenkins']['username'],
        password=config['jenkins']['password'],
    )

def get_test_results_by_time_periods(config, repos, periods):
    jenkins = connect(config)
    return {
            repo['name']    : get_test_results_for_repo(jenkins, repo, periods)
        for repo in repos}

def show_latest_build(jenkins, reponame):
    try:
        job = jenkins[reponame]
    except UnknownJob:
        LOGGER.warning("Unable to get data on Jenkins job %s", reponame)
        return
    build_ids = job.get_build_ids()
    latest_build = max(build_ids)
    build_id = latest_build
    while True:
        build = job.get_build(build_id)
        try:
            resultset = build.get_resultset()
            print("\t".join([str(x) for x in (reponame, build.buildno, build.get_timestamp().isoformat(), len(resultset))]))
            return
        except NoResults:
            build_id -= 1
            if build_id < latest_build - 3:
                LOGGER.warning("Cannot find useful build for %s", reponame)
                return

def get_test_results_for_repo(jenkins, repo, periods):
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
