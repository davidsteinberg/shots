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

	def __init__(self,fileName, included=False, logging=False):
		self.tokenizer = ShotsTokenizer(fileName,logging=logging)
		self.included = included

		self.currentLineNum = 0
		self.currentTokenNum = 0

		self.currentToken = None
		self.prevTokenType = ShotsToken.typeUnknown

		self.rootNode = ShotsNode(tag="",depth=-1)
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
			p = ShotsParser(fileName,included=True)
			p.tokenize()
			p.parse()
			
			node = ShotsNode(tag="",depth=self.getDepth(),parent=self.currentNode)
			for kid in p.rootNode.children:
				node.children.append(kid)
			
			return node
			
		else:
			fileName = quoteChar + fileName + quoteChar
		
			if fileExt == "css":
				node = ShotsNode(tag="link",depth=self.getDepth(),parent=self.currentNode,selfClosing=True)

				href = ShotsAttribute(name="href")
				href.value = fileName
				node.attributes.append(href)

				rel = ShotsAttribute(name="rel")
				rel.value = "\"stylesheet\""
				node.attributes.append(rel)

				return node
			elif fileExt == "js":
				node = ShotsNode(tag="script",depth=self.getDepth(),parent=self.currentNode)
			
				src = ShotsAttribute(name="src")
				src.value = fileName
				node.attributes.append(src)
			
				return node
			else:
				self.parseError("couldn't find file extension on " + ("fetch" if fetch else "includ") + "ed file")

	def getBreakElement(self):
		self.getNextToken()
	
		if self.currentToken.type == ShotsToken.typeNumber:
			node = ShotsNode(tag="",depth=self.getDepth(),parent=self.currentNode)
			for i in range(int(self.currentToken.value)):
				node.children.append(ShotsNode(tag="br",parent=self.currentNode,selfClosing=True))

		else:
			node = ShotsNode(tag="br",depth=self.getDepth(),parent=self.currentNode)
			node.selfClosing = True
			
		return node

	def getText(self):
		node = ShotsTextNode(self.currentToken.value,depth=self.getDepth())
		self.currentNode.children.append(node)

	def getDirective(self):
		node = ShotsTextNode(text="{% "+self.currentToken.value+" %}",depth=self.getDepth())
		self.currentNode.children.append(node)
		
	def getComment(self):
		node = ShotsTextNode(text="<!-- "+self.currentToken.value+" -->",depth=self.getDepth())
		self.currentNode.children.append(node)

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
				for i in range(line.depth):
					commentBody.append("    ")
				for token in line.tokens:
					commentBody.append(token.value + " ")
				commentBody.append("\n")
			
				self.currentLineNum += 1
				if self.currentLineNum >= len(self.tokenizer.lines):
					break
				line = self.tokenizer.lines[self.currentLineNum]
			
			self.currentLineNum -= 1

		return ShotsTextNode(text="<!--\n"+"".join(commentBody)+"-->",depth=commentDepth)

	def getNodeWithTag(self):
		if self.currentToken.value == "comment":
			node = self.getBlockComment()

		else:
			if self.included:
				self.lookingForHead = False
				self.fillingHead = False
		
			elif self.lookingForHead:
				if self.currentToken.value == "head":
					self.lookingForHead = False
				elif self.currentToken.value != "doctype" and self.currentToken.value != "html":
					headElement = ShotsNode(tag="head",depth=-1,parent=self.currentNode)
					self.currentNode.children.append(headElement)
					self.currentNode = headElement
			
					self.lookingForHead = False
				
					if self.currentToken.value not in self.tagsForHead:
						self.fillingHead = False
						self.currentNode = self.currentNode.parent
						if self.currentToken.value != "body":
							bodyElement = ShotsNode(tag="body",depth=-1,parent=self.currentNode)
							self.currentNode.children.append(bodyElement)
							self.currentNode = bodyElement

			elif self.fillingHead:
				if self.currentToken.value not in self.tagsForHead:
					self.fillingHead = False
					self.currentNode = self.currentNode.parent
					if self.currentToken.value != "body":
						bodyElement = ShotsNode(tag="body",depth=-1,parent=self.currentNode)
						self.currentNode.children.append(bodyElement)
						self.currentNode = bodyElement
	
			if self.currentToken.value == "include":
				node = self.includeFile()

			elif self.currentToken.value == "fetch":
				node = self.includeFile(fetch=True)

			elif self.currentToken.value == "media":
				node = self.getMediaElement()

			elif self.currentToken.value == "link":
				node = seld.getLinkElement()

			elif self.currentToken.value == "br":
				node = self.getBreakElement()

			elif self.currentToken.value == "style" or self.currentToken.value == "css":
				node = self.getStyleElement()

			elif self.currentToken.value == "script" or self.currentToken.value == "js" or self.currentToken.value == "javascript":
				node = self.getScriptElement()

			else:
				node = ShotsNode(tag=self.currentToken.value,depth=self.getDepth(),parent=self.currentNode)
				self.currentNode.children.append(node)
				self.currentNode = node
				node = None
				
				blockText = False
				
				self.getNextToken()
				while self.currentToken.type != ShotsToken.typeEOL:
					
					if self.currentToken.type == ShotsToken.typeAlpha:
						attr = ShotsAttribute(name=self.currentToken.value)
						self.getNextToken()
						
						if self.currentToken.type == ShotsToken.typeEquals:
							self.getNextToken()
							attr.value = self.currentToken.value
						
						self.currentNode.attributes.append(attr)
					
					elif self.currentToken.type == ShotsToken.typeClass:
						self.currentNode.classes.append(self.currentToken.value)
					
					elif self.currentToken.type == ShotsToken.typeID:
						self.currentNode.id = self.currentToken.value
					
					elif self.currentToken.type == ShotsToken.typeText:
						if self.currentToken.value == "":
							blockText = True
						else:
							self.currentNode.children.append(ShotsTextNode(text=self.currentToken.value))
							self.currentNode.multiline = False
						break
						
					elif self.currentToken.type == ShotsToken.typeChildElemNext:
						break
				
					self.getNextToken()
				
				if blockText:
					elemBody = []
					elemDepth = self.getDepth()
		
					self.currentLineNum += 1
					if self.currentLineNum < len(self.tokenizer.lines):
						line = self.tokenizer.lines[self.currentLineNum]
		
						while line.depth > elemDepth:
							for i in range(line.depth):
								elemBody.append("    ")
							for token in line.tokens:
								elemBody.append(token.value + " ")
							elemBody.append("\n")
			
							self.currentLineNum += 1
							if self.currentLineNum >= len(self.tokenizer.lines):
								break
							line = self.tokenizer.lines[self.currentLineNum]
			
						self.currentLineNum -= 1
					
					del elemBody[-1] # get rid of last newline
					self.currentNode.children.append(''.join(elemBody))
		
		if node:
			self.currentNode.children.append(node)

	def getDepth(self):
		return self.tokenizer.lines[self.currentLineNum].depth

	def getNode(self):
		if self.reachedEOF():
			return None

		while self.getDepth() <= self.currentNode.depth:
			self.currentNode = self.currentNode.parent

		self.getNextToken()

		if self.currentToken.type == ShotsToken.typeAlpha:
			self.getNodeWithTag()

		elif self.currentToken.type == ShotsToken.typeClass:
			self.getNodeWithClass()

		elif self.currentToken.type == ShotsToken.typeID:
			self.getNodeWithID()

		elif self.currentToken.type == ShotsToken.typeText:
			self.getText()

		elif self.currentToken.type == ShotsToken.typeDirective:
			self.getDirective()

		elif self.currentToken.type == ShotsToken.typeComment:
			self.getComment()
			
		return True

	def getNextNode(self):
		self.nextNode = self.getNode()
		self.currentLineNum += 1
		self.currentTokenNum = 0

	def tokenize(self):
		self.tokenizer.tokenize()

	def parse(self):
		self.getNextNode()
		while self.nextNode:
			self.getNextNode()
