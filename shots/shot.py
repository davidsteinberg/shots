#-------------------------
# Shot
#-------------------------

from ast import *
from tokenizer import *
from parser import ShotsParser

from shutil import copyfile
from os import listdir, remove, sep, walk
from os.path import abspath, dirname, isfile, join, splitext

from flask import render_template

import re
import sys

class Shot:

	# templateDir = "templates/"

	def __init__(self, fileName, extending=False, logging=False):
		found = False
		currentDir = dirname(dirname(abspath(__file__)))
		for root, dirs, files in walk(currentDir):
			if fileName in files:
				found = True
				fileName = "." + root.replace(currentDir, "", 1) + sep + fileName
				break
		if not found:
			self.error("couldn't find file " + fileName)
	
		self.fileName = fileName
		# self.fileName = Shot.templateDir + fileName

		self.extending = extending
		self.parser = ShotsParser(self.fileName,logging=logging)
			
	def error(self,message):
		print message
		exit
	
	def generateCode(self):
		result = ""
		kids = self.parser.rootNode.children
		if len(kids) > 0:
			if self.extending:
				for k in kids:
					result += str(k)
			else:
				if not isinstance(kids[0],ShotsTextNode) and kids[0].tag == "doctype":
					kids[0].tag = "!doctype"
					for k in kids:
						result += str(k)
				else:
					result = "<!doctype html>\n"
					if not isinstance(kids[0],ShotsTextNode) and kids[0].tag == "html":
						for k in kids:
							result += str(k)
					else:
						node = ShotsNode(tag="html",multiline=True)
						for k in kids:
							node.children.append(k)
						result += str(node)

		# last minute regex for template delimiters
		result = re.sub(r"\|([^|]+)\|",r"{{ \1 }}",result)
		return result
	
	def generateFile(self):
		genFile = open(self.fileName+".shot","w")
		genFile.write(self.generateCode())
		genFile.close()

	def render(self,**varArgs):
		self.parser.tokenize()
		self.parser.parse()
		self.generateFile()
	
		f = open(self.fileName + ".shot","r")
		result = f.read() # render_template(self.fileName + ".shot", **varArgs)
		f.close()

		return result

#-------------------------
# Main
#-------------------------

def main():
	logging = False
	
	if len(sys.argv) < 2:
		exit("Usage : " + sys.argv[0] + " <filename> [-d]\n        " + sys.argv[0] + " requires at least a file name as a parameter, with an optional debug flag")
	elif len(sys.argv) > 2:
		if sys.argv[2] == "-d":
			logging = True

	fileName, fileExt = splitext(sys.argv[1])
	if not fileExt:
		fileName += ".html"
	else:
		fileName += fileExt

	s = Shot(fileName,logging=logging)
	print s.render()

if __name__ == "__main__":
	main()
