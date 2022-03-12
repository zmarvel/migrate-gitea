import requests
import json
from argparse import ArgumentParser
import logging


def get(host, path, params=None, headers=None):
    url = f'{host}/api/v1/{path}'
    logging.debug(f'GET {url}')
    response = requests.get(url, headers=headers, params=params)
    json_content = json.loads(response.content)
    return json_content


def delete(host, path, params=None, headers=None):
    url = f'{host}/api/v1/{path}'
    logging.debug(f'DELETE {url}')
    response = requests.delete(url, headers=headers, params=params)
    return response
    # json_content = json.loads(response.content)
    # return json_content


def post(host, path, **kwargs):
    url = f'{host}/api/v1/{path}'
    logging.debug(f'POST url={url} {kwargs}')
    response = requests.post(url, **kwargs)
    return response


def migrate(src_host, src_token, dst_host, dst_token):
    src_headers = {'Authorization': f'token {src_token}'}
    dst_headers = {'Authorization': f'token {dst_token}'}
    # Get user ids
    src_user = get(src_host, 'user', headers=src_headers)
    print(src_user)
    src_uid = src_user['id']
    src_login = src_user['login']
    dst_uid = get(dst_host, 'user', headers=dst_headers)['id']
    logging.info('src_uid=%d src_login=%s dst_uid=%d', src_uid, src_login,
                 dst_uid)

    src_repos = get(src_host,
                    f'users/{src_login}/repos',
                    headers=src_headers,
                    params={'uid': src_uid})
    for repo in src_repos:
        repo_addr = f'{src_host}/{repo["full_name"]}.git'
        logging.info('src_addr=%s', repo_addr)
        response = post(dst_host,
                        'repos/migrate',
                        headers=dst_headers,
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
                            'service': 'gitea',
                            'private': repo['private'],
                        })
        logging.info('response_status=%d response_content=%s',
                     response.status_code, response.content)
        response.raise_for_status()

        # migrate issues

        # migrate releases

        # TODO: migreate pull requests


def delete_all(host, token):
    auth_headers = {'Authorization': f'token {token}'}
    user = get(host, 'user', headers=auth_headers)
    uid = user['id']

    repos = get(host,
                'repos/search',
                headers=auth_headers,
                params={'uid': uid})['data']

    for repo in repos:
        response = delete(host,
                          f'repos/{user["login"]}/{repo["name"]}',
                          headers=auth_headers)
        print(response.status_code)
        print(response.content)
        response.raise_for_status()


if __name__ == '__main__':

    parser = ArgumentParser(
        description='Migrate from one gitea instance to another')

    parser.add_argument('--src-token', help='Source API token')
    parser.add_argument('--src-token-file',
                        help='File containing source API token')
    # parser.add_argument('--src-user', help='Migrate repos for only this user')

    parser.add_argument('--dst-token', help='Destination API token')
    parser.add_argument('--dst-token-file',
                        help='File containing destination API token')
    # parser.add_argument('--dst-user',
    #                     help='Create migrated repos under this user')

    # TODO move to a separate script
    parser.add_argument('--delete-all',
                        action='store_true',
                        help='Instead of migrating, delete all repos')

    parser.add_argument('--debug',
                        action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--verbose',
                        action='store_true',
                        help='Enable verbose logging')

    parser.add_argument('src_host',
                        help='Address (and optionally port) of source host')
    parser.add_argument(
        'dst_host', help='Address (and optionally port) of destination host')

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

    log_level = logging.WARNING
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    logging.getLogger().setLevel(log_level)

    src_host = args.src_host
    if not src_host.startswith('http'):
        src_host = f'http://{src_host}'

    dst_host = args.dst_host
    if not dst_host.startswith('http'):
        dst_host = f'http://{dst_host}'

    if args.delete_all:
        delete_all(dst_host, dst_token)
    else:
        migrate(src_host, src_token, dst_host, dst_token)
