import os
import errno
import argparse
import re
import json
import io
import client as gciclient
import requests
import urlparse
from bs4 import BeautifulSoup

argparser = argparse.ArgumentParser(description='GCI Task Instances')
argparser.add_argument('--apikey', type=str, nargs='?', required=True,
                       help='api key')
argparser.add_argument('--instance', type=str, nargs='?', required=False,
                       help='task instance')
argparser.add_argument('--url', type=str, nargs='?',
                       default='https://codein.withgoogle.com',
                       help='server url')
argparser.add_argument('--debug', action='store_true',
                       help='enable debug request logging')
FLAGS = argparser.parse_args()

TEXT_FILE_NAME = 'task_information.txt'

def sterilize(directory_str):
	forbidden_chars = '/\\.*?<>:|'
	for char in forbidden_chars:
		directory_str = directory_str.replace(char, '_')
	return directory_str

def get_folder_name(instance):
        if instance['completion_date'] == 'None':
                return sterilize('0000-00-00 00_00_00' + '-' + instance['task_definition_name'] + "_-_" + instance['organization_name'])
	return sterilize(instance['completion_date'] + '-' + instance['task_definition_name'] + "_-_" + instance['organization_name'])

def get_prettified_info(instance):
	task_id = instance['id']
	task_def_id = instance['task_definition_id']
	task_name = instance['task_definition_name']
	task_desc = instance['description']
	task_status = instance['status']
	tags = instance['tags']
	max_instances = instance['max_instances']

	org_name = instance['organization_name']
	org_id = instance['organization_id']

	student_id = instance['student_id']
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
	return output

def get_instance_attachments(instance, cookies):
	page = requests.get('https://codein.withgoogle.com/api/program/current/taskupdate/?page=1&page_size=20&task_instance='+instance['id'], cookies=cookies)
	info = json.loads(page.text.encode('utf-8'))
	attachments = []
	for result in info['results']:
		for attachment in result['attachments']:
			url = attachment['url']
			name = attachment['filename']
			attachments += [{'url': 'https://codein.withgoogle.com'+url.encode('utf-8'), 'filename': name}]
	return attachments


def convert_to_utf8(input):
    if isinstance(input, dict):
        return {convert_to_utf8(key): convert_to_utf8(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [convert_to_utf8(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return str(input)

def write_to_folder(instance, cookies):
	info = get_prettified_info(instance)
	folder_name = get_folder_name(instance)
	if FLAGS.debug:
		folder_name = "Debug_" + folder_name
	current_path = os.getcwd()

	folder_path = os.path.join(current_path, folder_name.replace('"', ''))
	text_file_path = os.path.join(folder_path, TEXT_FILE_NAME)

	# Try create folder, catch any errors (e.g. folder already exists)
	try:
	    os.mkdir(folder_path)
	except OSError as e:
	    if e.errno != errno.EEXIST:
	        raise

        print("\t@ %s" % folder_path)

	# Write to description file
	with open(text_file_path, 'w') as outfile:
		outfile.write(info)

	# Download attachments
	attachments = get_instance_attachments(instance, cookies)
        # print(attachments)

	if attachments:
		for attachment in attachments:
			url = attachment['url']
                        urlpath = urlparse.urlparse(url).path
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
# 	else:
# 		print("\tThere are no attachments for task: " + instance['task_definition_name'])
	
def save_task_instances(client, cookies):
	next_page = 1
        count = 0;
	while next_page > 0:
		instances = client.ListTaskInstances(page=next_page)
		for ti in instances['results']:
			task_id = ti['task_definition_id']
			ti = convert_to_utf8(ti)
			task_definition = convert_to_utf8(get_task_definition(client, task_id))
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
                        print('#%05u: %s' % (count, ti['task_definition_name']))
			write_to_folder(ti, cookies)
                        count += 1;
		next_page = 0
		if instances['next']:
			result = re.search(r'page=(\d+)', instances['next'])
			if result:
				next_page = result.group(1)


def get_task_definition(client, task_def_id):
	return client.GetTask(task_def_id)

def debug(cookies, instance_id=5890447643770880):
	test_instance = {
		"status": "COMPLETED",
		"student_display_name": u"da\u00F1iel",
		"program_year": 2016,
		"task_definition_id": 5672905058811904,
		"student_id": 5096715048714240,
		"modified": "2016-11-03 01:51:51",
		"task_definition_name": "Random task name",
		"organization_name": u"\u1234",
		"completion_date": "2016-11-03 01:44:04",
		"deadline": "2016-11-09 01:01:48",
		"organization_id": 5640347044544512,
		"id": instance_id}

	test_definition = {
		'name': u'\u1234',
		'status': 2,
		'description': u'\u1234',
		'mentors': [u'\u1234'],
		'tags': [u'\u1234'],
		'is_beginner': False,
		'categories': [1,2,3],
		'time_to_complete_in_days': 4,
		'max_instances': 5
	}

	task_id = test_instance['task_definition_id']
	test_instance = convert_to_utf8(test_instance)
	test_definition = convert_to_utf8(test_definition)
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
		test_instance[key] = test_definition[key]
	write_to_folder(test_instance, cookies)

def main():
	client = gciclient.GCIAPIClient(
		auth_token=FLAGS.apikey,
	url_prefix=FLAGS.url)
	value = ''
	with open('sacsid_cookie.txt', 'r') as cookie_file:
		for line in cookie_file:
			value = line
			break 
	value = value.replace('\n', '')
	cookies = {
		'SACSID': value
	}
	if FLAGS.debug:
		if FLAGS.instance:
			print(cookies)
			debug(cookies, FLAGS.instance)
		else:
			debug(cookies)
	else:
		save_task_instances(client, cookies)

if __name__ == '__main__':
  main()

