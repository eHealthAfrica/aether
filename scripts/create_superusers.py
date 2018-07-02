#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys

AETHER_DJANGO_MODULES = [
    'kernel',
    'odk',
    'couchdb-sync',
    'ui',
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', dest='username', required=True)
    parser.add_argument(
        '--email',
        dest='email',
        required=False,
        default='test@example.com',
    )
    parser.add_argument('--password', dest='password', required=True)
    parser.add_argument(
        '--services',
        dest='services',
        nargs='+',
        default=AETHER_DJANGO_MODULES,
        required=False,
    )
    args = parser.parse_args()

    for service in args.services:
        cmd = [
            'docker-compose',
            'run',
            service,
            'manage',
            'setup_admin',
            '--username',
            args.username,
            '--email',
            args.email,
            '--password',
            args.password,
        ]
        msg = '\nCreating user "{username}" in service "{service}"...'
        print(msg.format(username=args.username, service=service))
        process = subprocess.run(cmd, stdout=subprocess.PIPE)
        if not process.returncode == 0:
            print(process.stdout.decode('utf-8'))
            sys.exit(1)


if __name__ == '__main__':
    main()
