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

	def reachedEOF(self):
		return self.currentLineNum >= len(self.tokenizer.lines)

	def getNextToken(self):
		self.currentToken = self.getToken()
		print self.currentToken

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
			return ShotsToken(type=ShotsToken.typeEOL)
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
			return s.rootNode
			
		else:		
			fileName = '"' + fileName + '"'
		
			if fileExt == "css":			
				node = ShotsNode(tag="link",parent=self.currentNode,selfClosing=True)

				href = ShotsAttribute(name="href")
				href.value = fileName
				node.attributes.append(href)

				rel = ShotsAttribute(name="rel")
				rel.value = "\"stylesheet\""
				node.attributes.append(rel)

				return node
			elif fileExt == "js":
				node = ShotsNode(tag="script",parent=self.currentNode)
			
				src = ShotsAttribute(name="src")
				src.value = fileName
				node.attributes.append(src)
			
				return node
			else:
				self.parseError("couldn't find file extension on included file")

	def makeBreakElement(self):
		self.getNextToken()
	
		if self.currentToken.type == ShotsToken.typeNumber:
			node = ShotsNode(tag="span",parent=self.currentNode)
			for i in range(int(self.currentToken.value)-1):
				node.children.append(ShotsNode(tag="br",parent=self.currentNode,selfClosing=True))

		else:
			node = ShotsNode(tag="br",parent=self.currentNode)
			node.selfClosing = True
			
		return node

	def getNodeWithDirective(self):
		return ShotsTextNode(text="{% "+self.currentToken.value+" %}")
		
	def getNodeWithComment(self):
		return ShotsTextNode(text="<!-- "+self.currentToken.value+" -->")

	def getNodeWithTag(self):
		if self.currentToken.value == "include":
			return self.includeFile()
		elif self.currentToken.value == "fetch":
			return self.includeFile(fetch=True)
		elif self.currentToken.value == "media":
			pass
		elif self.currentToken.value == "link":
			pass
		elif self.currentToken.value == "br":
			return self.makeBreakElement()
		else:
			pass
# 			if self.included:
# 				self.lookingForHead = False
# 				self.fillingHead = False
# 			
# 			elif self.lookingForHead:
# 				if identifier == "head":
# 					self.lookingForHead = False
# 				elif identifier != "doctype" and identifier != "html":
# 					headElement = PageElement(tag="head",depth=-1,parent=self.currentNode)
# 					self.currentNode.children.append(headElement)
# 					self.currentNode = headElement
# 				
# 					self.lookingForHead = False
# 					
# 					if identifier not in self.tagsForHead:
# 						self.fillingHead = False
# 						self.currentNode = self.currentNode.parent
# 						if identifier != "body":
# 							bodyElement = PageElement(tag="body",depth=-1,parent=self.currentNode)
# 							self.rootNode.children.append(bodyElement)
# 							self.currentNode = bodyElement
# 
# 			elif self.fillingHead:
# 				if identifier not in self.tagsForHead:
# 					self.fillingHead = False
# 					if identifier != "body":
# 						bodyElement = PageElement(tag="body",depth=-1,parent=self.currentNode)
# 						self.rootNode.children.append(bodyElement)
# 						self.currentNode = bodyElement
# 			
# 			self.makeElementWithTag(identifier)
# 			

	def getDepth(self):
		return self.tokenizer.lines[self.currentLineNum].depth

	def getNode(self):
		if self.reachedEOF():
			return None
	
		nextDepth = self.getDepth()
		
		if nextDepth <= self.currentNode.depth:
			self.currentNode = self.currentNode.parent

		self.getNextToken()

		if self.currentToken.type == ShotsToken.typeEOL:
			return None

		if self.currentToken.type == ShotsToken.typeAlpha:
			node = self.getNodeWithTag()
		elif self.currentToken.type == ShotsToken.typeClass:
			node = self.getNodeWithClass()
		elif self.currentToken.type == ShotsToken.typeID:
			node = self.getNodeWithID()
		elif self.currentToken.type == ShotsToken.typeText:
			node = self.getNodeWithText()
		elif self.currentToken.type == ShotsToken.typeDirective:
			node = self.getNodeWithDirective()
		elif self.currentToken.type == ShotsToken.typeComment:
			node = self.getNodeWithComment()
		return node

	def getNextNode(self):
		self.nextNode = self.getNode()
		self.currentLineNum += 1
		self.currentTokenNum = 0

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
