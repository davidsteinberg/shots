#-------------------------
# Parser
#-------------------------

from ast import *
from tokenizer import *

from os import sep, walk
from os.path import abspath, dirname

class ShotParser:

	selfClosers = ["area", "base", "br", "col", "command", "doctype", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source", "track", "wbr"]
	tagsForHead = ["base", "comment", "css", "fetch", "include", "js", "javascript", "link", "meta", "noscript", "script", "style", "title"]

	def __init__(self,fileName, included=False, logging=False):
		self.tokenizer = ShotTokenizer(fileName,logging=logging)
		self.included = included

		self.currentLineNum = 0
		self.currentTokenNum = 0

		self.currentToken = None
		self.prevTokenType = ShotToken.typeUnknown

		self.rootNode = ShotNode(tag="",depth=-1)
		self.currentNode = self.rootNode
		self.nextNode = None
		
		self.lookingForHead = True
		self.fillingHead = True
		self.bodyCreated = False

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
			return ShotToken(type=ShotToken.typeEOL)
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
			p = ShotParser(fileName,included=True)
			p.tokenize()
			p.parse()
			
			node = ShotNode(tag="",depth=self.getDepth(),parent=self.currentNode)
			for kid in p.rootNode.children:
				node.children.append(kid)
			
			return node
			
		else:
			fileName = quoteChar + fileName + quoteChar
		
			if fileExt == "css":
				node = ShotNode(tag="link",depth=self.getDepth(),parent=self.currentNode,selfClosing=True)

				href = ShotAttribute(name="href")
				href.value = fileName
				node.attributes.append(href)

				rel = ShotAttribute(name="rel")
				rel.value = "\"stylesheet\""
				node.attributes.append(rel)

				return node
			elif fileExt == "js":
				node = ShotNode(tag="script",depth=self.getDepth(),parent=self.currentNode)
			
				src = ShotAttribute(name="src")
				src.value = fileName
				node.attributes.append(src)
			
				return node
			else:
				self.parseError("couldn't find file extension on " + ("fetch" if fetch else "includ") + "ed file")

	def getBreakElement(self):
		self.getNextToken()
	
		if self.currentToken.type == ShotToken.typeNumber:
			node = ShotNode(tag="",depth=self.getDepth(),parent=self.currentNode)
			for i in range(int(self.currentToken.value)):
				node.children.append(ShotNode(tag="br",parent=self.currentNode,selfClosing=True))

		else:
			node = ShotNode(tag="br",depth=self.getDepth(),parent=self.currentNode)
			node.selfClosing = True
			
		return node

	def getText(self):
		node = ShotTextNode(self.currentToken.value,depth=self.getDepth())
		self.currentNode.children.append(node)

	def getDirective(self,closing=False):
		node = ShotNode(tag="templateDirective",depth=self.getDepth(),parent=self.currentNode)
		
		text = self.currentToken.value
		
		if closing:
			keyword = text.split(" ")[0]
		else:
			keyword = ""
		attr = ShotAttribute(name=keyword,value=text)
		node.attributes.append(attr)

		self.currentNode.children.append(node)
		self.currentNode = node
		
	def getComment(self):
		node = ShotTextNode(text="<!-- "+self.currentToken.value+" -->",depth=self.getDepth())
		self.currentNode.children.append(node)

	def getBlockComment(self):
		commentBody = []
		
		self.getNextToken()
		while self.currentToken.type != ShotToken.typeEOL:
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

		return ShotTextNode(text="<!--\n"+"".join(commentBody)+"-->",depth=commentDepth)

	def getNodeWithTag(self):
		if self.currentToken.value == "comment":
			node = self.getBlockComment()

		else:
			if self.included or self.bodyCreated:
				self.lookingForHead = False
				self.fillingHead = False
		
			elif self.lookingForHead:
				if self.currentToken.value == "head":
					self.lookingForHead = False
				elif self.currentToken.value != "doctype" and self.currentToken.value != "html":
					headElement = ShotNode(tag="head",depth=-1,parent=self.currentNode)
					self.currentNode.children.append(headElement)
					self.currentNode = headElement
			
					self.lookingForHead = False
				
					if self.currentToken.value not in self.tagsForHead:
						self.fillingHead = False
						self.currentNode = self.currentNode.parent
						if self.currentToken.value != "body":
							bodyElement = ShotNode(tag="body",depth=-1,parent=self.currentNode)
							self.currentNode.children.append(bodyElement)
							self.currentNode = bodyElement
						
						self.bodyCreated = True

			elif self.fillingHead:
				if self.currentToken.value not in self.tagsForHead:
					self.fillingHead = False
					self.currentNode = self.currentNode.parent
					if self.currentToken.value != "body":
						bodyElement = ShotNode(tag="body",depth=-1,parent=self.currentNode)
						self.currentNode.children.append(bodyElement)
						self.currentNode = bodyElement

					self.bodyCreated = True
	
			if self.currentToken.value == "include":
				node = self.includeFile()

			elif self.currentToken.value == "fetch":
				node = self.includeFile(fetch=True)

			elif self.currentToken.value == "media":
				node = self.getMediaElement()

			elif self.currentToken.value == "link":
				node = seld.getLinkElement()
				
			elif self.currentToken.value == "favicon":
				node = seld.getFaviconElement()

			elif self.currentToken.value == "br":
				node = self.getBreakElement()

			elif self.currentToken.value == "style" or self.currentToken.value == "css":
				node = self.getStyleElement()

			elif self.currentToken.value == "script" or self.currentToken.value == "js" or self.currentToken.value == "javascript":
				node = self.getScriptElement()

			else:
				node = ShotNode(tag=self.currentToken.value,depth=self.getDepth(),parent=self.currentNode)
				self.currentNode.children.append(node)
				self.currentNode = node
				node = None
				
				blockText = False
				
				self.getNextToken()
				while self.currentToken.type != ShotToken.typeEOL:
					
					if self.currentToken.type == ShotToken.typeAlpha:
						attr = ShotAttribute(name=self.currentToken.value)
						self.getNextToken()
						
						if self.currentToken.type == ShotToken.typeEquals:
							self.getNextToken()
							attr.value = self.currentToken.value
						
						self.currentNode.attributes.append(attr)
					
					elif self.currentToken.type == ShotToken.typeClass:
						self.currentNode.classes.append(self.currentToken.value)
					
					elif self.currentToken.type == ShotToken.typeID:
						self.currentNode.id = self.currentToken.value
					
					elif self.currentToken.type == ShotToken.typeText:
						if self.currentToken.value == "":
							blockText = True
						else:
							self.currentNode.children.append(ShotTextNode(text=self.currentToken.value))
							self.currentNode.multiline = False
						break
						
					elif self.currentToken.type == ShotToken.typeChildElemNext:
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

		if self.currentToken.type == ShotToken.typeAlpha:
			self.getNodeWithTag()

		elif self.currentToken.type == ShotToken.typeClass:
			self.currentToken = ShotToken(value="div")
			self.currentTokenNum = 0
			self.getNodeWithTag()

		elif self.currentToken.type == ShotToken.typeID:
			self.currentToken = ShotToken(value="div")
			self.currentTokenNum = 0
			self.getNodeWithTag()

		elif self.currentToken.type == ShotToken.typeComment:
			self.getComment()

		else:
			if not self.bodyCreated:
				head = ShotNode(tag="head",depth=-1,parent=self.currentNode)
				self.currentNode.children.append(head)

				body = ShotNode(tag="body",depth=-1,parent=self.currentNode)
				self.currentNode.children.append(body)

				self.currentNode = body
				self.bodyCreated = True
		
			if self.currentToken.type == ShotToken.typeText:
				self.getText()

			elif self.currentToken.type == ShotToken.typeDirective:
				self.getDirective()
				
			elif self.currentToken.type == ShotToken.typeDirectiveWithClosing:
				self.getDirective(closing=True)
			
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
