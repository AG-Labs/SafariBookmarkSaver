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

def main(inSource, inDestination, isVerbose, saveJSONFlag):
	outputTypeFull = isVerbose

	bookmarksPathShort = '~/Library/Safari/Bookmarks.plist'
	bookmarksPath = os.path.expanduser(bookmarksPathShort)
	saveToFolder =os.path.expanduser(inDestination)

	if not os.path.isdir(os.path.dirname(saveToFolder)):
		print('The folder',os.path.dirname(saveToFolder),'does not exist, please check destination')
		quit()

	global idKey
	global breakerCount

	with open(bookmarksPath, 'rb') as fp:
	    pl = plistlib.load(fp)
	    fullBookmarksMenu = [item for item in pl['Children'] if 'Title' in item 
	    and item['Title'] == 'BookmarksMenu'][0]
	    bookmarksMenu = fullBookmarksMenu['Children']
	    reducedList = [item for item in bookmarksMenu if 'Title' in item and item['Title'] == inSource]

	if len(reducedList) == 0:
		print('The selected folder is empty or does not exists please check source')
		quit()

	if saveJSONFlag:
		JSONDict = []
		finalJSON = getJSON(reducedList, JSONDict)
		sortedJSON = sortOutput(finalJSON[0]['children'])
		with open('foodData.json','w+') as f:
			json.dump(sortedJSON,f, indent=2, separators=(',', ': '))

	else:
		bookmarksDict = {}
		print('---- Finding All Bookmarks & Files ----')
		recursiveSearch(reducedList, saveToFolder, bookmarksDict)
		filesPresent = folderSearch(saveToFolder)
		print(len(bookmarksDict),'Bookmarks found.')
		
		print('---- Reducing Bookmarks ----')
		reducedBookmarksDict = reduceDictionary(bookmarksDict, filesPresent)
		print(len(reducedBookmarksDict), 'Bookmarks to save.')
		
		print('---- Updating File Locations ----')
		updatedBookmarksDict = movedBookmarks(reducedBookmarksDict, filesPresent)
		
		print('\n---- Deleting Old Files ----')
		filesPresent = folderSearch(saveToFolder)
		identifyDeletedBookmarks(bookmarksDict, filesPresent)

		print('---- Saving New Bookmarks ----')
		allNameStore = [] #used in check saved Bookmarks
		triedShellCommands = [] #
		triedNameStore = [] #
		loopAndSaveBookmarks(updatedBookmarksDict, allNameStore, triedNameStore, triedShellCommands)

		print('\n---- Finishing ----')
		failedNameStore = [] # used in check saved Bookmarks
		succeededNameStore = [] # used in check saved Bookmarks
		checkSavedBookmarks(allNameStore, succeededNameStore, failedNameStore)
		writeTesterToFil(allNameStore, triedShellCommands, failedNameStore, succeededNameStore, triedNameStore, outputTypeFull)

def recursiveSearch(inDict, inString, outDict):
	#recursively search through plist data, if a child exists the entry is a folder and must be searched
	#if a child does not exist store the entry
	global idKey
	for aChild in inDict:
		if 'Children' in aChild:
			tempString = inString + '/' + aChild['Title']
			recursiveSearch(aChild['Children'], tempString, outDict)
		else:
			# remove everything from url after the query string 
			if 'URLString' in aChild:
				tempURLString = aChild['URLString']
				reducedURLString = re.sub('\?.*$', '', tempURLString)
				fileName = re.sub('[^A-Za-z0-9/\s]+', '', aChild['URIDictionary']['title'])
				tempEntry = {'folder': inString, 'fileName': fileName,'URL': reducedURLString}
				outDict[idKey] = tempEntry
				idKey = idKey + 1

def getJSON(inDict, inJSON):

	for aChild in inDict:
		if 'Children' in aChild:
			tempString = aChild['Title']
			inJSON.append({'name':tempString, 'children':getJSON(aChild['Children'], []), 'active': False, 'toggled': False})

		else:
			# remove everything from url after the query string 
			if 'URLString' in aChild:
				reducedURLString = re.sub('\?.*$', '', aChild['URLString'])
				fileName = re.sub('[^A-Za-z0-9/\s]+', '', aChild['URIDictionary']['title'])
				inJSON.append({'name':fileName,'url':reducedURLString,'notes':'', 'active': False, 'toggled': True})

	return(inJSON)

def sortOutput(inJSON):
	sortFunc_py3 = cmp_to_key(sortFunc)
	sortedLevel = sorted(inJSON,key = sortFunc_py3)
	for index, item in enumerate(sortedLevel):		
		if 'children' in item:
			result = sortOutput(item['children'])
			sortedLevel[index]['children'] = result
	return sortedLevel

def sortFunc(input1, input2):
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

def folderSearch(inRoot):
	#return dictionary of file/folder structure for the destination folder
	identifiedFiles = {}
	for root, _, files in os.walk(inRoot, topdown=False):
		for name in files:
			if name != '.DS_Store':
				identifiedFiles[os.path.join(root, name)] = name
	return identifiedFiles

def reduceDictionary(inBookmarks, inFiles):
	#compare dictionary of bookmarks to dictionary of destination files
	#return dictionary of bookmarks which do not exist in the destination
	outBookmarks = dict(inBookmarks)
	for key, entry in inBookmarks.items():
		fullFilePath = entry['folder'] + '/' + entry['fileName'] + '-full.png'
		if fullFilePath in inFiles:
			del outBookmarks[key]
	return outBookmarks

def movedBookmarks(inBookmarks, inFiles):
	tracker = 1
	#check dictionary of bookmarks against destination files
	#if a missing bookmark exists in a different folder, copy it to destination location
	outBookmarks = dict(inBookmarks)
	for key, entry in inBookmarks.items():
		sys.stdout.write('\rAttempting to find bookmark {} in existing Files'.format(tracker))
		sys.stdout.flush()
		testString = entry['fileName'] + '-full.png'
		for key2, value in inFiles.items():
			destination = entry['folder']+'/'+entry['fileName'] +'-full.png'
			#check filename of missing against all other filenames
			# if a match is found and it is not of the same location copy
			#file and remove from dictionary of bookmarks
			if (testString == value and key2 != destination):
				if not os.path.isdir(entry['folder']):
					os.mkdir(entry['folder'])
				copy(key2, destination)
				del outBookmarks[key]
				break
		tracker += 1
		time.sleep(0.1)
	return outBookmarks

def identifyDeletedBookmarks(inBookmarks, inFiles):
	#compare all current files against all current bookmarks, if present in files and not
	#bookmarks delete file at that path
	for key, entry in inFiles.items():
		presentFlag = 0
		for key2, value in inBookmarks.items():
			testSting = value['folder']+'/'+value['fileName']+'-full.png'
			if key == testSting:
				presentFlag = 1
		if presentFlag == 0:
			os.remove(key)

def saveSiteAsPicture(inLink, inFilename,inTriedShellCommands):
	#take file name path and link and add arguments to shell commands pointer
	link = inLink + " "
	width = "--width=1280 "
	imSize = "-F "
	ignoreSSL = "--ignore-ssl-check "
	filename = "-o " + "\'" + inFilename + "\'"
	if link.startswith("https"):
		argstring = "webkit2png " + link + width + "--delay=10 " +imSize + filename
	else:
		argstring = "webkit2png " + ignoreSSL + link + width + "--delay=15 " +imSize + filename
	inTriedShellCommands.append(argstring)
	subprocess.run(argstring, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def writeTesterToFil(inTried, inArgs, inFailed, inSucceed, inATried, inOutputType):
	#save outputs to txt files for easier checking
	a = "All Bookmarks.txt"
	b = "Shellargs.txt"
	c = "Bookmarks Failed.txt"
	d = "bookmarks Succeeded.txt"
	e = "Tried Bookmarks.txt"
	if inOutputType:
		with open(a, mode = 'wt' ) as myFile:
			for entry in inTried:
				#myFile.write(str(entry['fileName']))
				myFile.write(str(entry))
				myFile.write('\n')
		with open(d, mode = 'wt' ) as myFile:
			for entry in inSucceed:
				myFile.write(str(entry))
				myFile.write('\n')
		with open(e, mode = 'wt' ) as myFile:
			for entry in inATried:
				myFile.write(str(entry))
				myFile.write('\n')
		with open(b, mode = 'wt') as myFile:
			print("\n\n")
			for entry in inArgs:
				entry = entry.replace(u'\xa0', u' ')
				myFile.write(entry)
				myFile.write('\n')
	with open(c, mode = 'wt' ) as myFile:
		for entry in inFailed:
			myFile.write(str(entry))
			myFile.write('\n')

def checkSavedBookmarks(inAttempts, outSucceed, outFailed):
	#Loop through attemped bookmarks and check for file existence, return succeeded and failed
	for entry in inAttempts:
		if os.path.isfile(entry["fileName"]+"-full.png"):
			outSucceed.append(entry)
		else:
			outFailed.append(entry)

def loopAndSaveBookmarks(inBookmarkDict, outAllStore , outAttemptedStore, outAttemptedArgs ):
	urlList = {}
	tracker = 1
	total = len(inBookmarkDict)
	for key, entry in inBookmarkDict.items():
		sys.stdout.write('\rAttempting to save bookmark {} of {}'.format(tracker,total))
		sys.stdout.flush()
		#Remove unsafe characters from web titles and create a full file path and
		#append to to storage dictionary checkers
		folderPath = entry['folder']
		end = '/' + entry['fileName']
		fullString = folderPath + end
		entry['fileName'] = fullString
		outAllStore.append(entry)

		if entry['URL'] in urlList:
			try:
				if not os.path.isdir(folderPath):
					os.mkdir(folderPath)
				copy(urlList[entry['URL']], folderPath)
			except:
				outAttemptedStore.append(entry)
				req = Request(entry['URL'], headers={'User-Agent': 'Mozilla/5.0'})
				try:
					requestCode = urlopen(req).getcode()
					saveSiteAsPicture(entry['URL'], fullString,outAttemptedArgs)
				except:
					pass
		else:
			fullFilePath = fullString + "-full.png"
			#check for existence of file and folder, pass if file already saved or create file and 
			#folder
			if os.path.isdir(folderPath):
				outAttemptedStore.append(entry)
				req = Request(entry['URL'], headers={'User-Agent': 'Mozilla/5.0'})
				try:
					requestCode = urlopen(req).getcode()
					saveSiteAsPicture(entry['URL'], fullString,outAttemptedArgs)
					urlList[entry['URL']] = fullFilePath
				except:
					#logg HTTP error if needed
					pass
			else:
				os.makedirs(folderPath)
				outAttemptedStore.append(entry)
				req = Request(entry['URL'], headers={'User-Agent': 'Mozilla/5.0'})
				try:
					requestCode = urlopen(req).getcode()
					saveSiteAsPicture(entry['URL'], fullString,outAttemptedArgs)
					urlList[entry['URL']] = fullFilePath
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
