from dataclasses import dataclass
from turtle import st
import requests
import json
from argparse import ArgumentError, ArgumentParser
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


def post(host, path, **kwargs):
    url = f'{host}/api/v1/{path}'
    logging.debug(f'POST url={url} {kwargs}')
    response = requests.post(url, **kwargs)
    return response


def migrate(src_host, src_token, dst_host, dst_token):
    src_headers = get_headers(src_token)
    dst_headers = get_headers(dst_token)
    # Get user ids
    src_user = get_user(src_host, headers=src_headers)
    src_uid = src_user['id']
    src_login = src_user['login']
    dst_uid = get_user(dst_host, headers=dst_headers)['id']
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


class Server:

    def __init__(self, host: str, token: str):
        self.token = token
        self.host = host
        self._headers = {'Authorization': f'token {self.token}'}

    def get_user(self, **kwargs):
        response = self.get('user', **kwargs)
        print(f'response: {response}')
        return response

    @property
    def headers(self):
        return self._headers

    def _add_headers_to_kwargs(self, kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers'].update(self.headers)

    def get(self, path, **kwargs):
        self._add_headers_to_kwargs(kwargs)

        url = f'{self.host}/api/v1/{path}'
        logging.debug('GET %s', url)
        response = requests.get(url, **kwargs)
        logging.debug('response=%s', response)
        json_content = json.loads(response.content)
        return json_content

    def delete(self, path, **kwargs):
        self._add_headers_to_kwargs(kwargs)

        url = f'{self.host}/api/v1/{path}'
        logging.debug(f'DELETE {url}')
        response = requests.delete(url, **kwargs)
        return response

    def post(self, path, **kwargs):
        self._add_headers_to_kwargs(kwargs)

        url = f'{self.host}/api/v1/{path}'
        logging.debug(f'POST url={url} {kwargs}')
        response = requests.post(url, **kwargs)
        return response

    def get_issues(self, user: str, repo: str, state: str = 'open'):
        """Get issues associated with a user's repository.

        Arguments:
            user: Username of repository owner.
            repo: Repository name.
            state: One of (closed, open, all).
        """
        return self.get(f'repos/{user}/{repo}/issues', params={'state': state})

    def post_issue(self, user: str, repo: str, title: str, body: str,
                   closed: bool):
        """Add an issue to a user's repository.

        Arguments:
            user: Username of repository owner.
            repo: Repository name.
        """

        data = {
            'title': title,
            'body': body,
            'closed': closed,
        }
        logging.debug('Post issue %s', data)
        response = self.post(f'repos/{user}/{repo}/issues',
                             data=json.dumps(data),
                             headers={'Content-Type': 'text/json'})
        logging.debug('response=%s text=%s', response, response.text)


@dataclass
class CommonArgs:
    src_token: str
    dst_token: str

    src_host: str
    dst_host: str

    debug: bool
    verbose: bool

    @staticmethod
    def add_to_parser(parser: ArgumentParser):
        parser.add_argument('--src-token', help='Source API token')
        parser.add_argument('--src-token-file',
                            help='File containing source API token')
        # parser.add_argument('--src-user', help='Migrate repos for only this user')

        parser.add_argument('--dst-token', help='Destination API token')
        parser.add_argument('--dst-token-file',
                            help='File containing destination API token')
        # parser.add_argument('--dst-user',
        #                     help='Create migrated repos under this user')

        parser.add_argument('--debug',
                            action='store_true',
                            help='Enable debug logging')
        parser.add_argument('--verbose',
                            action='store_true',
                            help='Enable verbose logging')

        parser.add_argument(
            'src_host', help='Address (and optionally port) of source host')
        parser.add_argument(
            'dst_host',
            help='Address (and optionally port) of destination host')

    @classmethod
    def from_args(cls, args):
        if args.src_token_file is not None:
            with open(args.src_token_file, 'r') as f:
                src_token = f.read().strip()
        elif args.src_token is not None:
            src_token = args.src_token
        else:
            raise ValueError(
                'Must provide either --src-token or --src-token-file')

        if args.dst_token_file is not None:
            with open(args.dst_token_file, 'r') as f:
                dst_token = f.read().strip()
        elif args.dst_token is not None:
            dst_token = args.dst_token
        else:
            raise ValueError(
                'Must provide either --dst-token or --dst-token-file')

        # TODO: consider using a library to normalize urls
        src_host = args.src_host
        if not src_host.startswith('http'):
            src_host = f'http://{src_host}'

        dst_host = args.dst_host
        if not dst_host.startswith('http'):
            dst_host = f'http://{dst_host}'

        return cls(src_token=src_token,
                   dst_token=dst_token,
                   src_host=src_host,
                   dst_host=dst_host,
                   debug=args.debug,
                   verbose=args.verbose)


if __name__ == '__main__':

    parser = ArgumentParser(
        description='Migrate from one gitea instance to another')

    # TODO move to a separate script
    parser.add_argument('--delete-all',
                        action='store_true',
                        help='Instead of migrating, delete all repos')

    args = parser.parse_args()
    common_args = CommonArgs.from_args(args)

    log_level = logging.WARNING
    if common_args.debug:
        log_level = logging.DEBUG
    elif common_args.verbose:
        log_level = logging.INFO
    logging.getLogger().setLevel(log_level)

    if args.delete_all:
        delete_all(common_args.dst_host, common_args.dst_token)
    else:
        migrate(common_args.src_host, common_args.src_token,
                common_args.dst_host, common_args.dst_token)
