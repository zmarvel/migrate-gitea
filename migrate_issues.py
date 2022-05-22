from typing import List, Optional

from argparse import ArgumentParser
import logging
from pprint import pprint

from migrator import CommonArgs, Server, migrate


def migrate_issues(src_host,
                   src_token,
                   dst_host,
                   dst_token,
                   repo: str,
                   skip: Optional[List[int]] = None):
    if skip is None:
        skip = []

    src_server = Server(src_host, src_token)
    src_user = src_server.get_user()

    dst_server = Server(dst_host, dst_token)
    dst_user = src_server.get_user()

    src_issues = list(
        src_server.get_issues(src_user['login'], repo, state='all'))
    pprint(src_issues)

    src_issues.sort(key=lambda issue: issue['number'])

    for issue in src_issues:
        if issue['number'] in skip:
            print(f'Skipping issue \'{issue["title"]}\' ({issue["number"]})')
            continue
        print(f'Create issue \'{issue["title"]}\' ({issue["number"]})')
        dst_server.post_issue(dst_user['login'], repo, issue['title'],
                              issue['body'], issue['closed_at'] is not None)


def delete_all_issues(dst_host, dst_token, repo):
    # TODO
    pass


def main():
    parser = ArgumentParser()

    CommonArgs.add_to_parser(parser)

    parser.add_argument('--repo', required=True)
    parser.add_argument('--skip',
                        default='',
                        help='Comma-separated list of issue numbers to skip.')

    parser.add_argument('--delete-all', action='store_true')

    args = parser.parse_args()
    common_args = CommonArgs.from_args(args)

    log_level = logging.WARN
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    logging.getLogger().setLevel(log_level)

    if args.delete_all:
        delete_all_issues(common_args.dst_host, common_args.dst_token,
                          args.repo)
    else:
        migrate_issues(common_args.src_host,
                       common_args.src_token,
                       common_args.dst_host,
                       common_args.dst_token,
                       args.repo,
                       skip=[int(x) for x in args.skip.split(',') if x != ''])


if __name__ == '__main__':
    main()
