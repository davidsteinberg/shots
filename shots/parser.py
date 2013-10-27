#-------------------------
# Parser
#-------------------------

from ast import *
from tokenizer import *

from os import sep, walk
from os.path import abspath, dirname

class ShotsParser:
	selfClosers = ["area", "base", "br", "col", "command", "doctype", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source", "track", "wbr"]
	tagsForHead = ["base", "comment", "css", "fetch", "include", "js", "javascript", "link", "meta", "noscript", "script", "style", "title"]

	def __init__(self,fileName,logging=False):
		self.tokenizer = ShotsTokenizer(fileName,logging=logging)

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
		quoteChar = fileName[0]
		fileName = fileName.replace(quoteChar,"")
		
		fileExt = fileName.split('.')[-1]
		
		if fetch:
			found = False
			currentDir = dirname(dirname(abspath(__file__)))
			for root, dirs, files in walk(currentDir):
				if fileName in files:
					found = True
					fileName = "." + root.replace(currentDir, "", 1) + sep + fileName
					break
			if not found:
				self.parseError("couldn't fetch file " + fileName)
	
		if fileExt == "html":
			p = ShotsParser(fileName)
			p.tokenize()
			p.parse()
			
			node = ShotsNode(tag="",parent=self.currentNode)
			for kid in p.rootNode.children:
				node.children.append(kid)
			
			return node
			
		else:
			fileName = quoteChar + fileName + quoteChar
		
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

	def getBreakElement(self):
		self.getNextToken()
	
		if self.currentToken.type == ShotsToken.typeNumber:
			node = ShotsNode(tag="",parent=self.currentNode)
			for i in range(int(self.currentToken.value)):
				node.children.append(ShotsNode(tag="br",parent=self.currentNode,selfClosing=True))

		else:
			node = ShotsNode(tag="br",parent=self.currentNode)
			node.selfClosing = True
			
		return node

	def getDirective(self):
		return ShotsTextNode(text="{% "+self.currentToken.value+" %}")
		
	def getComment(self):
		return ShotsTextNode(text="<!-- "+self.currentToken.value+" -->")

	def getBlockComment(self):
		commentBody = []
		
		self.getNextToken()
		while self.currentToken.type != ShotsToken.typeEOL:
			commentBody.append(self.currentToken.value)
			self.getNextToken()
		
		commentDepth = self.getDepth()
		
		self.currentLineNum += 1
		if self.currentLineNum < len(self.tokenizer.lines):
			line = self.tokenizer.lines[self.currentLineNum]
		
			while line.depth > commentDepth:
				for i in range(line.depth-1):
					commentBody.append("    ")
				for token in line.tokens:
					commentBody.append(token.value + " ")
				commentBody.append("\n")
			
				self.currentLineNum += 1
				if self.currentLineNum >= len(self.tokenizer.lines):
					break
				line = self.tokenizer.lines[self.currentLineNum]

		return ShotsTextNode(text="<!--\n"+"".join(commentBody)+"-->")

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
			return self.getBreakElement()
		elif self.currentToken.value == "comment":
			return self.getBlockComment()
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

		if self.getDepth() <= self.currentNode.depth:
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
			node = self.getText()
		elif self.currentToken.type == ShotsToken.typeDirective:
			node = self.getDirective()
		elif self.currentToken.type == ShotsToken.typeComment:
			node = self.getComment()
			
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