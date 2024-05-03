#!/usr/bin/env python3

import argparse
import os
import requests
import json
import sys

def parse_args():
    parser = argparse.ArgumentParser(description='Download state files from Scalr')
    parser.add_argument('--output-dir', '-o', required=True, type=str, help='Output directory')
    parser.add_argument('--host', '-d', type=str, default=os.getenv('SCALR_HOST'), help='Scalr host')
    parser.add_argument('--token', '-t', type=str, default=os.getenv('SCALR_TOKEN'), help='Scalr API token')
    return parser.parse_args()

def setup_headers(token):
    return {
        "accept": "application/vnd.api+json",
        "Prefer": "profile=preview",
        "authorization": "Bearer " + token
    }

def get_workspace_data(session, host, headers, page):
    url = f"https://{host}/api/iacp/v3/workspaces?page[number]={page}"
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError("Request failed. Wrong token?")
    return json.loads(response.text)

def download_state_files(session, host, headers, output_dir, workspace_data):
    for item in workspace_data['data']:
        state_url = f"https://{host}/api/iacp/v3/workspaces/{item['id']}/current-state-version"
        response = session.get(state_url, headers=headers)
        state_data = json.loads(response.text)

        try:
            download_link = state_data['data']['links']['download']
        except KeyError:
            continue

        print(f"Downloading state file for {item['id']} to {output_dir}")
        file_response = session.get(download_link)
        file_path = os.path.join(output_dir, f"{item['id']}.json")
        with open(file_path, "wb") as f:
            f.write(file_response.content)

def main():
    args = parse_args()
    headers = setup_headers(args.token)

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    with requests.Session() as session:
        page = 1
        while True:
            workspace_data = get_workspace_data(session, args.host, headers, page)
            download_state_files(session, args.host, headers, args.output_dir, workspace_data)

            pagination = workspace_data.get('meta', {}).get('pagination', {})
            total_pages = pagination.get('total-pages', 1)  # Assume there is at least one page if missing

            if page == total_pages:
                break
            page += 1

if __name__ == '__main__':
    main()
