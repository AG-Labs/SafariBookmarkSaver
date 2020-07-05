echo $SHELL

if [ $SHELL = '/bin/zsh' ]; then

	echo 'setting up scripts for zsh shell'
	echo "alias randomSelector=\"python $(pwd)/SafariBookmarkSaver.py -S -n 6 -r 70 -t ~/Desktop\"" >> ~/.zshrc
	echo "alias bookmarkSaver=\"python $(pwd)/SafariBookmarkSaver.py -j -t ./\"" >> ~/.zshrc
	echo "alias bookmarkSaverPDF=\"python $(pwd)/SafariBookmarkSaver.py -j -t ./\"" >> ~/.zshrc

elif [$SHELL = '/bin/bash' ]; then

	echo 'setting up scripts for bash shell'
	echo "alias bookmarkSaver=\"python $(pwd)/SafariBookmarkSaver.py -S -n 6 -r 70 -t ~/Desktop\"" >> ~/.bashrc
	echo "alias bookmarkSaver=\"python $(pwd)/SafariBookmarkSaver.py -j -t ./\"" >> ~/.bashrc
	echo "alias bookmarkSaverPDF=\"python $(pwd)/SafariBookmarkSaver.py -j -t ./\"" >> ~/.bashrc

fi
