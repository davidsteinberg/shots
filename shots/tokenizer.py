#-------------------------
# Tokenizer
#-------------------------

import re

class ShotToken:

	typeAlpha = 0
	typeArrayCloser = 1
	typeArrayOpener = 2
	typeClass = 3
	typeChildElemNext = 4
	typeComma = 5
	typeComment = 6
	typeDirective = 7
	typeDirectiveSelfClosing = 8
	typeEquals = 9
	typeEOL = 10
	typeID = 11
	typeNumber = 12
	typeQuote = 13
	typeText = 14
	typeUnknown = 15

	typeNumToName = [
		"typeAlpha",
		"typeArrayCloser",
		"typeArrayOpener",
		"typeClass",
		"typeChildElemNext",
		"typeComma",
		"typeComment",
		"typeDirective",
		"typeDirectiveSelfClosing",
		"typeEquals",
		"typeEOL",
		"typeID",
		"typeNumber",
		"typeQuote",
		"typeText",
		"typeUnknown"
	]

	def __init__(self,value="",type="unknown"):
		self.value = value
		self.type = type
	
	def __str__(self):
		return self.value

class ShotLine:
	def __init__(self,depth=0):
		self.depth = depth
		self.tokens = []

class ShotTokenizer:
	def __init__(self, fileName):

		self.fileName = fileName

		self.currentChar = " "		
		self.currentToken = None
		self.currentPosInLine = 0

		self.EOL = "$___$"

		self.currentLine = ""
		self.currentLineNum = 0
		self.currentLineLen = 0

		self.lines = []
		
	def getChar(self):
		if self.currentPosInLine >= self.currentLineLen:
			return self.EOL
		c = self.currentLine[self.currentPosInLine]
		if c == "\n" or c == "\r":
			return self.EOL
		self.currentPosInLine += 1
		return c
	
	def getNextChar(self):
		self.currentChar = self.getChar()

	def getToken(self):
		if self.currentChar == self.EOL:
			return ShotToken(type=ShotToken.typeEOL)
	
		# gobble whitespace
		while self.currentChar == " " or self.currentChar == "\t":
			self.getNextChar()
	
		# alpha
		if self.currentChar.isalpha() or self.currentChar == "_" or self.currentChar == "|":
			t = ShotToken(type=ShotToken.typeAlpha)
		
			identifier = [self.currentChar]

			templating = True if self.currentChar == "|" else False

			self.getNextChar()
			while self.currentChar.isalnum() or self.currentChar == "_" or self.currentChar == "-" or self.currentChar == "|" or templating:
				identifier.append(self.currentChar)
				if self.currentChar == "|":
					templating = not templating
				self.getNextChar()

			t.value = "".join(identifier)
		
		# number
		elif self.currentChar.isdigit():
			t = ShotToken(type=ShotToken.typeNumber)
		
			number = []
			while self.currentChar.isdigit():
				number.append(self.currentChar)
				self.getNextChar()
		
			t.value = "".join(number)

		# quote
		elif self.currentChar == "'" or self.currentChar == "\"":
			t = ShotToken(type=ShotToken.typeQuote)
		
			quoteChar = self.currentChar
			quote = [quoteChar]
			
			self.getNextChar()
			while self.currentChar != quoteChar:
				quote.append(self.currentChar)
				self.getNextChar()
				if self.currentChar == quoteChar:
					if quote[-1] == "\\":
						quote.append(self.currentChar)
						self.getNextChar()

			self.getNextChar()

			quote.append(quoteChar)
			t.value = "".join(quote)

		# text
		elif self.currentChar == ":":
			self.getNextChar()
			if self.currentChar == ":":
				self.getNextChar()
				t = ShotToken(type=ShotToken.typeChildElemNext)
			else:
				t = ShotToken(type=ShotToken.typeText)
			
				text = []
			
				if self.currentChar == self.EOL:
					t.value = ""
				else:
					self.getNextChar()
					while self.currentChar != self.EOL:
						text.append(self.currentChar)
						self.getNextChar()
			
					t.value = "".join(text)
		
		# class
		elif self.currentChar == ".":
			t = ShotToken(type=ShotToken.typeClass)
		
			className = []
			
			templating = False

			self.getNextChar()
			while self.currentChar.isalnum() or self.currentChar == "_" or self.currentChar == "-" or self.currentChar == "|" or templating:
				className.append(self.currentChar)
				if self.currentChar == "|":
					templating = not templating
				self.getNextChar()

			t.value = "".join(className)
	
		# id
		elif self.currentChar == "#":
			t = ShotToken(type=ShotToken.typeID)
			
			id = []

			templating = False

			self.getNextChar()
			while self.currentChar.isalnum() or self.currentChar == "_" or self.currentChar == "-" or self.currentChar == "|" or templating:
				id.append(self.currentChar)
				if self.currentChar == "|":
					templating = not templating
				self.getNextChar()

			t.value = "".join(id)
	
		# template directive
		elif self.currentChar == "-":
			self.getNextChar()
			
			if self.currentChar == "-":
				t = ShotToken(type=ShotToken.typeDirectiveSelfClosing)
				self.getNextChar()
			else:
				t = ShotToken(type=ShotToken.typeDirective)
			
			directive = []
			
			self.getNextChar()
			while self.currentChar != self.EOL:
				directive.append(self.currentChar)
				self.getNextChar()
			
			t.value = "".join(directive)

		# comment	
		elif self.currentChar == "!":
			t = ShotToken(type=ShotToken.typeComment)
			
			comment = []
			
			self.getNextChar()
			self.getNextChar()
			while self.currentChar != self.EOL:
				comment.append(self.currentChar)
				self.getNextChar()
			
			t.value = "".join(comment)

		elif self.currentChar == "=":
			t = ShotToken(type=ShotToken.typeEquals)
			self.getNextChar()
		
		elif self.currentChar == "[":
			t = ShotToken(type=ShotToken.typeArrayOpener)
			self.getNextChar()
			
		elif self.currentChar == "]":
			t = ShotToken(type=ShotToken.typeArrayCloser)
			self.getNextChar()
			
		elif self.currentChar == ",":
			t = ShotToken(type=ShotToken.typeComma)
			self.getNextChar()
	
		else:
			t = ShotToken(type=ShotToken.typeUnknown,value=self.currentChar)
			self.getNextChar()

		return t

	def getNextToken(self):
		self.currentToken = self.getToken()
		
	def tokenizeLine(self):
		self.currentPosInLine = 0

		# find opening whitespace
		self.getNextChar()
		while self.currentChar == " " or self.currentChar == "\t":
			self.getNextChar()
		
		# TODO : should tabs and spaces count the same?
		# should you be able to set the space width of a tab, and it would count that much?
		
		line = ShotLine(depth=self.currentPosInLine-1)

		self.getNextToken()
		while self.currentToken.type != ShotToken.typeEOL:
			line.tokens.append(self.currentToken)
			self.getNextToken()
		
		return line
		
	def tokenize(self):
		for line in open(self.fileName,"r"):
			self.currentLineNum += 1
			if not re.match(r"^\s*$",line):
				self.currentLine = line
				self.currentLineLen = len(line)
				self.lines.append(self.tokenizeLine())
