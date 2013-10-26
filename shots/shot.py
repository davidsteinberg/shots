#-------------------------
# Shot
#-------------------------

from shutil import copyfile
from os import listdir, remove, sep, walk
from os.path import abspath, dirname, isfile, join, splitext

from ast import *

from flask import render_template

import re
import sys

class Shot(object):
	def __init__(self, fileName, included=False, debug=False):
		self.debugging = debug
		
		self.fileName = fileName
		self.included = included

		self.currentPosInCode = 0
		self.currentLineNum = 0
		self.currentCharNum = 0
		self.currentLineDepth = 0
		self.findingCurrentLineDepth = False

		self.lastChar = " "
		self.currentToken = []
		self.currentTokenType = ""
		self.prevTokenType = ""
		
		self.delimiters = {
			"line" : [":"],
			"class" : ["."],
			"id" : ["#"],
			"equals" : ["="],
			"comment" : ["!"],
			"directive" : ["@"],
		}

		self.extending = False
		
		self.selfClosers = ["area", "base", "br", "col", "command", "doctype", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source", "track", "wbr"]
		
		self.currentNode = self.rootNode = PageElement(tag="document",depth=-1,multiline=True)
		
		self.lookingForHead = True
		self.fillingHead = True
		
		self.tagsForHead = ["base", "comment", "css", "fetch", "include", "js", "javascript", "link", "meta", "noscript", "script", "style", "title"]
		
		self.__EOF__ = "@ EOF @"

		f = open("templates/"+fileName,"r")
		self.code = re.sub(r"\n\s*\n", "\n", f.read()) + "\n"
		self.codeLen = len(self.code)
		f.close()
		
		self.parseSource()
		
		genFile = open("templates/shot."+fileName,"w")	
		genFile.write(self.generateCode())
		genFile.close()

	def parseError(self,string):
		exit("Parse Error on line " + str(self.currentLineNum+1) + ", char " + str(self.currentCharNum+1) + " : " + string)

	def getChar(self):
		if self.currentPosInCode >= self.codeLen:
			return self.__EOF__
		c = self.code[self.currentPosInCode]
		self.currentPosInCode += 1
		self.currentCharNum += 1
		return c

	def makeDirective(self):
		self.logCreation("directive")
		directive = ["\n{%"]
		self.currentNode.addingDirective = True
		self.getNextToken()

		while self.currentTokenType != "alpha":
			directive.append(self.currentToken)
			self.getNextToken()

		beginningWord = self.currentToken

		while self.currentTokenType != "newline":
			if self.currentToken == "extends":
				self.extending = True
				directive.append(self.currentToken)
				self.getNextToken()
				while self.currentTokenType != "quote":
					directive.append(self.currentToken)
					self.getNextToken()

				fileName = self.currentToken[1:-1]
				s = Shot(fileName)
				directive.append("'shot."+fileName+"'")
			
			elif self.currentTokenType == "directive":
				directive.append(" %} {% end"+beginningWord)
			else:
				directive.append(self.currentToken)
			
			self.getNextToken()
		
		directive.append(" %}\n")
		self.currentNode.children.append(TextNode("".join(directive),depth=self.currentLineDepth))
		
		self.currentNode.addingDirective = False
		self.logFinishedCreation("directive")

	def addDelimiter(self):
		self.logCreation("delimiter")
		self.currentNode.addingDelimiter = True
		self.getNextToken()
		delim = self.currentToken
		self.getNextToken()
		while self.currentTokenType != "newline":
			self.delimiters[delim].append(self.currentToken)
			self.getNextToken()
		
		self.currentNode.addingDelimiter = False
		self.logFinishedCreation("delimiter")

	def makeAttribute(self,name):
		self.logCreation("attribute " + name)
		newAttr = ElementAttribute(name=name)
		if name == "href" or name == "src" or "action":
			self.currentNode.makingSrcOrHref = True
		self.getNextToken()
		if self.currentTokenType == "equals":
			self.getNextToken()
			if self.currentTokenType != "quote":
				self.parseError("expected value for attribute")
			newAttr.value = self.currentToken
		self.currentNode.attributes.append(newAttr)
		self.currentNode.makingSrcOrHref = False
		self.logFinishedCreation("attribute " + name)

	def makeElementWithID(self,id):
		self.logCreation("id "+id)
		futureDepth = 0
		if self.currentNode.multiline:
			futureDepth = self.currentLineDepth			
		newNode = PageElement(id=id,parent=self.currentNode,depth=futureDepth)
		self.currentNode.children.append(newNode)
		self.currentNode = newNode
		self.currentNode.elementHasID = True
		self.logFinishedCreation("id "+id)

	def makeBreakElement(self):
		futureDepth = 0
		if self.currentNode.multiline:
			futureDepth = self.currentLineDepth
		newNode = PageElement(tag="br",parent=self.currentNode,depth=futureDepth)
		self.currentNode.children.append(newNode)
		self.currentNode = newNode
	
		self.currentNode.selfClosing = True
	
		self.getNextToken()
	
		if self.currentTokenType == "digit":
			for i in range(int(self.currentToken)-1):
				self.currentNode.parent.children.append(PageElement(tag="br",parent=self.currentNode,selfClosing=True,depth=futureDepth))
			self.getNextToken()
			if self.currentTokenType == "newline" or self.currentToken == self.__EOF__:
				self.currentToken = "1"
	
		self.currentNode = self.currentNode.parent

		return

	def replaceText(self):
		# get strings before and after with
		# replace before with after in code
		
		before = []
		after = []
		
		self.lastChar = self.getChar()
		while self.lastChar == ' ' or self.lastChar == '\t':
			self.lastChar = self.getChar()
		
		quoteChar = self.lastChar
		
		self.lastChar = self.getChar()
		while self.lastChar != quoteChar:
			before.append(self.lastChar)
			self.lastChar = self.getChar()
			if self.lastChar == quoteChar and before[-1] == "\\":
				before = quoteString[:-1]
				before.append(quoteChar)
				self.lastChar = self.getChar()

		beforeString = ''.join(before)

		self.lastChar = self.getChar()
		while self.lastChar != '"' and self.lastChar != '\'':
			self.lastChar = self.getChar()

		quoteChar = self.lastChar
					
		self.lastChar = self.getChar()
		while self.lastChar != quoteChar:
			after.append(self.lastChar)
			self.lastChar = self.getChar()
			if self.lastChar == quoteChar and after[-1] == "\\":
				after = after[:-1]
				after.append(quoteChar)
				self.lastChar = self.getChar()

		afterString = ''.join(after)

		self.lastChar = self.getChar()
		while self.lastChar != '\n':
			self.lastChar = self.getChar()

		self.code = self.code[self.currentPosInCode:].replace(beforeString,afterString)
		self.currentPosInCode = 0
		self.codeLen = len(self.code)
	
	def includeFile(self,fetch=False):
		fileName = []
		fileExt = []
		
		self.lastChar = self.getChar()
		while self.lastChar != '\n':
			if self.lastChar != '"' and self.lastChar != '\'':
				fileName.append(self.lastChar)
				if self.lastChar == '.':
					del fileExt[:]
				else:
					fileExt.append(self.lastChar)
			self.lastChar = self.getChar()
		
		fileNameString = ''.join(fileName).strip()
		fileExtString = ''.join(fileExt).strip()
		
		if fileExtString == "html":
			s = Shot(fileNameString,included=True)
			for kid in s.rootNode.children:
				self.currentNode.children.append(kid)
		else:
			if fetch:
				found = False
				currentDir = dirname(abspath(__file__))
				for root, dirs, files in walk(currentDir):
					if fileNameString in files:
						found = True
						fileNameString = root.replace(currentDir, "", 1) + sep + fileNameString
						break
				if not found:
					self.parseError("couldn't fetch file " + fileNameString)
		
			fileNameString = '"' + fileNameString + '"'
		
			if fileExtString == "css":			
				newNode = PageElement(tag="link",parent=self.currentNode,selfClosing=True)

				href = ElementAttribute(name="href")
				href.value = fileNameString
				newNode.attributes.append(href)

				rel = ElementAttribute(name="rel")
				rel.value = "\"stylesheet\""
				newNode.attributes.append(rel)

				self.currentNode.children.append(newNode)
			elif fileExtString == "js":
				newNode = PageElement(tag="script",parent=self.currentNode)
			
				src = ElementAttribute(name="src")
				src.value = fileNameString
				newNode.attributes.append(src)
			
				self.currentNode.children.append(newNode)
			else:
				self.parseError("couldn't find file extension on included file")
	
	def makeBlockComment(self):
		futureDepth = 0
		if self.currentNode.multiline:
			futureDepth = self.currentLineDepth
		newNode = PageElement(tag="command",parent=self.currentNode,depth=futureDepth)
		self.currentNode = newNode
		
		self.currentNode.makingStyleOrScript = True

		commentBody = ["<!--\n"]

		self.getNextToken()
		while not self.currentNode.finished:
			self.getNextToken()
			if self.currentNode.finished:
				break
			else:
				commentBody.append(self.currentToken)
		
		self.currentNode = self.currentNode.parent
		
		commentBody.append(" -->")
		self.currentNode.children.append(TextNode("".join(commentBody),depth=self.currentLineDepth))
	
	def makeStyleElement(self):
		futureDepth = 0
		if self.currentNode.multiline:
			futureDepth = self.currentLineDepth
		newNode = PageElement(tag="style",parent=self.currentNode,depth=futureDepth)
		self.currentNode.children.append(newNode)
		self.currentNode = newNode
		
		self.currentNode.lookingForAttributes = True
		self.getNextToken()
		
		styleBody = []
		
		# block
		if self.currentTokenType == "newline":
			self.currentNode.lookingForAttributes = False
			self.currentNode.makingStyleOrScript = True
			self.currentNode.multiline = True
			
			while not self.currentNode.finished:
				self.getNextToken()
				if self.currentNode.finished:
					break
				else:
					styleBody.append(self.currentToken)
		
		# inline
		elif self.currentTokenType == "line":
			self.currentNode.lookingForAttributes = False
			self.currentNode.makingStyleOrScript = True
			while self.currentTokenType != "newline":
				self.getNextToken()
				styleBody.append(self.currentToken)
			styleBody.append(self.currentToken)
		
		# style reference
		else:
			self.currentNode.tag = "link"
			self.currentNode.selfClosing = True

			newAttr = ElementAttribute(name="rel")
			newAttr.value = "\"stylesheet\""
			self.currentNode.attributes.append(newAttr)
		
			while self.currentTokenType != "newline":
				self.getNextToken()
				
			for a in self.currentNode.attributes:
				if a.name == "src":
					a.name = "href"
		
		if len(styleBody) > 0:
			self.currentNode.children.append(TextNode(text="\n"+"".join(styleBody[:-1]),depth=self.currentLineDepth))
		if self.currentNode.finished:
			while self.currentLineDepth <= self.currentNode.depth:
				self.currentNode = self.currentNode.parent
		else:
			self.currentNode = self.currentNode.parent

	
	def makeScriptElement(self):
		futureDepth = 0
		if self.currentNode.multiline:
			futureDepth = self.currentLineDepth
		newNode = PageElement(tag="script",parent=self.currentNode,depth=futureDepth)
		self.currentNode.children.append(newNode)
		self.currentNode = newNode
		
		self.currentNode.lookingForAttributes = True
		
		scriptBody = []
		
		self.getNextToken()
		
		# block
		if self.currentTokenType == "newline":
			self.currentNode.lookingForAttributes = False
			self.currentNode.makingStyleOrScript = True
			self.currentNode.multiline = True
			
			while not self.currentNode.finished:
				self.getNextToken()
				if self.currentNode.finished:
					break
				else:
					scriptBody.append(self.currentToken)
		
		# inline
		elif self.currentTokenType == "line":
			self.currentNode.lookingForAttributes = False
			self.currentNode.makingStyleOrScript = True
			while self.currentTokenType != "newline":
				self.getNextToken()
				scriptBody.append(self.currentToken)
			scriptBody.append(self.currentToken)
		
		# script reference
		else:
			while self.currentTokenType != "newline":
				self.getNextToken()
		
		if len(scriptBody) > 0:
			self.currentNode.children.append(TextNode(text="\n"+"".join(scriptBody[:-1]),depth=self.currentLineDepth))
		if self.currentNode.finished:
			while self.currentLineDepth <= self.currentNode.depth:
				self.currentNode = self.currentNode.parent
		else:
			self.currentNode = self.currentNode.parent
		
	def makeElementWithTag(self,tag):
		self.logCreation(tag)
		if tag == "br":
			self.makeBreakElement()
		
		elif tag == "style" or tag == "css":
			self.makeStyleElement()
		
		elif tag == "script" or tag == "js" or tag == "javascript":
			self.makeScriptElement()
		
		elif tag == "comment":
			self.makeBlockComment()

		elif tag == "include":
			self.includeFile()
			
		elif tag == "fetch":
			self.includeFile(fetch=True)

		else:
			if self.currentNode.elementHasID:
				self.currentNode.tag = tag
			else:
				futureDepth = 0
				if self.currentNode.multiline:
					futureDepth = self.currentLineDepth
				newNode = PageElement(tag=tag,parent=self.currentNode,depth=futureDepth)
				self.currentNode.children.append(newNode)
				self.currentNode = newNode

			self.currentNode.elementHasID = False

			if tag in self.selfClosers:
				self.currentNode.selfClosing = True

			self.currentNode.addingClasses = True

			self.getNextToken()
			if self.currentTokenType == "class":
				while self.currentTokenType == "class" or self.currentTokenType == "alpha":
					self.getNextToken()
			
			self.currentNode.addingClasses = False
			self.currentNode.lookingForAttributes = True

			self.currentNode.multiline = True
			while self.currentTokenType != "newline":
				if self.currentTokenType == "line":
					self.currentNode.multiline = False
					self.currentNode.lookingForAttributes = False
					self.currentNode.definingInnerHTML = True

					if self.currentNode.willBeMakingLiteralTextBlock:
						break
				
				self.getNextToken()

			if self.currentNode.willBeMakingLiteralTextBlock:
				self.currentNode.willBeMakingLiteralTextBlock = False
				self.currentNode.makingLiteralTextBlock = True
				self.currentNode.lookingForAttributes = False

				self.logCreation("literal text block")
				
				elemBody = []
				self.getNextToken()
				
				if self.currentNode.definingInnerHTML:
					while self.currentTokenType != "newline":
						elemBody.append(self.currentToken)
						self.getNextToken()					
				else: # block
					while not self.currentNode.finished:
						elemBody.append(self.currentToken)
						self.getNextToken()

				self.currentNode.children.append(TextNode(''.join(elemBody).strip()))
				
				if self.currentNode.finished:
					while self.currentLineDepth <= self.currentNode.depth:
						self.currentNode = self.currentNode.parent
				else:
					self.currentNode = self.currentNode.parent
				
				self.logFinishedCreation("literal text block")
				self.logFinishedCreation(tag)
				
				return

			self.currentNode.lookingForAttributes = False
			if not self.currentNode.definingInnerHTML and not self.currentNode.selfClosing:
				self.currentNode.multiline = True
				self.currentNode.definingInnerHTML = True
				
				while self.currentTokenType != self.__EOF__ and self.currentNode.definingInnerHTML:
					self.getNextToken()

			else:
				self.currentNode = self.currentNode.parent
				self.logFinishedCreation(tag)
	
	#-------------------------
	# Get Token
	#-------------------------

	def getToken(self):

		self.prevTokenType = self.currentTokenType

		# gobble up spaces and tabs, but NOT newlines
		while self.lastChar == " " or self.lastChar == "\t":
			if self.findingCurrentLineDepth:
				self.currentLineDepth += 1
			prevChar = self.lastChar
			self.lastChar = self.getChar()
			if self.currentNode.makingStyleOrScript or self.currentNode.addingDirective or self.currentNode.makingLiteralTextBlock:
				return prevChar
		
		# newline
		if self.lastChar == "\n":
			self.logDigestion("newline")
			self.currentTokenType = "newline"

			self.currentLineNum += 1
			self.currentCharNum = 0
			self.currentLineDepth = 0
			self.findingCurrentLineDepth = True

			self.lastChar = self.getChar()
			return "\n"
		
		# ending a block
		if self.findingCurrentLineDepth:
			self.findingCurrentLineDepth = False
			while self.currentLineDepth <= self.currentNode.depth:
				self.logFinishedCreation(self.currentNode.tag)
				if self.currentNode.makingStyleOrScript or self.currentNode.makingLiteralTextBlock:
					self.currentNode.finished = True
					return
				else :
					self.currentNode = self.currentNode.parent
		
		# alpha
		if self.lastChar.isalpha() or self.lastChar == '_':
			self.logDigestion("alpha")
			self.currentTokenType = "alpha"

			identifierString = []
			while self.lastChar.isalnum() or self.lastChar == "_" or self.lastChar == "-": # TODO - this is too broad i think
				identifierString.append(self.lastChar)
				self.lastChar = self.getChar()

			identifier = ''.join(identifierString)

			self.printTier(identifier,2)
			
			if self.currentNode.makingStyleOrScript or self.currentNode.addingDelimiter or self.currentNode.addingDirective or self.currentNode.makingLiteralTextBlock:
				return identifier
	
			elif self.currentNode.makingAnID:
				self.currentNode.makingAnID = False
				self.makeElementWithID(identifier)
	
			elif self.currentNode.addingClasses:
				if self.prevTokenType == "class":
					self.currentNode.classes.append(identifier)
				else:
					for delim in self.delimiters:
						for symbol in self.delimiters[delim]:
							if identifier == symbol:
								self.currentTokenType = delim
								return symbol					
			
					self.currentNode.lookingForAttributes = True
					self.makeAttribute(identifier)
				
			elif self.currentNode.lookingForAttributes:
				for delim in self.delimiters:
					for symbol in self.delimiters[delim]:
						if identifier == symbol:
							self.currentTokenType = delim
							return symbol
				
				self.makeAttribute(identifier)

			elif identifier == "custom":
				self.addDelimiter()

			elif identifier == "replace":
				self.replaceText()

			else:
				for delim in self.delimiters:
					for symbol in self.delimiters[delim]:
						if identifier == symbol:
							self.currentTokenType = delim
							return symbol
				
				if self.included:
					self.lookingForHead = False
					self.fillingHead = False
					
				elif self.lookingForHead:
					if identifier == "head":
						self.lookingForHead = False
					elif identifier != "doctype" and identifier != "html":
						headElement = PageElement(tag="head",depth=-1,parent=self.currentNode)
						self.currentNode.children.append(headElement)
						self.currentNode = headElement
					
						self.lookingForHead = False
						
						if identifier not in self.tagsForHead:
							self.fillingHead = False
							self.currentNode = self.currentNode.parent
							if identifier != "body":
								bodyElement = PageElement(tag="body",depth=-1,parent=self.currentNode)
								self.rootNode.children.append(bodyElement)
								self.currentNode = bodyElement

				elif self.fillingHead:
					if identifier not in self.tagsForHead:
						self.fillingHead = False
						if identifier != "body":
							bodyElement = PageElement(tag="body",depth=-1,parent=self.currentNode)
							self.rootNode.children.append(bodyElement)
							self.currentNode = bodyElement
				
				self.makeElementWithTag(identifier)
		
		# numbers
		elif self.lastChar.isdigit():
			self.logDigestion("digit")
			self.currentTokenType = "digit"

			numberString = []
			while self.lastChar.isdigit():
				numberString.append(self.lastChar)
				self.lastChar = self.getChar()
			
			number = "".join(numberString)
			self.printTier(number,2)
			
			return number

		# quotes
		elif self.lastChar == "\"" or self.lastChar == "'":
			self.logDigestion("quote")
			self.currentTokenType = "quote"
			
			quoteChar = self.lastChar
			self.lastChar = self.getChar()
			
			quoteString = []
			while self.lastChar != quoteChar:
				quoteString.append(self.lastChar)
				if self.lastChar == quoteChar:
					if quoteString[-1] == "\\":
						if not self.lookingForAttributes:
							self.currentToken = self.currentToken[:-1]
				self.lastChar = self.getChar()
			self.lastChar = self.getChar()

			quote = ''.join(quoteString)

			self.printTier(quote,2)

			if self.currentNode.lookingForAttributes:
				if self.prevTokenType == "equals":
					if self.currentNode.makingSrcOrHref and quote[0] == '@':
						quoteChar = "\""
						newQuote = ["{{ url_for('"]
						c = 1
						while quote[c].isspace():
							c += 1
							
						dir = []
						while quote[c].isalnum() or quote[c] == '_' or quote[c] == '.' or quote[c] == '|' or quote[c] == '/' or quote[c].isspace():
							if quote[c] == '|':
								dir.append("' + ")
								c += 1
								while quote[c] != '|':
									dir.append(quote[c])
									c += 1
								dir.append(" + '")
							else:
								dir.append(quote[c])
							c += 1
							if c >= len(quote):
								break

						newQuote.append(("".join(dir)).strip())
	
						if c < len(quote):
							while quote[c].isspace():
								c += 1
								if c >= len(quote):
									break
	
							if quote[c] == ':':
								c += 1
								while quote[c].isspace():
									c += 1
								filename = []
								while quote[c].isalnum() or quote[c] == '_' or quote[c] == '.' or quote[c] == '|' or quote[c] == '/' or quote[c].isspace():
									if quote[c] == '|':
										filename.append("' + ")
										c += 1
										while quote[c] != '|':
											filename.append(quote[c])
											c += 1
										filename.append(" + '")
									else:
										filename.append(quote[c])
									c += 1
									if c >= len(quote):
										break
							newQuote.append("',filename='"+"".join(filename))
						
						quote = "".join(newQuote) + "') }}"
					return quoteChar + quote + quoteChar
				else:
					self.printTier("will make literal text block")
					self.currentNode.willBeMakingLiteralTextBlock = True
			elif self.currentNode.makingStyleOrScript or self.currentNode.addingDirective or self.currentNode.makingLiteralTextBlock:
				return quoteChar + quote + quoteChar
			elif self.currentNode.definingInnerHTML:
				if self.currentNode.multiline:
					self.currentNode.children.append(TextNode(quote,depth=self.currentLineDepth))
				else:
					self.currentNode.children.append(TextNode(quote))
			elif self.currentNode.addingClasses:
				self.printTier("will make literal text block")
				self.currentNode.willBeMakingLiteralTextBlock = True
			else:
				newNode = TextNode(quote,depth=self.currentLineDepth)
				self.currentNode.children.append(newNode)

		# adjustable symbols
		
		elif self.lastChar in self.delimiters["line"]:

			# if making style or script
			# check if its escaped
		
			self.logDigestion("line")
			self.currentTokenType = "line"
			result = self.lastChar
			self.lastChar = self.getChar()
			return result
		
		# return if you are making literals
		
		elif self.currentNode.addingDirective:
			for delim in self.delimiters:
				for symbol in self.delimiters[delim]:
					if self.lastChar == symbol:
						self.currentTokenType = delim
						self.lastChar = self.getChar()
						return symbol

			result = self.lastChar
			self.lastChar = self.getChar()
			return result			
		
		elif self.currentNode.makingStyleOrScript or self.currentNode.makingLiteralTextBlock:
			result = self.lastChar
			self.lastChar = self.getChar()
			return result
		
		# more adjustable symbols
		
		elif self.lastChar in self.delimiters["class"]:
			self.logDigestion("class")
			self.currentTokenType = "class"
			result = self.lastChar
			self.lastChar = self.getChar()
			return result
				
		elif self.lastChar in self.delimiters["equals"]:
			self.logDigestion("equals")
			self.currentTokenType = "equals"
			result = self.lastChar
			self.lastChar = self.getChar()
			return result
		
		elif self.lastChar in self.delimiters["id"]:
			self.logDigestion("id")
			self.currentTokenType = "id"
			self.currentNode.makingAnID = True
			result = self.lastChar
			self.lastChar = self.getChar()
			return result
		
		elif self.lastChar in self.delimiters["directive"]:
			self.logDigestion("directive")
			self.currentTokenType = "directive"
			self.lastChar = self.getChar()
			if not self.currentNode.addingDirective:
				self.makeDirective()
		
		elif self.lastChar in self.delimiters["comment"]:
			self.logDigestion("comment")
			comment = ["\n<!-- "]

			self.lastChar = self.getChar()
			while self.lastChar != self.__EOF__ and self.lastChar != "\n":
				comment.append(self.lastChar)
				self.lastChar = self.getChar()
			
			comment.append(" -->\n")
			self.currentNode.children.append(TextNode("".join(comment),depth=self.currentLineDepth))
			
			if self.lastChar != self.__EOF__:
				return self.getToken()
		
		elif self.lastChar == self.__EOF__:
			self.logDigestion(self.__EOF__)
			self.currentTokenType = self.__EOF__
			return self.__EOF__
		
		else:
			self.currentTokenType = " - unknown - "
			result = self.lastChar
			self.lastChar = self.getChar()
			return result

	def getNextToken(self):
		self.currentToken = self.getToken()

	def printTier(self,string, num=0):
		if not self.debugging:
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

	def parseSource(self):
		while self.currentTokenType != self.__EOF__:
			if self.debugging:
				print "\n-----------------------------------------"
				print " main loop call to get next token"
				print "-----------------------------------------\n"
			self.getNextToken()

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
						newNode = PageElement(tag="html",multiline=True)
						for k in kids:
							newNode.children.append(k)
						result += str(newNode)

		# last minute regex for template delimiters
		result = re.sub(r"\|([^|]+)\|",r"{{ \1 }}",result)
		return result
	
	def render(self,**varArgs):
		result = render_template("shot."+self.fileName, **varArgs)

		templates = [ f for f in listdir("templates") if isfile(join("templates",f)) ]
		for t in templates:
			if re.match("shot\..+",t):
				remove("templates/"+t)
		
		return result

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

	s = Shot(fileName,debug=debugging)
	print s.generateCode()

if __name__ == "__main__":
	main()
