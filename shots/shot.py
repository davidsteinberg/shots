#-------------------------
# Shot
#-------------------------

import re
import sys

from os import sep, walk
from os.path import abspath, dirname, splitext

from jinja2 import Environment
from loader import ShotLoader

class Shot:

	environment = Environment(loader=ShotLoader())

	def __init__(self, fileName, logging=False):
		self.fileName = fileName
			
	def error(self,message):
		print message
		exit()

	def render(self,**varArgs):
		template = Shot.environment.get_template(self.fileName)
		return template.render(**varArgs)

#-------------------------
# Main
#-------------------------

def main():
	beforeJinja = False
	logging = False
	
	if len(sys.argv) < 2:
		exit("Usage : " + sys.argv[0] + " <filename> [-d]\n        " + sys.argv[0] + " requires at least a file name as a parameter, with an optional debug flag")
	elif len(sys.argv) > 2:
		if "-j" in sys.argv:
			beforeJinja = True
		if "-l" in sys.argv:
			logging = True

	fileName, fileExt = splitext(sys.argv[1])
	if not fileExt:
		fileName += ".html"
	else:
		fileName += fileExt

	s = Shot(fileName,logging=logging)

	if beforeJinja:
		print s.generateCode() + "\n\n----------------\n"
	
	print s.render()

if __name__ == "__main__":
	main()
