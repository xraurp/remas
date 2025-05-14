#!/usr/bin/env python3
# Script to get Grafana alert by UID
import httpx
import json
import argparse
import getpass
import sys

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--username",
        help="Grafana username",
        required=True
    )
    parser.add_argument(
        "--password",
        help="Grafana password (if not provided, will be prompted)",
        required=False
    )
    parser.add_argument(
        '--alert-uid',
        help='Grafana alert UID',
        required=True
    )
    parser.add_argument(
        '--output-file',
        help='Output file',
        default='alert.json'
    )
    parser.add_argument(
        '--grafana-url',
        help='Grafana URL',
        default='http://localhost:3000'
    )
    return parser.parse_args()

def join_url_path(*args) -> str:
    """
    Joins parts of URL path together.
    :param args: parts of the URL paths to join
    :return (str): joined URL path
    """
    return '/'.join(map(lambda x: str(x).strip('/'), args))

def get_grafana_config(
    path: str,
    grafana_url: str,
    username: str,
    password: str
) -> httpx.Response:
    """
    Gets config from given API path from Grafana.
    :param path (str): path on Grafana instance API
    :param grafana_url (str): Grafana URL
    :param username (str): Grafana username
    :param password (str): Grafana password
    :return (httpx.Response): response
    """
    response = httpx.request(
        method='GET',
        url=join_url_path(grafana_url, path),
        auth=(username, password),
    )
    # Raise error if any
    response.raise_for_status()
    return response

def main():
    args = parse_args()
    password = args.password
    if password is None:
        password = getpass.getpass('Enter Grafana password: ')
    
    path = f'/api/v1/provisioning/alert-rules/{args.alert_uid}'

    response = get_grafana_config(
        path=path,
        grafana_url=args.grafana_url,
        username=args.username,
        password=password
    )
    with open(args.output_file, 'w') as f:
        json.dump(response.json(), f, indent=4)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
