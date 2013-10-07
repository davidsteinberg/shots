#-------------------------
# Imports
#-------------------------

from shutil import copyfile
from os import remove
from os import listdir
from os.path import isfile, join

from flask import render_template

import re
import sys

#-------------------------
# Debugging
#-------------------------

debugging = False

def printTier(string, num=0):
	global debugging
	if not debugging:
		return

	for i in range(num):
		print "    ",
	print string

def logDigestion(eaten):
	printTier("- eat " + eaten,1)

def logCreation(tag):
	printTier("make " + tag)

def logFinishedCreation(tag):
	printTier("finished making " + tag)

#-------------------------
# AST Parts
#-------------------------

class ElementAttribute:
	def __init__(self, name, value=None):
		self.name = name
		self.value = value
	
	def __str__(self):
		result = self.name
		if self.value:
			 result += "=" + self.value
		return result

class TextNode:
	def __init__(self, text):
		self.text = text
	
	def __str__(self):
		return self.text

class PageElement:
	def __init__(self, tag=None, parent=None, id=None, selfClosing=False):
		self.id = id
		self.tag = tag
		self.classes = []
		self.attributes = []
		self.parent = parent
		self.children = []
		self.selfClosing = selfClosing
		
		self.makingAnID = False
		self.lookingForAttributes = False
		self.addingClasses = False
		self.elementHasID = False
		self.definingInnerHTML = False
		self.makingStyleOrScript = False
		self.addingDelimiter = False
		self.addingDirective = False
		self.makingLiteralTextBlock = False
		self.willBeMakingLiteralTextBlock = False
		self.makingSrcOrHref = False

	def __str__(self):
		result = "<" + self.tag
		if self.id:
			result += " id=\"" + self.id + "\""
		if len(self.classes) > 0:
			result += " class=\"" + " ".join(self.classes) + "\""
		if len(self.attributes) > 0:
			for a in self.attributes:
				result += " " + str(a)
		result += ">"
		if not self.selfClosing:
			if len(self.children) > 0:
				for c in self.children:
					if isinstance(c,TextNode):
						result += str(c)
					else:
						result += "\n"
						result += str(c)
			result += "</" + self.tag + ">"
		result += "\n"
		return result

#-------------------------
# Shot
#-------------------------

class Shot:
	def __init__(self, fileName):
		self.fileName = fileName
		self.currentPosInCode = 0

		self.lastChar = " "
		self.currentToken = []
		self.currentTokenType = ""
		self.prevTokenType = ""
		
		self.delimiters = {
			"block" : ["`"],
			"line" : [":"],
			"class" : ["."],
			"id" : ["#"],
			"equals" : ["="],
			"comment" : ["!"],
			"directive" : ["@"],
		}

		self.extending = False
		
		self.selfClosers = ["area", "base", "br", "col", "command", "doctype", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source", "track", "wbr"]
		
		self.currentNode = self.rootNode = PageElement(tag="document")
		
		self.__EOF__ = "@ EOF @"

		f = open("templates/"+fileName,"r")
		self.code = f.read() + "\n"
		self.codeLen = len(self.code)		
		f.close()
		
		self.parseSource()
		
		genFile = open("templates/shot."+fileName,"w")	
		genFile.write(self.generateCode())
		genFile.close()

	def parseError(self,string):
		exit("Parse Error at char " + str(self.currentPosInCode) + ": " + string)

	def getChar(self):
		if self.currentPosInCode >= self.codeLen:
			return self.__EOF__
		c = self.code[self.currentPosInCode]
		self.currentPosInCode += 1
		return c

	def makeDirective(self):
		logCreation("directive")
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
		self.currentNode.children.append(TextNode("".join(directive)))
		
		self.currentNode.addingDirective = False
		logFinishedCreation("directive")

	def addDelimiter(self):
		logCreation("delimiter")
		self.currentNode.addingDelimiter = True
		self.getNextToken()
		delim = self.currentToken
		self.getNextToken()
		while self.currentTokenType != "newline":
			self.delimiters[delim].append(self.currentToken)
			self.getNextToken()
		
		self.currentNode.addingDelimiter = False
		logFinishedCreation("delimiter")

	def makeAttribute(self,name):
		logCreation("attribute " + name)
		newAttr = ElementAttribute(name=name)
		if name == "href" or name == "src":
			self.currentNode.makingSrcOrHref = True
		self.getNextToken()
		if self.currentTokenType == "equals":
			self.getNextToken()
			if self.currentTokenType != "quote":
				self.parseError("expected value for attribute")
			newAttr.value = self.currentToken
		self.currentNode.attributes.append(newAttr)
		self.currentNode.makingSrcOrHref = False
		logFinishedCreation("attribute " + name)

	def makeElementWithID(self,id):
		logCreation("id "+id)
		newNode = PageElement(id=id,parent=self.currentNode)
		self.currentNode.children.append(newNode)
		self.currentNode = newNode
		self.currentNode.elementHasID = True
		logFinishedCreation("id "+id)

	def makeBreakElement(self):
		newNode = PageElement(tag="br",parent=self.currentNode)
		self.currentNode.children.append(newNode)
		self.currentNode = newNode
	
		self.currentNode.selfClosing = True
	
		self.getNextToken()
	
		if self.currentTokenType == "digit":
			for i in range(int(self.currentToken)-1):
				self.currentNode.parent.children.append(PageElement(tag="br",parent=self.currentNode,selfClosing=True))
			self.getNextToken()
			if self.currentTokenType == "newline" or self.currentToken == self.__EOF__:
				self.currentToken = "1"
	
		self.currentNode = self.currentNode.parent

		return
	
	def makeBlockComment(self):
		self.currentNode.makingStyleOrScript = True

		commentBody = ["<!-- "]

		self.getNextToken()
		while self.currentTokenType != "block":	
			commentBody.append(self.currentToken)
			self.getNextToken()
		
		self.getNextToken() # gobble the slash
		
		commentBody.append(" -->\n")
		self.currentNode.children.append(TextNode("".join(commentBody)))
		
		self.currentNode.makingStyleOrScript = False
	
	def makeStyleElement(self):
		newNode = PageElement(tag="style",parent=self.currentNode)
		self.currentNode.children.append(newNode)
		self.currentNode = newNode
		
		self.currentNode.lookingForAttributes = True
		self.getNextToken()
		
		styleBody = []
		
		# block
		if self.currentTokenType == "newline":
			self.currentNode.lookingForAttributes = False
			self.currentNode.makingStyleOrScript = True
			
			while self.currentTokenType != "block":
				self.getNextToken()
				styleBody.append(self.currentToken)
			
			self.getNextToken() # gobble the slash
		
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
			self.currentNode.children.append(TextNode(text="\n"+"".join(styleBody[:-1])))
		self.currentNode = self.currentNode.parent
	
	def makeScriptElement(self):
		newNode = PageElement(tag="script",parent=self.currentNode)
		self.currentNode.children.append(newNode)
		self.currentNode = newNode
		
		self.currentNode.lookingForAttributes = True
		
		scriptBody = []
		
		self.getNextToken()
		
		# block
		if self.currentTokenType == "newline":
			self.currentNode.lookingForAttributes = False
			self.currentNode.makingStyleOrScript = True
			
			while self.currentTokenType != "block":
				self.getNextToken()
				scriptBody.append(self.currentToken)
			
			self.getNextToken() # gobble the slash
		
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
			self.currentNode.children.append(TextNode(text="\n"+"".join(scriptBody[:-1])))
		self.currentNode = self.currentNode.parent
		
	def makeElementWithTag(self,tag):
		logCreation(tag)
		if tag == "br":
			self.makeBreakElement()
		
		elif tag == "style" or tag == "css":
			self.makeStyleElement()
		
		elif tag == "script" or tag == "js" or tag == "javascript":
			self.makeScriptElement()
		
		elif tag == "comment":
			self.makeBlockComment()
		
		else:
			if self.currentNode.elementHasID:
				self.currentNode.tag = tag
			else:
				newNode = PageElement(tag=tag,parent=self.currentNode)
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

			while self.currentTokenType != "newline":
				if self.currentTokenType == "line":
					self.currentNode.lookingForAttributes = False
					self.currentNode.definingInnerHTML = True

					if self.currentNode.willBeMakingLiteralTextBlock:
						break
				
				self.getNextToken()

			if self.currentNode.willBeMakingLiteralTextBlock:
				self.currentNode.willBeMakingLiteralTextBlock = False
				self.currentNode.makingLiteralTextBlock = True
				self.currentNode.lookingForAttributes = False

				logCreation("literal text block")
				if self.currentNode.definingInnerHTML:
					stopper = "newline"
				else:
					stopper = "block"
			
				elemBody = []
				self.getNextToken()
				while self.currentTokenType != stopper:
					elemBody.append(self.currentToken)
					self.getNextToken()

				self.currentNode.children.append(TextNode(''.join(elemBody).strip()))
				
				self.currentNode = self.currentNode.parent
				
				logFinishedCreation("literal text block")
				logFinishedCreation(tag)
				
				return

			self.currentNode.lookingForAttributes = False
			if not self.currentNode.definingInnerHTML and not self.currentNode.selfClosing:
				self.currentNode.definingInnerHTML = True
				while self.currentTokenType != "block":
					self.getNextToken()
				self.getNextToken()
			
			self.currentNode.definingInnerHTML = False
			self.currentNode.lookingForAttributes = False
			
			self.currentNode = self.currentNode.parent

		logFinishedCreation(tag)
	
	#-------------------------
	# Get Token
	#-------------------------

	def getToken(self):

		self.prevTokenType = self.currentTokenType

		# gobble up spaces and tabs, but NOT newlines
		while self.lastChar == " " or self.lastChar == "\t":
			prevChar = self.lastChar
			self.lastChar = self.getChar()
			if self.currentNode.makingStyleOrScript or self.currentNode.addingDirective or self.currentNode.makingLiteralTextBlock:
				return prevChar
		
		# newline
		if self.lastChar == "\n":		
			logDigestion("newline")
			self.currentTokenType = "newline"
			self.lastChar = self.getChar()
			return "\n"
		
		# alpha
		elif self.lastChar.isalpha() or self.lastChar == '_':
			logDigestion("alpha")
			self.currentTokenType = "alpha"

			identifierString = []
			while self.lastChar.isalnum() or self.lastChar == "_" or self.lastChar == "-": # TODO - this is too broad i think
				identifierString.append(self.lastChar)
				self.lastChar = self.getChar()

			identifier = ''.join(identifierString)

			printTier(identifier,2)
			
			if self.currentNode.makingStyleOrScript or self.currentNode.addingDelimiter or self.currentNode.addingDirective or self.currentNode.makingLiteralTextBlock:
				return identifier
	
			if self.currentNode.makingAnID:
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

			else:
				for delim in self.delimiters:
					for symbol in self.delimiters[delim]:
						if identifier == symbol:
							self.currentTokenType = delim
							return symbol
				
				self.makeElementWithTag(identifier)
		
		# numbers
		elif self.lastChar.isdigit():
			logDigestion("digit")
			self.currentTokenType = "digit"

			numberString = []
			while self.lastChar.isdigit():
				numberString.append(self.lastChar)
				self.lastChar = self.getChar()
			
			number = "".join(numberString)
			printTier(number,2)
			
			return number

		# quotes
		elif self.lastChar == "\"" or self.lastChar == "'":
			logDigestion("quote")
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

			printTier(quote,2)

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
					printTier("will make literal text block")
					self.currentNode.willBeMakingLiteralTextBlock = True
			elif self.currentNode.makingStyleOrScript or self.currentNode.addingDirective or self.currentNode.makingLiteralTextBlock:
				return quoteChar + quote + quoteChar
			elif self.currentNode.definingInnerHTML:
				newNode = TextNode(quote)
				self.currentNode.children.append(newNode)
			elif self.currentNode.addingClasses:
				printTier("will make literal text block")
				self.currentNode.willBeMakingLiteralTextBlock = True
			else:
				newNode = TextNode(quote)
				self.currentNode.children.append(newNode)

		# adjustable symbols
		
		elif self.lastChar in self.delimiters["block"]:

			# if making style or script
			# check if its escaped
			
			logDigestion("block")
			self.currentTokenType = "block"
			result = self.lastChar
			self.lastChar = self.getChar()
			return result
		
		elif self.lastChar in self.delimiters["line"]:

			# if making style or script
			# check if its escaped
		
			logDigestion("line")
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
			logDigestion("class")
			self.currentTokenType = "class"
			result = self.lastChar
			self.lastChar = self.getChar()
			return result
				
		elif self.lastChar in self.delimiters["equals"]:
			logDigestion("equals")
			self.currentTokenType = "equals"
			result = self.lastChar
			self.lastChar = self.getChar()
			return result
		
		elif self.lastChar in self.delimiters["id"]:
			logDigestion("id")
			self.currentTokenType = "id"
			self.currentNode.makingAnID = True
			result = self.lastChar
			self.lastChar = self.getChar()
			return result
		
		elif self.lastChar in self.delimiters["directive"]:
			logDigestion("directive")
			self.currentTokenType = "directive"
			self.lastChar = self.getChar()
			if not self.currentNode.addingDirective:
				self.makeDirective()
		
		elif self.lastChar in self.delimiters["comment"]:
			logDigestion("comment")
			comment = ["\n<!-- "]

			self.lastChar = self.getChar()
			while self.lastChar != self.__EOF__ and self.lastChar != "\n":
				comment.append(self.lastChar)
				self.lastChar = self.getChar()
			
			comment.append(" -->\n")
			self.currentNode.children.append(TextNode("".join(comment)))
			
			if self.lastChar != self.__EOF__:
				return self.getToken()
		
		elif self.lastChar == self.__EOF__:
			logDigestion(self.__EOF__)
			self.currentTokenType = self.__EOF__
			return self.__EOF__
		
		else:
			self.currentTokenType = " - unknown - "
			result = self.lastChar
			self.lastChar = self.getChar()
			return result

	def getNextToken(self):
		self.currentToken = self.getToken()

	def parseSource(self):
		while self.currentTokenType != self.__EOF__:
			if debugging:
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
				if kids[0].tag == "doctype":
					kids[0].tag = "!doctype"
					for k in kids:
						result += str(k)
				else:
					result = "<!doctype html>\n"
					if kids[0].tag != "html":
						newNode = PageElement(tag="html")
						for k in kids:
							newNode.children.append(k)
						result += str(newNode)
					else:
						for k in kids:
							result += str(k)

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
	global debugging

	if len(sys.argv) < 2:
		exit(sys.argv[0] + " requires at least file name as a parameter, optional debug flag\nUsage : " + sys.argv[0] + " <filename> [-d]")
	elif len(sys.argv) > 2:
		if sys.argv[2] == "-d":
			debugging = True

	fileName = sys.argv[1]

	s = Shot(fileName)
	print s.generateCode()

if __name__ == "__main__":
	main()
