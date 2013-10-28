#-------------------------
# Tokenizer
#-------------------------

import re

class ShotsToken:

	typeAlpha = 0
	typeClass = 1
	typeChildElemNext = 2
	typeComment = 3
	typeDirective = 4
	typeDirectiveWithClosing = 5
	typeEquals = 6
	typeEOL = 7
	typeID = 8
	typeNumber = 9
	typePointer = 10
	typeQuote = 11
	typeText = 12
	typeUnknown = 13

	def __init__(self,value="",type="unknown"):
		self.value = value
		self.type = type
	
	def __str__(self):
		return self.value

class ShotsLine:
	def __init__(self,depth=0):
		self.depth = depth
		self.tokens = []

class ShotsTokenizer:
	def __init__(self, fileName, logging=False):

		self.fileName = fileName
		self.logging = logging

		self.currentChar = " "		
		self.currentToken = None
		self.currentPosInLine = 0

		self.EOL = "$"

		self.currentLine = ""
		self.currentLineNum = 0
		self.currentLineLen = 0

		self.lines = []
	
	def log(self,message):
		if self.logging:
			print message
		
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
			return ShotsToken(type=ShotsToken.typeEOL)
	
		# gobble whitespace
		while self.currentChar == " " or self.currentChar == "\t":
			self.getNextChar()
	
		# alpha
		if self.currentChar.isalpha() or self.currentChar == "_" or self.currentChar == "|":
			t = ShotsToken(type=ShotsToken.typeAlpha)
		
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
			t = ShotsToken(type=ShotsToken.typeNumber)
		
			number = []
			while self.currentChar.isdigit():
				number.append(self.currentChar)
				self.getNextChar()
		
			t.value = "".join(number)

		# quote
		elif self.currentChar == "'" or self.currentChar == "\"":
			t = ShotsToken(type=ShotsToken.typeQuote)
		
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
				t = ShotsToken(type=ShotsToken.typeChildElemNext)
			else:
				t = ShotsToken(type=ShotsToken.typeText)
			
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
			t = ShotsToken(type=ShotsToken.typeClass)
		
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
			t = ShotsToken(type=ShotsToken.typeID)
			
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
				t = ShotsToken(type=ShotsToken.typeDirectiveWithClosing)
				self.getNextChar()
			else:
				t = ShotsToken(type=ShotsToken.typeDirective)
			
			directive = []
			
			self.getNextChar()
			while self.currentChar != self.EOL:
				directive.append(self.currentChar)
				self.getNextChar()
			
			t.value = "".join(directive)

		# comment	
		elif self.currentChar == "!":
			t = ShotsToken(type=ShotsToken.typeComment)
			
			comment = []
			
			self.getNextChar()
			self.getNextChar()
			while self.currentChar != self.EOL:
				comment.append(self.currentChar)
				self.getNextChar()
			
			t.value = "".join(comment)

		elif self.currentChar == "=":
			t = ShotsToken(type=ShotsToken.typeEquals,value=self.currentChar)
			self.getNextChar()
	
		else:
			t = ShotsToken(type=ShotsToken.typeUnknown,value=self.currentChar)
			self.getNextChar()

		self.log(str(t.type) + " : " + t.value)

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
		
		line = ShotsLine(depth=self.currentPosInLine-1)

		self.getNextToken()
		while self.currentToken.type != ShotsToken.typeEOL:
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
