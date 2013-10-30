#-------------------------
# Shot
#-------------------------

import re
import sys

from os import sep, walk
from os.path import abspath, dirname, isfile, splitext

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from parser import ShotParser

environment = Environment(loader=FileSystemLoader("/"))
templateDir = "/templates"
fileSuffix = ".shot"

class Shot:
	def __init__(self, filename, overwrite=True, included=False, logging=False):
		fileExt = filename.split(".")[-1]
		if not fileExt or fileExt != "html":
			filename += ".html"

		self.filename = locate(filename)
		self.overwrite = overwrite
		self.included = included
		self.logging = logging

		if self.overwrite or not isfile(self.filename):
			self.parser = ShotParser(self.filename, included=self.included, logging=self.logging)

	def log(self, message):
		if self.logging:
			print message

	def generateShot(self):
		self.log("generating " + self.filename)
	
		if self.overwrite or not isfile(self.filename):
			self.filename += fileSuffix
			f = open(self.filename,"w")

			code = self.parser.generateCode()
			self.log("\nCODE\n\n"+code+"\n\nEND CODE\n")

			f.write(code)
			f.close()

	def render(self,**varArgs):
		self.generateShot()
		template = environment.get_template(self.filename)
		return template.render(**varArgs)

#-------------------------
# Locate
#-------------------------

def locate(filename):
	found = False
	currentDir = dirname(dirname(abspath(__file__))) + templateDir
	for root, dirs, files in walk(currentDir):
		if filename in files:
			found = True
			filename = currentDir + sep + filename
			break
	if not found:
		raise TemplateNotFound(filename)
	
	return filename


#-------------------------
# Main
#-------------------------

def main():
	beforeJinja = False
	logging = False
	
	if len(sys.argv) < 2:
		exit("Usage : " + sys.argv[0] + " <filename> [-d]\n        " + sys.argv[0] + " requires at least a file name as a parameter, with an optional debug flag")
	elif len(sys.argv) > 2:
		if "-l" in sys.argv:
			logging = True
		if "-j" in sys.argv:
			beforeJinja = True

	if beforeJinja:
		s = Shot(sys.argv[1], overwrite=True, logging=logging)
		print s.parser.generateCode()
	else:
		s = Shot(sys.argv[1], logging=logging)
		print s.render()

if __name__ == "__main__":
	main()
