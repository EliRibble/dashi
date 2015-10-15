import logging

import dateutil
import requests

LOGGER = logging.getLogger(__name__)


def get_statistics(config, start, end):

    session = create_session(config['sentry']['username'], config['sentry']['password'], config['sentry']['url'])
    all_issues = [get_resolved_issues(config, session, project) for project in config['sentry']['projects']]
    all_issues = [issue for group in all_issues for issue in group]
    in_period = [issue for issue in all_issues if _resolved_between(issue, start, end)]
    formatted = [format_issue(issue, config['users']) for issue in in_period]
    by_user = {user.name: get_user_statistics(formatted, user) for user in config['users']}
    return {
        "issue_count"   : len(in_period),
        "by_user"       : by_user,
    }

def format_issue(issue, users):
    return {
        "count"         : issue['count'],
        "first_seen"    : dateutil.parser.parse(issue['firstSeen']),
        "last_seen"     : dateutil.parser.parse(issue['lastSeen']),
        "project"       : issue['project']['name'],
        "resolved_by"   : _get_resolved_by(issue, users),
        "url"           : issue['permalink'],
    }

def get_user_statistics(issues, user):
    def _get_key(issue):
        return "{}:{}".format(issue['project'], issue['last_seen'].isoformat())

    my_issues = [issue for issue in issues if issue['resolved_by'] == user]
    return {
        'count'         : len(my_issues),
        'issues'        : sorted(my_issues, key=_get_key),
        'percentage'    : get_percentage(issues, my_issues),
    }

def get_percentage(issues, my_issues):
    return round(len(my_issues) / float(len(issues)), 2) * 100

def _log_request(request):
    LOGGER.debug("--- Request ---")
    LOGGER.debug("%s %s", request.method, request.url)
    for header, value in request.headers.items():
        LOGGER.debug("  %s: %s", header, value)
    LOGGER.debug(" ")
    LOGGER.debug(request.body)

def _log_response(response):
    LOGGER.debug("--- Response ---")
    LOGGER.debug("%s", response.status_code)
    for header, value in response.headers.items():
        LOGGER.debug("  %s: %s", header, value)
    LOGGER.debug(" ")
    #LOGGER.debug(response.text)

def create_session(username, password, url):
    login_url = url + '/auth/login/'
    session = requests.Session()
    response = session.get(login_url)
    assert response.ok

    payload = {
        "csrfmiddlewaretoken"   : response.cookies['csrf'],
        "op"                    : "login",
        "username"              : username,
        "password"              : password,
    }
    request = requests.Request('POST', login_url, data=payload, headers={'Referer': login_url})
    prepared = session.prepare_request(request)
    response = session.send(prepared)
    assert response.ok

    return session

def get_resolved_issues(config, session, project):
    url = '{}/groups/?query=is%3Aresolved&limit=100&statsPeriod=14d'.format(project['url'])
    request = requests.Request('GET', url)
    prepared = session.prepare_request(request)
    response = session.send(prepared)
    assert response.ok
    data = response.json()

    results = []
    LOGGER.debug("Getting %s individual issues for %s", len(data), project)
    for issue in data:
        issue_url = '{}/api/0/groups/{}/'.format(config['sentry']['url'], issue['id'])
        response = session.get(issue_url)
        assert response.ok
        results.append(response.json())
    return results

def _get_resolved_datetime(issue):
    for action in issue['activity']:
        created = dateutil.parser.parse(action['dateCreated'])
        if action['type'] == 'set_resolved':
            return created

def _resolved_between(issue, start, end):
    resolved = _get_resolved_datetime(issue)
    return resolved and end > resolved > start

def _get_resolved_by(issue, users):
    for action in issue['activity']:
        #created = dateutil.parser.parse(action['dateCreated'])
        if action['type'] == 'set_resolved':
            for user in users:
                if action['user'] and action['user']['name'] in user.aliases:
                    return user
    return None

def _resolved_by(issue, user):
    for action in issue['activity']:
        #created = dateutil.parser.parse(action['dateCreated'])
        if all([
            action['type'] == 'set_resolved',
            action['user']['name'] in user.aliases if action['user'] else False,
            ]):
            return True
    return False

def _get_resolved_between(issues, start, end):
    return [issue for issue in issues if _resolved_between(issue, start, end)]

def _get_resolved_between_by(issues, start, end, user):
    return [issue for issue in issues if _resolved_between(issue, start, end) and _resolved_by(issue, user)]
