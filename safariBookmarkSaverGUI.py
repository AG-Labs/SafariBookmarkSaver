import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QDesktopWidget,QMainWindow,QHBoxLayout, QVBoxLayout, QProgressBar,QComboBox, QLabel, QFileDialog, QLineEdit
from PyQt5.QtCore import QBasicTimer, QThread
import plistlib
import os
import SafariBookmarkSaver

class Example(QMainWindow):
	def __init__(self, combo_list):
		super().__init__()
		self.initUI(combo_list)        
        
	def initUI(self,combo_list):
		self.setGeometry(300, 300, 650, 220)
		self.setWindowTitle('Batch Bookmark Saver')

		save_button = QPushButton('Save Bookmarks', self)
		save_button.clicked.connect(self.saveAction)
		quit_button = QPushButton('Quit', self)
		quit_button.clicked.connect(QApplication.instance().quit)

		widget = QWidget(self)
		self.setCentralWidget(widget)

		quit_save_hbox = QHBoxLayout()
		quit_save_hbox.addStretch()
		quit_save_hbox.addWidget(quit_button)
		quit_save_hbox.addWidget(save_button)

		vbox = QVBoxLayout()
		self.selectLabel = QLabel('Select Source Folder')
		vbox.addWidget(self.selectLabel)
		self.myCombo = self.setupComboBox(combo_list)
		vbox.addWidget(self.myCombo)
		vbox.addStretch()

		self.destinationLabel = QLabel('Select Destination Folder')
		vbox.addWidget(self.destinationLabel)
		central_hbox = QHBoxLayout()

		self.destinationField = QLineEdit()
		default_destination_short = '~/Desktop'
		default_destination = os.path.expanduser(default_destination_short)
		self.destinationField.setText(default_destination)
		
		self.destinationSelect = QPushButton('Select Folder',self)
		self.destinationSelect.clicked.connect(self.selectDir)
		central_hbox.addWidget(self.destinationField)
		central_hbox.addWidget(self.destinationSelect)
		vbox.addLayout(central_hbox)

		vbox.addStretch()

		self.descriptionLabel = QLabel('')
		vbox.addWidget(self.descriptionLabel)
		self.pbar = QProgressBar(self)
		self.pbar.setGeometry(45, 150, 400, 25)
		self.pbar.hide()#design feedback with the main code to move the pbar
		vbox.addWidget(self.pbar)
		vbox.addStretch()
		vbox.addLayout(quit_save_hbox)

		widget.setLayout(vbox)
		
		self.center()
		self.show()

	def setupComboBox(self, in_list):
		combo = QComboBox(self)
		combo.addItem("All")
		for a_counter in in_list:
			combo.addItem(a_counter)
		combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
		return(combo)


	def saveAction(self):
		self.appThread = BookmarkSaverThread(self.myCombo.currentText(), self.destinationField.text())
		self.appThread.start()

	def center(self):
		qr = self.frameGeometry()
		cp = QDesktopWidget().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def selectDir(self):
		dest = QFileDialog.getExistingDirectory(self,'select dir')
		self.destinationField.setText(dest)

class BookmarkSaverThread(QThread):
	def __init__(self, in_source, in_destination):
		QThread.__init__(self)
		self.source = in_source
		self.destination = in_destination

	def __del__(self):
		self.wait()
	
	def run(self):
		loopBookmarksRefac.main(self.source, self.destination, False)

def get_all_bookmarks(bookmarks_path):
	with open(bookmarks_path, 'rb') as fp:
		pl = plistlib.load(fp)
		bookmarks_outer_menu = [item for item in pl['Children'] if 'Title' in item and item['Title'] == 'BookmarksMenu'][0]
		bookmarks_menu = bookmarks_outer_menu['Children']

		my_saved_array = find_folders(bookmarks_menu)

		my_ordered_array = order_bookmarks(my_saved_array)
		prepared_array = prepare_bookmark_name(my_ordered_array)
		return prepared_array
    
def find_folders(in_dict):
	out_arr = []
	dict_level = 0
	recusive_folders(in_dict, out_arr ,dict_level)
	return out_arr

def recusive_folders(in_dict, out_arr, in_level):
	for a_child in in_dict:
		if 'Children' in a_child:
			recusive_folders(a_child['Children'], out_arr ,in_level + 1)
			temp = {'level': in_level ,'Title': a_child['Title']}
			out_arr.append(temp)

def order_bookmarks(in_arr):
	previous_key = 0
	counter = 0
	tracker = []
	for a_key in in_arr:
		current_key = a_key['level']
		if current_key > previous_key:
			for _ in range(current_key - previous_key):
				tracker.append(counter)
		elif current_key < previous_key:
			in_arr.insert(tracker.pop(), in_arr.pop(counter))
		previous_key = current_key
		counter += 1
	return in_arr

def prepare_bookmark_name(in_arr):
	 out_arr = []
	 for a_key in in_arr:
	 	prefix = ""
	 	title = a_key['Title']
	 	tab_number = a_key['level']
	 	for _ in range(tab_number):
	 		prefix += "    "
	 	out_arr.append(prefix + title)
	 return(out_arr)

if __name__ == '__main__':
    bookmarksPathShort = '~/Library/Safari/Bookmarks.plist'
    bookmarks_path = os.path.expanduser(bookmarksPathShort)
    bookmarkList = get_all_bookmarks(bookmarks_path)

    app = QApplication(sys.argv)
    ex = Example(bookmarkList)

    sys.exit(app.exec_())