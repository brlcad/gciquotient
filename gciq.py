#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
if sys.version_info[0] >= 3:
	unicode = str
try:
	reload(sys)  # Python 2.7
	sys.setdefaultencoding('utf8')
except NameError:
	pass
import errno
import argparse
import re
import json
import io
import time
try:
	import urlparse as up # Python 2.7
except:
	import urllib.parse as up # Python 3
import requests
import client as gciclient

argparser = argparse.ArgumentParser(description='GCI Task Instances')
argparser.add_argument('--apikey', type=str, nargs='?', required=True,
                       help='api key')
argparser.add_argument('--instance', type=str, nargs='?', required=False,
                       help='download a single task instance')
argparser.add_argument('--url', type=str, nargs='?',
                       default='https://codein.withgoogle.com',
                       help='server url')
argparser.add_argument('--datadir', type=str, nargs='?',
                       default='gci_data',
                       help='directory in which to store all downloaded data')
FLAGS = argparser.parse_args()

INSTANCE_HTML = 'index.html'
INSTANCE_SUMMARY_FILENAME = 'instance.txt'
INSTANCE_FILENAME = 'instance.json'
INSTANCE_ACTIVITY_FILENAME = 'activity.json'
INSTANCE_THROTTLE = 1


def sterilize(directory_str):
	# scrub chars that are a PITA in directory names
	forbidden_chars = '/\\*?<>:|'
	for char in forbidden_chars:
		directory_str = directory_str.replace(char, '_')
	# collapse sequences to a single scrub
	directory_str = re.sub(r'_+', '_', directory_str)
	# substitute non-printable chars and non-ascii
	directory_str = re.sub(r'[^ -~]+', 'X', directory_str)
	# some NAS-encrypted filesystems limit filenames to 144 chars, so stop short
	return (directory_str[:140] + '...') if len(directory_str) > 140 else directory_str


def convert_to_utf8(input):
	if isinstance(input, dict):
		return {convert_to_utf8(key): convert_to_utf8(value) for key, value in input.items()}
	elif isinstance(input, list):
		return [convert_to_utf8(element) for element in input]
	elif isinstance(input, unicode):
		return input
	else:
		return str(input)


def get_task_file_name(task):
	return sterilize(convert_to_utf8(task['id']) + '-' + convert_to_utf8(task['name']).replace('"', '') + '.json')


def write_task(taskdir, task):
	file_name = get_task_file_name(task)
	file_path = os.path.join(taskdir, file_name)
	# print("\t@ %s" % file_path)
	with open(file_path, 'w') as outfile:
		outfile.write(json.dumps(task, indent=4))
	outfile.close()


def get_instance_folder_name(instance):
	if instance['modified'] == 'None':
		instance['modified'] = '0000-00-00 00_00_00'
	task_name = convert_to_utf8(instance['task_definition_name']).replace('"', '')
	return sterilize(convert_to_utf8(instance['modified']) + '-' + convert_to_utf8(instance['id']) + '-' + task_name + "_-_" + convert_to_utf8(instance['organization_name']))


def get_prettified_info(instance):
	task_id = str(instance['id'])
	task_def_id = str(instance['task_definition_id'])
	task_name = instance['task_definition_name']
	task_desc = instance['description']
	task_status = instance['status']
	tags = instance['tags']
	max_instances = instance['max_instances']

	org_name = instance['organization_name']
	org_id = str(instance['organization_id'])

	student_id = str(instance['student_id'])
	student_name = instance['student_display_name']

	mentors = instance['mentors']
	is_beginner = instance['is_beginner']
	categories = instance['categories']
	time_given = instance['time_to_complete_in_days']
	deadline = instance['deadline']
	completion_date = instance['completion_date']
	modified = instance['modified']
	category_names = ['Coding', 'User Interface', 'Documentation & Training', 'Quality Assurance', 'Outreach & Research']

	output = org_name + ' (Org ID ' + org_id + ')' + '\n'
	output += 'Task ID ' + task_id + ' | Task Definition ID ' + task_def_id + '\n'
	output += 'Max instances: ' + max_instances + '\n'
	output += '\n'
	output += 'Title: ' + task_name + '\n'
	output += 'Description: ' + task_desc + '\n'
	output += 'Tags: ' + (', '.join(list(tags))) + '\n'
	output += '\n'
	output += 'Categories: ' + (', '.join(category_names[int(c)-1] for c in categories)) + '\n'
	output += 'Is Beginner: ' + ('Yes' if is_beginner == 'True' else 'No') + '\n'
	output += 'Time given to complete: ' + time_given + ' days' + '\n'
	output += '\n'
	output += 'Mentors: ' + (', '.join(list(mentors))) + '\n'
	output += 'Student: ' + student_name + ' (ID ' + student_id + ')' + '\n'
	output += '\n'
	output += 'Status: ' + task_status + (' (' + deadline + ')' if task_status == 'COMPLETED' else '') + '\n'
	output += 'Last modified: ' + modified + '\n'
	return convert_to_utf8(output)


def get_instance_activity(instance, cookies):
	page = requests.get('https://codein.withgoogle.com/api/program/current/taskupdate/?task_instance=' + str(instance['id']), cookies=cookies)
	info = json.loads(page.text.encode('utf-8'))
	if 'results' in info:
		return info['results']
	print('...WARNING: unknown instance activity result, see ' + INSTANCE_ACTIVITY_FILENAME)
	return info


def get_instance_html(instance, cookies):
	page = requests.get('https://codein.withgoogle.com/dashboard/task-instances/' + str(instance['id']) + '/', cookies=cookies)
	return page.text


def list_instance_attachments(activity):
	attachments = []
	for result in activity:
		for attachment in result['attachments']:
			url = attachment['url']
			name = attachment['filename']
			attachments += [{'url': 'https://codein.withgoogle.com' + url.encode('utf-8'), 'filename': name}]
	return attachments


def write_instance(datadir, instance, cookies):
	folder_name = get_instance_folder_name(instance)
	folder_path = os.path.join(datadir, folder_name)
	try:
		os.mkdir(folder_path)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise

	print("\t@ %s" % folder_path)

	# write a summary text file
	summary_file = os.path.join(folder_path, INSTANCE_SUMMARY_FILENAME)
	info = get_prettified_info(instance)
	with open(summary_file, 'w') as outfile:
		outfile.write(info)
	outfile.close()

	# get the discussion and state changes
	activity = get_instance_activity(instance, cookies)
	activity_file = os.path.join(folder_path, INSTANCE_ACTIVITY_FILENAME)
	with open(activity_file, 'w') as outfile:
		outfile.write(json.dumps(activity, indent=4))
	outfile.close()

	# download attachments
	attachments = list_instance_attachments(activity)
	if attachments:
		for attachment in attachments:
			url = attachment['url']
			urlpath = up.urlparse(url).path
			base = os.path.basename(os.path.dirname(urlpath))
			filename = base + '_' + attachment['filename'].encode('utf-8')
			print('\tgetting ' + filename)
			attachment_path = os.path.join(folder_path, filename)
			file_contents = requests.get(url, cookies=cookies, stream=True)
			# Throw an error for bad status codes
			# file_contents.raise_for_status()
			if file_contents.status_code != 200:
				print('\tWARNING: %s failed' % url)

			with io.open(attachment_path, 'wb') as outfile:
				for block in file_contents.iter_content(1024):
					outfile.write(block)
			outfile.close()

#	 # mark this instance done
#	 html_file = os.path.join(folder_path, INSTANCE_HTML)
#	 html = get_instance_html(instance, cookies)
#	 with open(html_file, 'w') as outfile:
#		 outfile.write(html)
#	 outfile.close()

	# write the raw instance json
	instance_file = os.path.join(folder_path, INSTANCE_FILENAME)
	with open(instance_file, 'w') as outfile:
		outfile.write(json.dumps(instance, indent=4))
	outfile.close()


def get_tasks(datadir, client, cookies):
	all_tasks = []
	next_page = 1
	print('...downloading tasks...', end='')
	sys.stdout.flush()
	while next_page > 0:
		print('.', end='')
		sys.stdout.flush()
		tasks = client.ListTasks(page=next_page)
		time.sleep(INSTANCE_THROTTLE)
		for t in tasks['results']:
			all_tasks.append(t)

		next_page = 0
		if tasks['next']:
			result = re.search(r'page=(\d+)', tasks['next'])
			if result:
				next_page = int(result.group(1))
	print('done! (%lu tasks)' % len(all_tasks))
	return all_tasks


def save_tasks(datadir, client, cookies):
	tasks = get_tasks(datadir, client, cookies)
	taskdir = os.path.join(datadir, 'tasks')
	try:
		os.mkdir(taskdir)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise

	print('...saving GCI tasks to [%s]' % taskdir, end='')
	sys.stdout.flush()
	for t in tasks:
		write_task(taskdir, t)
		print('.', end='')
		sys.stdout.flush()
	print('done!')


def save_instances(datadir, client, cookies):
	instdir = os.path.join(datadir, 'instances')
	try:
		os.mkdir(instdir)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise

	next_page = 1
	count = 0
	print('...saving GCI instances to [%s]' % instdir)
	while next_page > 0:
		instances = client.ListTaskInstances(page=next_page)
		time.sleep(INSTANCE_THROTTLE)
		for ti in instances['results']:
			print('#%05u: %s' % (count, convert_to_utf8(ti['task_definition_name'])))

			# skip instances we already downloaded
			last_file = get_instance_folder_name(ti)
			last_file = os.path.join(instdir, last_file)
			last_file = os.path.join(last_file, INSTANCE_FILENAME)
			if os.path.isfile(last_file) and os.path.getsize(last_file) > 0:
				print('...skipped, already done')
				count += 1
				continue
				
			task_id = ti['task_definition_id']
			task_definition = convert_to_utf8(client.GetTask(task_id))
			# print(task_definition)
			time.sleep(INSTANCE_THROTTLE)
			useful_info = [
				'description',
				'max_instances',
				'tags',
				'mentors',
				'is_beginner',
				'categories',
				'time_to_complete_in_days'
				]
			for key in useful_info:
				ti[key] = task_definition[key]

			write_instance(instdir, ti, cookies)
			count += 1
		next_page = 0
		if instances['next']:
			result = re.search(r'page=(\d+)', instances['next'])
			if result:
				next_page = int(result.group(1))


def main():
	print("GCI Quotient: noun | gē-sē-ī kwō-shənt")
	print(" \"the magnitude of a specified characteristic or quality\"")

	client = gciclient.GCIAPIClient(
		auth_token=FLAGS.apikey,
		url_prefix=FLAGS.url)
	value = ''
	with open('sacsid_cookie.txt', 'r') as cookie_file:
		for line in cookie_file:
			value = line
			break
	cookie_file.close()

	value = value.replace('\n', '')
	cookies = {
		'SACSID': value
		}

	try:
		os.mkdir(FLAGS.datadir)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise

	if os.path.isdir(FLAGS.datadir):
		print('...saving GCI data to [%s]' % FLAGS.datadir)

	save_tasks(FLAGS.datadir, client, cookies)
	save_instances(FLAGS.datadir, client, cookies)

if __name__ == '__main__':
	main()

