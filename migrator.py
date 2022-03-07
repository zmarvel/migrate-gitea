import requests
import json
from argparse import ArgumentParser


def get(host, path, params=None, headers=None):
    response = requests.get(f'http://{host}/api/v1/{path}', headers=headers, params=params)
    json_content = json.loads(response.content)
    return json_content


def delete(host, path, params=None, headers=None):
    url = f'http://{host}/api/v1/{path}'
    print(f'DELETE {url}')
    response = requests.delete(url, headers=headers, params=params)
    return response
    # json_content = json.loads(response.content)
    # return json_content



def migrate(src_host, src_token, dst_host, dst_token):
    # Get user ids
    src_uid = get(src_host, 'user', headers={'Authorization': f'token {src_token}'})['id']
    print('src_uid', src_uid)
    dst_uid = get(dst_host, 'user', headers={'Authorization': f'token {dst_token}'})['id']
    print('dst_uid', dst_uid)


    src_repos = get(src_host, 'repos/search',
            headers={'Authorization': f'token {src_token}'},
            params={'uid': src_uid})['data']
    for repo in src_repos:
        repo_addr = f'http://{src_host}/{repo["full_name"]}.git'
        print(repo_addr)
        response = requests.post(f'http://{dst_host}/api/v1/repos/migrate/',
                headers={'Authorization': f'token {dst_token}'},
                params={
                    'access_token': dst_token,
                    },
                data={
                    'auth_token': src_token,
                    'clone_addr': repo_addr,
                    'repo_name': repo['name'],
                    'mirror': repo['mirror'],
                    'mirror_interval': repo['mirror_interval'],
                    'description': repo['description'],
                    'issues': repo['has_issues'],
                    'pull_requests': repo['has_pull_requests'],
                    'wiki': repo['has_wiki'],
                    'private': repo['private'],
                    })
        print(response.status_code)
        print(response.content)

        # migrate issues

        # migrate releases

        # TODO: migreate pull requests



def delete_all(host, token):
    auth_headers = {'Authorization': f'token {token}'}
    user = get(host, 'user', headers=auth_headers)
    print('user', user)
    uid = user['id']

    repos = get(host, 'repos/search',
            headers=auth_headers,
            params={'uid': uid})['data']

    for repo in repos:
        response = delete(host, f'repos/{user["login"]}/{repo["name"]}', headers=auth_headers)
        print(response.status_code)
        print(response.content)



if __name__ == '__main__':

    parser = ArgumentParser(description='Migrate from one gitea instance to another')

    parser.add_argument('--src-token', help='Source API token')
    parser.add_argument('--src-token-file', help='File containing source API token')
    parser.add_argument('--dst-token', help='Destination API token')
    parser.add_argument('--dst-token-file', help='File containing destination API token')
    parser.add_argument('--delete-all', action='store_true', help='Instead of migrating, delete all repos')
    parser.add_argument('src_host', help='Address (and optionally port) of source host')
    parser.add_argument('dst_host', help='Address (and optionally port) of destination host')

    args = parser.parse_args()

    if args.src_token_file is not None:
        with open(args.src_token_file, 'r') as f:
            src_token = f.read().strip()
    elif args.src_token is not None:
        src_token = args.src_token
    else:
        print('Must provide either --src-token or --src-token-file')
        exit(1)

    if args.dst_token_file is not None:
        with open(args.dst_token_file, 'r') as f:
            dst_token = f.read().strip()
    elif args.dst_token is not None:
        dst_token = args.dst_token
    else:
        print('Must provide either --dst-token or --dst-token-file')
        exit(1)

    src_host = args.src_host
    dst_host = args.dst_host

    if args.delete_all:
        delete_all(dst_host, dst_token)
    else:
        migrate(src_host, src_token, dst_host, dst_token)
