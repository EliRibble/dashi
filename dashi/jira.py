import logging

import requests
import requests.auth

LOGGER = logging.getLogger(__name__)

def create_session(username, password):
    auth = requests.auth.HTTPBasicAuth(username, password)
    session =  requests.Session()
    session.auth = auth
    return session

def _do_search(session, payload, startAt=None):
    startAt = startAt if startAt is not None else 0
    payload['startAt'] = startAt
    response = session.post("https://sendshapes.atlassian.net/rest/api/2/search", json=payload)
    if not response.ok:
        import pdb;pdb.set_trace()
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
