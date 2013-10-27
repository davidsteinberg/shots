from shot import Shot

from os import remove, sep, walk
from os.path import abspath, dirname

import re

def cleanup():
	currentDir = dirname(dirname(abspath(__file__)))
	for root, dirs, files in walk(currentDir):
		for fileName in files:
			if re.match(r".+\.shot$",fileName):
				fileName = "." + root.replace(currentDir, "", 1) + sep + fileName
				remove(fileName)
