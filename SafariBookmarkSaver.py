from urllib.request import Request, urlopen
from functools import cmp_to_key
import plistlib
import subprocess
import os
import re
from shutil import copy
import argparse
import time
import sys
import json

global idKey
idKey = 0
global breakerCount
breakerCount = 0

def main(in_source, in_destination, is_verbose, save_json_flag):
	output_type_full = is_verbose

	bookmarks_path_short = '~/Library/Safari/Bookmarks.plist'
	bookmarks_path = os.path.expanduser(bookmarks_path_short)
	save_to_folder =os.path.expanduser(in_destination)

	if not os.path.isdir(os.path.dirname(save_to_folder)):
		print('The folder',os.path.dirname(save_to_folder),'does not exist, please check destination')
		quit()

	global idKey
	global breakerCount

	with open(bookmarks_path, 'rb') as fp:
	    pl = plistlib.load(fp)
	    full_bookmarks_menu = [item for item in pl['Children'] if 'Title' in item 
	    and item['Title'] == 'BookmarksMenu'][0]
	    bookmarks_menu = full_bookmarks_menu['Children']
	    reduced_list = [item for item in bookmarks_menu if 'Title' in item and item['Title'] == in_source]

	if len(reduced_list) == 0:
		print('The selected folder is empty or does not exists please check source')
		quit()

	if save_json_flag:
		json_dict = []
		final_json = get_json(reduced_list, json_dict)
		sorted_json = sort_output(final_json[0]['children'])
		with open('foodData.json','w+') as f:
			json.dump(sorted_json,f, indent=2, separators=(',', ': '))

	else:
		bookmarks_dict = {}
		print('---- Finding All Bookmarks & Files ----')
		recursive_search(reduced_list, save_to_folder, bookmarks_dict)
		files_present = folder_search(save_to_folder)
		print(len(bookmarks_dict),'Bookmarks found.')
		
		print('---- Reducing Bookmarks ----')
		reduced_bookmarks_dict = reduce_dictionary(bookmarks_dict, files_present)
		print(len(reduced_bookmarks_dict), 'Bookmarks to save.')
		
		print('---- Updating File Locations ----')
		updated_bookmarks_dict = moved_bookmarks(reduced_bookmarks_dict, files_present)
		
		print('\n---- Deleting Old Files ----')
		files_present = folder_search(save_to_folder)
		identify_deleted_bookmarks(bookmarks_dict, files_present)

		print('---- Saving New Bookmarks ----')
		all_name_store = [] #used in check saved Bookmarks
		tried_shell_commands = [] #
		tried_name_store = [] #
		loop_and_save_bookmarks(updated_bookmarks_dict, all_name_store, tried_name_store, tried_shell_commands)

		print('\n---- Finishing ----')
		failed_name_store = [] # used in check saved Bookmarks
		succeeded_name_store = [] # used in check saved Bookmarks
		check_saved_bookmarks(all_name_store, succeeded_name_store, failed_name_store)
		write_tester_to_file(all_name_store, tried_shell_commands, failed_name_store, succeeded_name_store, tried_name_store, output_type_full)

def recursive_search(in_dict, in_string, out_dict):
	#recursively search through plist data, if a child exists the entry is a folder and must be searched
	#if a child does not exist store the entry
	global idKey
	for a_child in in_dict:
		if 'Children' in a_child:
			temp_string = in_string + '/' + a_child['Title']
			recursive_search(a_child['Children'], temp_string, out_dict)
		else:
			# remove everything from url after the query string 
			if 'URLString' in a_child:
				temp_url_string = a_child['URLString']
				reduced_url_string = re.sub('\?.*$', '', temp_url_string)
				file_name = re.sub('[^A-Za-z0-9/\s]+', '', a_child['URIDictionary']['title'])
				temp_entry = {'folder': in_string, 'file_name': file_name,'URL': reduced_url_string}
				out_dict[idKey] = temp_entry
				idKey = idKey + 1

def get_json(in_dict, in_json):

	for a_child in in_dict:
		if 'Children' in a_child:
			temp_string = a_child['Title']
			in_json.append({'name':temp_string, 'children':get_json(a_child['Children'], []), 'active': False, 'toggled': False})

		else:
			# remove everything from url after the query string 
			if 'URLString' in a_child:
				reduced_url_string = re.sub('\?.*$', '', a_child['URLString'])
				file_name = re.sub('[^A-Za-z0-9/\s]+', '', a_child['URIDictionary']['title'])
				in_json.append({'name':file_name,'url':reduced_url_string,'notes':'', 'active': False, 'toggled': True})

	return(in_json)

def sort_output(in_json):
	sort_func_py3 = cmp_to_key(sort_func)
	sorted_level = sorted(in_json,key = sort_func_py3)
	for index, item in enumerate(sorted_level):		
		if 'children' in item:
			result = sort_output(item['children'])
			sorted_level[index]['children'] = result
	return sorted_level

def sort_func(input1, input2):
	if 'children' in input1 and 'children' in input2:
		if input1['name'].lower() > input2['name'].lower():
			return 1 
		elif input1['name'].lower() == input2['name'].lower():
			return 0 
		else:
			return -1
	elif 'children' in input1:
		return -1
	elif 'children' in input2:
		return 1
	else:
		if input1['name'].lower() > input2['name'].lower():
			return 1 
		elif input1['name'].lower() == input2['name'].lower():
			return 0 
		else:
			return -1

def folder_search(in_root):
	#return dictionary of file/folder structure for the destination folder
	identified_files = {}
	for root, _, files in os.walk(in_root, topdown=False):
		for name in files:
			if name != '.DS_Store':
				identified_files[os.path.join(root, name)] = name
	return identified_files

def reduce_dictionary(in_bookmarks, in_files):
	#compare dictionary of bookmarks to dictionary of destination files
	#return dictionary of bookmarks which do not exist in the destination
	out_bookmarks = dict(in_bookmarks)
	for key, entry in in_bookmarks.items():
		full_file_path = entry['folder'] + '/' + entry['file_name'] + '-full.png'
		if full_file_path in in_files:
			del out_bookmarks[key]
	return out_bookmarks

def moved_bookmarks(in_bookmarks, in_files):
	tracker = 1
	#check dictionary of bookmarks against destination files
	#if a missing bookmark exists in a different folder, copy it to destination location
	out_bookmarks = dict(in_bookmarks)
	for key, entry in in_bookmarks.items():
		sys.stdout.write('\rAttempting to find bookmark {} in existing Files'.format(tracker))
		sys.stdout.flush()
		test_string = entry['file_name'] + '-full.png'
		for key2, value in in_files.items():
			destination = entry['folder']+'/'+entry['file_name'] +'-full.png'
			#check filename of missing against all other filenames
			# if a match is found and it is not of the same location copy
			#file and remove from dictionary of bookmarks
			if (test_string == value and key2 != destination):
				if not os.path.isdir(entry['folder']):
					os.mkdir(entry['folder'])
				copy(key2, destination)
				del out_bookmarks[key]
				break
		tracker += 1
		time.sleep(0.1)
	return out_bookmarks

def identify_deleted_bookmarks(in_bookmarks, in_files):
	#compare all current files against all current bookmarks, if present in files and not
	#bookmarks delete file at that path
	for key, entry in in_files.items():
		present_flag = 0
		for key2, value in in_bookmarks.items():
			test_string = value['folder']+'/'+value['file_name']+'-full.png'
			if key == test_string:
				present_flag = 1
		if present_flag == 0:
			os.remove(key)

def save_site_as_picture(in_link, in_filename,in_tried_shell_commands):
	#take file name path and link and add arguments to shell commands pointer
	link = in_link + " "
	width = "--width=1280 "
	im_size = "-F "
	ignore_ssl = "--ignore-ssl-check "
	file_name = "-o " + "\'" + in_filename + "\'"
	if link.startswith("https"):
		argstring = "webkit2png " + link + width + "--delay=10 " +im_size + file_name
	else:
		argstring = "webkit2png " + ignore_ssl + link + width + "--delay=15 " +im_size + file_name
	in_tried_shell_commands.append(argstring)
	subprocess.run(argstring, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def write_tester_to_file(in_tried, in_args, in_failed, in_succeed, in_a_tried, in_output_type):
	#save outputs to txt files for easier checking
	a = "All Bookmarks.txt"
	b = "Shellargs.txt"
	c = "Bookmarks Failed.txt"
	d = "bookmarks Succeeded.txt"
	e = "Tried Bookmarks.txt"
	if in_output_type:
		with open(a, mode = 'wt' ) as myFile:
			for entry in in_tried:
				#myFile.write(str(entry['fileName']))
				myFile.write(str(entry))
				myFile.write('\n')
		with open(d, mode = 'wt' ) as myFile:
			for entry in in_succeed:
				myFile.write(str(entry))
				myFile.write('\n')
		with open(e, mode = 'wt' ) as myFile:
			for entry in in_a_tried:
				myFile.write(str(entry))
				myFile.write('\n')
		with open(b, mode = 'wt') as myFile:
			print("\n\n")
			for entry in in_args:
				entry = entry.replace(u'\xa0', u' ')
				myFile.write(entry)
				myFile.write('\n')
	with open(c, mode = 'wt' ) as myFile:
		for entry in in_failed:
			myFile.write(str(entry))
			myFile.write('\n')

def check_saved_bookmarks(in_attempts, out_succeed, out_failed):
	#Loop through attemped bookmarks and check for file existence, return succeeded and failed
	for entry in in_attempts:
		if os.path.isfile(entry["file_name"]+"-full.png"):
			out_succeed.append(entry)
		else:
			out_failed.append(entry)

def loop_and_save_bookmarks(in_bookmark_dict, out_all_store , out_attempted_store, out_attempted_args ):
	url_list = {}
	tracker = 1
	total = len(in_bookmark_dict)
	for key, entry in in_bookmark_dict.items():
		sys.stdout.write('\rAttempting to save bookmark {} of {}'.format(tracker,total))
		sys.stdout.flush()
		#Remove unsafe characters from web titles and create a full file path and
		#append to to storage dictionary checkers
		folder_path = entry['folder']
		end = '/' + entry['file_name']
		full_string = folder_path + end
		entry['file_name'] = full_string
		out_all_store.append(entry)

		if entry['URL'] in url_list:
			try:
				if not os.path.isdir(folder_path):
					os.mkdir(folder_path)
				copy(url_list[entry['URL']], folder_path)
			except:
				out_attempted_store.append(entry)
				req = Request(entry['URL'], headers={'User-Agent': 'Mozilla/5.0'})
				try:
					request_code = urlopen(req).getcode()
					if request_code == 200:
						save_site_as_picture(entry['URL'], full_string,out_attempted_args)
				except:
					pass
		else:
			full_file_path = full_string + "-full.png"
			#check for existence of file and folder, pass if file already saved or create file and 
			#folder
			if os.path.isdir(folder_path):
				out_attempted_store.append(entry)
				req = Request(entry['URL'], headers={'User-Agent': 'Mozilla/5.0'})
				try:
					request_code = urlopen(req).getcode()
					if request_code == 200:
						save_site_as_picture(entry['URL'], full_string,out_attempted_args)
						url_list[entry['URL']] = full_file_path
				except:
					#logg HTTP error if needed
					pass
			else:
				os.makedirs(folder_path)
				out_attempted_store.append(entry)
				req = Request(entry['URL'], headers={'User-Agent': 'Mozilla/5.0'})
				try:
					request_code = urlopen(req).getcode()
					if request_code == 200:
						save_site_as_picture(entry['URL'], full_string,out_attempted_args)
						url_list[entry['URL']] = full_file_path
				except:
					#logg HTTP error if needed
					pass
		tracker += 1

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='Save Safari Bookmarks.')
	parser.add_argument("-v","--verbose", help="Store all descriptor files - default false results in only a description of failed files",action="store_true")
	parser.add_argument("-d", "--destination", type=str, help="Location to save output files. Please provide only from after the /Users/aUser folder")
	parser.add_argument("-s", "--source", type=str, help="Subfolder of bookmarks to save")
	parser.add_argument("-j","--json", help="Store only JSON store of files - default false",action="store_true")

	args = parser.parse_args()
	# add a ~/ to the front if required
	destination = args.destination
	source = args.source
	
	if destination:
		if destination[0] != '~':
			if destination[0] != '/':
				destination = '~/' + destination
			elif destination[0] == '/':
				destination = '~' + destination
	else:
		#Enter title of destination folder you wish to save here if not using CLI
		destination = '~/OneDrive/Food Save'

	if source:
		pass
	else:
		#Enter title of bookmark folder you wish to save here if not using CLI
		source = 'Cooking'

	main(source, destination, args.verbose, args.json)
