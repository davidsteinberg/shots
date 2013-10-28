#-------------------------
# Shot
#-------------------------

from ast import *
from tokenizer import *
from parser import ShotParser

from os import sep, walk
from os.path import abspath, dirname, splitext

from jinja2 import Template

import re
import sys

class Shot:

	def __init__(self, fileName, fetch=True, extending=False, logging=False):
		if fetch:
			found = False
			currentDir = dirname(dirname(abspath(__file__)))
			for root, dirs, files in walk(currentDir):
				if fileName in files:
					found = True
					fileName = "." + root.replace(currentDir, "", 1) + sep + fileName
					break
			if not found:
				self.error("Shot error : couldn't find file " + fileName)
	
		self.fileName = fileName

		self.extending = extending
		self.parser = ShotParser(self.fileName,logging=logging)
			
	def error(self,message):
		print message
		exit()
	
	def generateCode(self):
		self.parser.tokenize()
		self.parser.parse()
	
		result = ""
		kids = self.parser.rootNode.children
		if len(kids) > 0:
			if self.extending:
				for k in kids:
					result += str(k)
			else:
				if not isinstance(kids[0],ShotTextNode) and kids[0].tag == "doctype":
					kids[0].tag = "!doctype"
					for k in kids:
						result += str(k)
				else:
					result = "<!doctype html>\n"
					if not isinstance(kids[0],ShotTextNode) and kids[0].tag == "html":
						for k in kids:
							result += str(k)
					else:
						node = ShotNode(tag="html",multiline=True)
						for k in kids:
							node.children.append(k)
						result += str(node)

		# last minute regex for template delimiters
		result = re.sub(r"\|([^|]+)\|",r"{{ \1 }}",result)
		return result

	def render(self,**varArgs):
		result = Template(self.generateCode())
		return result.render(**varArgs)

#-------------------------
# Main
#-------------------------

def main():
	debugging = False
	
	if len(sys.argv) < 2:
		exit("Usage : " + sys.argv[0] + " <filename> [-d]\n        " + sys.argv[0] + " requires at least a file name as a parameter, with an optional debug flag")
	elif len(sys.argv) > 2:
		if sys.argv[2] == "-d":
			debugging = True

	fileName, fileExt = splitext(sys.argv[1])
	if not fileExt:
		fileName += ".html"
	else:
		fileName += fileExt

	s = Shot(fileName)

	if debugging:
		print s.generateCode()
	else:
		print s.render()

if __name__ == "__main__":
	main()
