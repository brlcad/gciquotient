#!/usr/bin/env python3

import os
import sys
import argparse
import json
import time
from fnmatch import fnmatch

import requests

import client as gciclient

argparser = argparse.ArgumentParser(description='GCI Tasks')
argparser.add_argument('--apikey', type=str, nargs='?', required=True,
                       help='api key')
argparser.add_argument('--url', type=str, nargs='?',
                       default='https://codein.withgoogle.com',
                       help='server url')
argparser.add_argument('--datadir', type=str, nargs='?',
                       default='gci_data',
                       help='directory in which to store all downloaded data')
FLAGS = argparser.parse_args()

INSTANCE_THROTTLE = 1


def read_task(task_dir, task_file):
    file_path = os.path.join(task_dir, task_file)
    # print("\t@ %s" % file_path)
    with open(file_path, 'r') as infile:
        return json.load(infile)


def get_tasks(task_dir):
    all_tasks = []
    print('...reading tasks...', end='')
    sys.stdout.flush()
    for file in os.listdir(task_dir):
        if fnmatch(file, '*.json'):
            all_tasks.extend([read_task(task_dir, file)])
    print('done! (%lu tasks)' % len(all_tasks))
    return all_tasks


def make_tasks(datadir, client):
    taskdir = os.path.join(datadir, 'tasks')
    tasks = get_tasks(taskdir)

    print('...submitting tasks to GCI [%s]' % taskdir, end='')
    sys.stdout.flush()
    for t in tasks:
        submit_task(t, client)
        print('.', end='')
        sys.stdout.flush()
    print('done!')


def submit_task(task, client):
    # GCI API will err out if "max_instances" is set to 0, even if it
    # is possible to set it to 0 in the interface.
    if not task.get('max_instances'):
        task['max_instances'] = 1
    try:
        return client.NewTask(task)
    except requests.exceptions.HTTPError as e:
        from pprint import pprint
        pprint(task)
        pprint(e.response.text)
        raise

def main():
    print("GCI Product: noun | gē-sē-ī prŏd-əkt")
    print(" \"the triviality of a specified characteristic or quality\"")

    client = gciclient.GCIAPIClient(
        auth_token=FLAGS.apikey,
        url_prefix=FLAGS.url)

    if not os.path.isdir(FLAGS.datadir):
        print('...data directory does not exist! [%s]' % FLAGS.datadir)
        exit(1)
    else:
        print('...reading GCI task data from [%s]' % FLAGS.datadir)

    make_tasks(FLAGS.datadir, client)

if __name__ == '__main__':
    main()

