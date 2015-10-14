import logging

import requests
import requests.auth

LOGGER = logging.getLogger(__name__)

def get_statistics(config, start, end):
    session = create_session(**config['jira'])
    created = issues_created_between(session, start, end)
    without_epic = _get_without_epic(created)
    without_estimate = _get_without_estimate(created)
    resolved = issues_resolved_between(session, start, end)
    return {
        'created'           : created['total'],
        'resolved'          : resolved['total'],
        'without_estimate'  : len(without_estimate),
        'without_epic'      : len(without_epic),
        'personal'          : {user.name: len(_get_personally_resolved(resolved, user)) for user in config['users']}
    }

def create_session(username, password):
    auth = requests.auth.HTTPBasicAuth(username, password)
    session =  requests.Session()
    session.auth = auth
    return session

def _get_without_epic(created):
    without_epic = [issue for issue in created['issues'] if issue['fields']['customfield_10008'] is None]
    return without_epic

def _get_without_estimate(created):
    def _has_estimate(issue):
        return any([issue['fields']['aggregatetimeestimate'],
                    issue['fields']['aggregatetimeoriginalestimate']])

    without_estimate = [issue for issue in created['issues'] if not _has_estimate(issue)]
    return without_estimate

def _get_personally_resolved(resolved, user):
    results = []
    for issue in resolved['issues']:
        assignee = issue['fields']['assignee']
        key = assignee['key'] if assignee is not None else None
        if key == user.config.get('jirakey', None):
            results.append(issue)
    return results

def _do_search(session, payload, startAt=None):
    startAt = startAt if startAt is not None else 0
    payload['startAt'] = startAt
    response = session.post("https://sendshapes.atlassian.net/rest/api/2/search", json=payload)
    if not response.ok:
        raise Exception("Failed to query jira: {}".format(response.json()))
    data = response.json()
    return data

def search(session, payload):
    startAt = 0
    data = _do_search(session, payload, startAt)
    results = data
    while results['total'] > results['maxResults']:
        startAt += data['maxResults']
        data = _do_search(session, payload, startAt)
        results['maxResults'] += data['maxResults']
        results['issues'] += data['issues']
    return results

def get_issue(session, issue):
    query = {
        "jql"   :"id = {}".format(issue),
    }
    return search(session, query)

def issues_created_between(session, start, end):
    jql = "created >= {} AND created < {}".format(start.date().isoformat(), end.date().isoformat())
    query = {
        "jql"           : jql,
        "fields"        : [
            "aggregateprogress",
            "aggregatetimeestimate",
            "aggregatetimeoriginalestimate",
            "aggregatetimespent",
            "created",
            "customfield_10008",
            "id",
        ],
    }
    return search(session, query)

def issues_resolved_between(session, start, end):
    jql = "resolved >= {} AND resolved < {}".format(start.date().isoformat(), end.date().isoformat())
    query = {
         "jql"      : jql,
         "fields"   : ["assignee", "id", "resolved"],
     }
    return search(session, query)
