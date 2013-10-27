#-------------------------
# Shot
#-------------------------

from shutil import copyfile
from os import listdir, remove, sep, walk
from os.path import abspath, dirname, isfile, join, splitext

from ast import *
from tokenizer import *

from flask import render_template

import re
import sys

class Shot:

	templateDir = "../templates/"

	selfClosers = ["area", "base", "br", "col", "command", "doctype", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source", "track", "wbr"]
	tagsForHead = ["base", "comment", "css", "fetch", "include", "js", "javascript", "link", "meta", "noscript", "script", "style", "title"]

	EOL = "$"

	def __init__(self, fileName, extending=False, including=False, logging=False):

		self.fileName = Shot.templateDir + fileName

		self.extending = extending
		self.including = including
		self.logging = logging
		
		self.tokenizer = ShotsTokenizer(self.fileName,logging=logging)

		self.currentLineNum = 0
		self.currentTokenNum = 0
		self.currentDepth = 0

		self.currentToken = None
		self.prevTokenType = ShotsToken.typeUnknown

		self.rootNode = ShotsNode(tag="document",depth=-1,multiline=True)
		self.currentNode = self.rootNode
		self.nextNode = None
		
		self.lookingForHead = True
		self.fillingHead = True

	def parseError(self,string):
		exit("Parse Error on line " + str(self.currentLineNum+1) + ", token " + str(self.currentTokenNum) + " : " + string)

	def getNextToken(self):
		self.currentToken = self.getToken()

	def printTier(self,string, num=0):
		if not self.logging:
			return
	
		for i in range(num):
			print "    ",
		print string

	def logDigestion(self,eaten):
		self.printTier("- eat " + eaten,1)

	def logCreation(self,tag):
		self.printTier("make " + tag)

	def logFinishedCreation(self,tag):
		self.printTier("finished making " + tag)

	def getToken(self):
		if self.currentTokenNum >= len(self.tokenizer.lines[self.currentLineNum].tokens):
			return self.EOL
		self.currentTokenNum += 1
		return self.tokenizer.lines[self.currentLineNum].tokens[self.currentTokenNum-1]

	def getNextToken(self):
		self.currentToken = self.getToken()

	def includeFile(self,fetch=False):
		self.getNextToken()
		
		fileName = self.currentToken.value
		fileExt = fileName.split('.')[-1]
		
		if fetch:
			found = False
			currentDir = dirname(dirname(abspath(__file__)))
			for root, dirs, files in walk(currentDir):
				if fileName in files:
					found = True
					fileName = root.replace(currentDir, "", 1) + sep + fileName
					break
			if not found:
				self.parseError("couldn't fetch file " + fileName)
	
		if fileExt == "html":
			s = Shot(fileName,included=True)
			for kid in s.rootNode.children:
				self.currentNode.children.append(kid)
			
		else:		
			fileName = '"' + fileName + '"'
		
			if fileExt == "css":			
				newNode = ShotsNode(tag="link",parent=self.currentNode,selfClosing=True)

				href = ShotsAttribute(name="href")
				href.value = fileName
				newNode.attributes.append(href)

				rel = ShotsAttribute(name="rel")
				rel.value = "\"stylesheet\""
				newNode.attributes.append(rel)

				self.currentNode.children.append(newNode)
			elif fileExt == "js":
				newNode = ShotsNode(tag="script",parent=self.currentNode)
			
				src = ShotsAttribute(name="src")
				src.value = fileName
				newNode.attributes.append(src)
			
				self.currentNode.children.append(newNode)
			else:
				self.parseError("couldn't find file extension on included file")

	def getNodeWithTag(self):
		if self.currentToken.value == "fetch":
			self.includeFile(fetch=True)
		elif self.currentToken.value == "include":
			pass
		elif self.currentToken.value == "media":
			pass
		elif self.currentToken.value == "link":
			pass
		else:
			pass

	def getDepth(self):
		return self.tokenizer.lines[self.currentLineNum].depth

	def getNode(self):	
		nextDepth = self.getDepth()
		
		if nextDepth <= self.currentNode.depth:
			self.currentNode = self.currentNode.parent

		self.getNextToken()

		node = None

		if self.currentToken.type == ShotsToken.typeAlpha:
			node = self.getNodeWithTag()
		elif self.currentToken.type == ShotsToken.typeClass:
			node = self.getNodeWithClass()
		elif self.currentToken.type == ShotsToken.typeID:
			node = self.getNodeWithID()
		elif self.currentToken.type == ShotsToken.typeText:
			node = self.getNodeWithText()

		return node

	def getNextNode(self):
		self.nextNode = self.getNode()

	def tokenize(self):
		self.tokenizer.tokenize()

	def parse(self):
		self.getNextNode()
		while self.nextNode:
			self.currentNode.children.append(self.nextNode)
			self.getNextNode()
			
	def generateCode(self):
		result = ""
		kids = self.rootNode.children
		if len(kids) > 0:
			if self.extending:
				for k in kids:
					result += str(k)
			else:
				if not isinstance(kids[0],TextNode) and kids[0].tag == "doctype":
					kids[0].tag = "!doctype"
					for k in kids:
						result += str(k)
				else:
					result = "<!doctype html>\n"
					if not isinstance(kids[0],TextNode) and kids[0].tag == "html":
						for k in kids:
							result += str(k)
					else:
						newNode = ShotsNode(tag="html",multiline=True)
						for k in kids:
							newNode.children.append(k)
						result += str(newNode)

		# last minute regex for template delimiters
		result = re.sub(r"\|([^|]+)\|",r"{{ \1 }}",result)
		return result
	
	def generateFile(self):
		genFile = open(Shot.templateDir+self.fileName+".shot","w")
		genFile.write(self.generateCode())
		genFile.close()

	def render(self,**varArgs):
		self.tokenize()
		self.parse()
		self.generateFile()
	
		f = open(self.fileName + ".shot","r")
		result = f.read() # render_template(self.fileName + ".shot", **varArgs)
		f.close()

		templates = [ f for f in listdir(Shot.templateDir) if isfile(join(Shot.templateDir,f)) ]
		for t in templates:
			if re.match(".+\.shot",t):
				remove(Shot.templateDir + t)
		
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
