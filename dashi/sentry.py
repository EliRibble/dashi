import logging

from requests import Session

LOGGER = logging.getLogger(__name__)

def create_session(username, password):
    session = Session()
    response = session.get("https://beta.getsentry.com/auth/login/")
    assert response.ok

    payload = {
        "csrfmiddlewaretoken"   : response.cookies['csrf'],
        "op"                    : "login",
        "username"              : username,
        "password"              : password,
    }
    response = session.post("https://beta.getsentry.com/auth/login/", data=payload, headers={'Referer': 'https://beta.getsentry.com/authentise/'})
    assert response.ok
    return session

def get_resolved_issues(session, project):

    url = 'https://beta.getsentry.com/api/0/projects/authentise/{}/groups/?query=is%3Aresolved&limit=100&statsPeriod=14d'.format(project)
    response = session.get(url)
    assert response.ok
    data = response.json()

    results = []
    LOGGER.debug("Getting %s individual issues for %s", len(data), project)
    for issue in data:
        issue_url = 'https://beta.getsentry.com/api/0/groups/{}/'.format(issue['id'])
        response = session.get(issue_url)
        assert response.ok
        results.append(response.json())
    return results

#def get_resolved_issues(project):
    #'https://beta.getsentry.com/api/0/groups/69931207/'
    #requests.get('https://app.getsentry.com/api/authentise/dev-hoth/poll/?status=1')
