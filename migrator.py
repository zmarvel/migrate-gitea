import requests
import json
import pprint

# curl --request GET --url https://yourusername:password@gitea.your.host/api/v1/users/<username>/tokens


with open('monferno-token.txt', 'r') as f:
    monferno_token = f.read().strip()

with open('natu-token.txt', 'r') as f:
    natu_token = f.read().strip()

monferno_host = 'git-beta.zackmarvel.com:80'
natu_host = 'git.zackmarvel.com'


def get(host, path, params=None, headers=None):
    response = requests.get(f'http://{host}/api/v1/{path}', headers=headers, params=params)
    json_content = json.loads(response.content)
    return json_content

# Get user ids
natu_uid = get(natu_host, 'user', headers={'Authorization': f'token {natu_token}'})['id']
print('natu_uid', natu_uid)
monferno_uid = get(monferno_host, 'user', headers={'Authorization': f'token {monferno_token}'})['id']
print('monferno_uid', monferno_uid)


natu_repos = get(natu_host, 'repos/search',
        headers={'Authorization': f'token {natu_token}'},
        params={'uid': natu_uid})['data']
for repo in natu_repos:
    repo_addr = f'http://{natu_host}/{repo["full_name"]}.git'
    print(repo_addr)
    response = requests.post(f'http://{monferno_host}/api/v1/repos/migrate/',
            headers={'Authorization': f'token {monferno_token}'},
            params={
                'access_token': monferno_token,
                },
            data={
                'auth_token': natu_token,
                'clone_addr': repo_addr,
                'repo_name': repo['name'],
                'mirror': repo['mirror'],
                'mirror_interval': repo['mirror_interval'],
                'description': repo['description'],
                # 'issues': repo['has_issues'],
                # 'pull_requests': repo['has_pull_requests'],
                'wiki': repo['has_wiki'],
                'private': repo['private'],
                })
    print(response.status_code)
    print(response.content)
