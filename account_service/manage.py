import sys

import account_service.service as srv


def create_tables(*args):
    srv.configure()
    srv.create_tables()


def runtests(*args):
    import pytest
    import os
    root_dir = os.path.dirname(os.path.dirname(srv.__file__))
    pytest.main(list(args) + [root_dir])


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 0:
        print(f'Command required')
        exit(0)

    command = args[0].lower()
    args = args[1:]

    if command == 'createtables':
        create_tables(*args)
    if command == 'runtests':
        runtests(*args)
    else:
        print(f'Unknown command: {command}')
        exit(1)
