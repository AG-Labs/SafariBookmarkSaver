import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QDesktopWidget,QMainWindow,QHBoxLayout, QVBoxLayout, QProgressBar,QComboBox, QLabel, QFileDialog, QLineEdit
from PyQt5.QtCore import QBasicTimer, QThread
import plistlib
import os
import SafariBookmarkSaver

class Example(QMainWindow):
	def __init__(self, comboList):
		super().__init__()
		self.initUI(comboList)        
        
	def initUI(self,comboList):
		self.setGeometry(300, 300, 650, 220)
		self.setWindowTitle('Batch Bookmark Saver')

		saveButton = QPushButton('Save Bookmarks', self)
		saveButton.clicked.connect(self.saveAction)
		quitButton = QPushButton('Quit', self)
		quitButton.clicked.connect(QApplication.instance().quit)

		widget = QWidget(self)
		self.setCentralWidget(widget)

		quitSaveHBox = QHBoxLayout()
		quitSaveHBox.addStretch()
		quitSaveHBox.addWidget(quitButton)
		quitSaveHBox.addWidget(saveButton)

		vbox = QVBoxLayout()
		self.selectLabel = QLabel('Select Source Folder')
		vbox.addWidget(self.selectLabel)
		self.myCombo = self.setupComboBox(comboList)
		vbox.addWidget(self.myCombo)
		vbox.addStretch()

		self.destinationLabel = QLabel('Select Destination Folder')
		vbox.addWidget(self.destinationLabel)
		centralHbox = QHBoxLayout()

		self.destinationField = QLineEdit()
		defaultDestinationShort = '~/Desktop'
		defaultDestination = os.path.expanduser(defaultDestinationShort)
		self.destinationField.setText(defaultDestination)
		
		self.destinationSelect = QPushButton('Select Folder',self)
		self.destinationSelect.clicked.connect(self.selectDir)
		centralHbox.addWidget(self.destinationField)
		centralHbox.addWidget(self.destinationSelect)
		vbox.addLayout(centralHbox)

		vbox.addStretch()

		self.descriptionLabel = QLabel('')
		vbox.addWidget(self.descriptionLabel)
		self.pbar = QProgressBar(self)
		self.pbar.setGeometry(45, 150, 400, 25)
		self.pbar.hide()#design feedback with the main code to move the pbar
		vbox.addWidget(self.pbar)
		vbox.addStretch()
		vbox.addLayout(quitSaveHBox)

		widget.setLayout(vbox)
		
		self.center()
		self.show()

	def setupComboBox(self, inList):
		combo = QComboBox(self)
		combo.addItem("All")
		for aCounter in inList:
			combo.addItem(aCounter)
		combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
		return(combo)


	def saveAction(self):
		self.appThread = bookmarkSaverThread(self.myCombo.currentText(), self.destinationField.text())
		self.appThread.start()

	def center(self):
		qr = self.frameGeometry()
		cp = QDesktopWidget().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def selectDir(self):
		dest = QFileDialog.getExistingDirectory(self,'select dir')
		self.destinationField.setText(dest)

class bookmarkSaverThread(QThread):
	def __init__(self, inSource, inDestination):
		QThread.__init__(self)
		self.source = inSource
		self.destination = inDestination

	def __del__(self):
		self.wait()
	
	def run(self):
		loopBookmarksRefac.main(self.source, self.destination, False)

def getAllBookmarks(bookmarksPath):
	with open(bookmarksPath, 'rb') as fp:
		pl = plistlib.load(fp)
		bookmarksOuterMenu = [item for item in pl['Children'] if 'Title' in item and item['Title'] == 'BookmarksMenu'][0]
		bookmarksMenu = bookmarksOuterMenu['Children']

		mySavedArray = findFolders(bookmarksMenu)

		myOrderedArray = orderBookmarks(mySavedArray)
		preparedArray = prepareBookmarkName(myOrderedArray)
		return preparedArray
    
def findFolders(inDict):
	outArr = []
	dictLevel = 0
	recusiveFolders(inDict, outArr ,dictLevel)
	return outArr

def recusiveFolders(inDict, outArr, inLevel):
	for aChild in inDict:
		if 'Children' in aChild:
			tempNameStore = aChild['Title']
			recusiveFolders(aChild['Children'], outArr ,inLevel + 1)
			temp = {'level': inLevel ,'Title': aChild['Title']}
			outArr.append(temp)

def orderBookmarks(inArr):
	previousKey = 0
	counter = 0
	tracker = []
	for aKey in inArr:
		currentKey = aKey['level']
		if currentKey > previousKey:
			for counter2 in range(currentKey - previousKey):
				tracker.append(counter)
		elif currentKey < previousKey:
			inArr.insert(tracker.pop(), inArr.pop(counter))
		previousKey = currentKey
		counter += 1
	return inArr

def prepareBookmarkName(inArr):
	 outArr = []
	 for aKey in inArr:
	 	prefix = ""
	 	title = aKey['Title']
	 	tabNumber = aKey['level']
	 	for counter in range(tabNumber):
	 		prefix += "    "
	 	outArr.append(prefix + title)
	 return(outArr)

if __name__ == '__main__':
    bookmarksPathShort = '~/Library/Safari/Bookmarks.plist'
    bookmarksPath = os.path.expanduser(bookmarksPathShort)
    bookmarkList = getAllBookmarks(bookmarksPath)

    app = QApplication(sys.argv)
    ex = Example(bookmarkList)

    sys.exit(app.exec_())