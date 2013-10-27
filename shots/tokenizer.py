#-------------------------
# Tokenizer
#-------------------------

import re

class Token:
	def __init__(self,value="",type="unknown"):
		self.value = value
		self.type = type

class Tokenizer:
	def __init__(self, fileName, log=False):

		self.logging = log

		self.currentChar = " "
		
		self.currentToken = None
		
		self.currentPosInLine = 0

		self.currentLine = ""
		self.currentLineNum = 0
		self.currentLineLen = 0

		self.lines = []		
		
		self.script = open(fileName,"r")
	
	def log(self,message):
		if self.logging:
			print message
		
	def getChar(self):
		if self.currentPosInLine >= self.currentLineLen:
			return "EOL"
		c = self.currentLine[self.currentPosInLine]
		self.currentPosInLine += 1
		return c
	
	def getNextChar(self):
		self.currentChar = self.getChar()

	def getToken(self):
		if self.currentChar == "EOL" or self.currentChar == "\n" or self.currentChar == "\r":
			return Token(type="EOL")
	
		# gobble whitespace
		while self.currentChar == " " or self.currentChar == "\t":
			self.getNextChar()
	
		# alpha
		if self.currentChar.isalpha() or self.currentChar == "_":
			t = Token(type="alpha")
		
			identifier = [self.currentChar]

			self.getNextChar()
			while self.currentChar.isalnum() or self.currentChar == "_" or self.currentChar == "-":
				identifier.append(self.currentChar)
				self.getNextChar()

			t.value = "".join(identifier)
	
		# number
		elif self.currentChar.isdigit():
			t = Token(type="number")
		
			number = []
			while self.currentChar.isdigit():
				number.append(self.currentChar)
				self.getNextChar()
		
			t.value = "".join(number)

		# quote
		elif self.currentChar == "'" or self.currentChar == "\"":
			t = Token(type="quote")
		
			quoteChar = self.currentChar
			quote = []
			
			self.getNextChar()
			while self.currentChar != quoteChar:
				quote.append(self.currentChar)
				self.getNextChar()
				if self.currentChar == quoteChar:
					if quote[-1] == "\\":
						quote.append(self.currentChar)
						self.getNextChar()

			self.getNextChar()

			t.value = "".join(quote)

		# text
		elif self.currentChar == ":":
			self.getNextChar()
			if self.currentChar == ":":
				self.getNextChar()
				t = Token(type="childElemNext")
			else:
				t = Token(type="text")
			
				text = []
			
				if self.currentChar == "EOL":
					t.value = ""
				else:
					self.getNextChar()
					while self.currentChar != "EOL":
						text.append(self.currentChar)
						self.getNextChar()
			
					t.value = "".join(text)
		
		# class
		elif self.currentChar == ".":
			t = Token(type="class")
		
			className = []
			
			self.getNextChar()
			while self.currentChar.isalnum() or self.currentChar == "_" or self.currentChar == "-":
				className.append(self.currentChar)
				self.getNextChar()

			t.value = "".join(className)
	
		# id
		elif self.currentChar == "#":
			t = Token(type="id")
			
			id = []
			
			self.getNextChar()
			while self.currentChar.isalnum() or self.currentChar == "_" or self.currentChar == "-":
				id.append(self.currentChar)
				self.getNextChar()

			t.value = "".join(id)
	
		# pointer
		elif self.currentChar == "-":
			t = Token(type="pointer")
			self.getNextChar()
			if self.currentChar == ">":
				self.getNextChar()
	
		# template directive
		elif self.currentChar == "@":
			t = Token(type="directive")
			
			directive = []
			
			self.getNextChar()
			self.getNextChar()			
			while self.currentChar != "EOL":
				directive.append(self.currentChar)
				self.getNextChar()
			
			t.value = "".join(directive)

		# comment	
		elif self.currentChar == "!":
			t = Token(type="comment")
			
			comment = []
			
			self.getNextChar()
			self.getNextChar()
			while self.currentChar != "EOL":
				comment.append(self.currentChar)
				self.getNextChar()
			
			t.value = "".join(comment)

		elif self.currentChar == "=":
			t = Token(type="equals",value=self.currentChar)
			self.getNextChar()
	
		else:
			t = Token(type="uknown",value=self.currentChar)
			self.getNextChar()

		self.log(t.type + " : " + t.value)

		return t

	def getNextToken(self):
		self.currentToken = self.getToken()
		
	def tokenizeLine(self):
		self.currentPosInLine = 0
		
		tokens = []

		# find opening whitespace
		self.getNextChar()
		while self.currentChar == " " or self.currentChar == "\t":
			self.getNextChar()
		
		# TODO : should tabs and spaces count the same?
		# should you be able to set the space width of a tab, and it would count that much?
		
		tokens.append(self.currentPosInLine)

		self.getNextToken()
		while self.currentToken.type != "EOL":
			tokens.append(self.currentToken)
			self.getNextToken()
		
		return tokens
		
	def tokenize(self):
		for line in self.script:
			self.currentLineNum += 1
			if not re.match(r"^\s*$",line):
				self.currentLine = line
				self.currentLineLen = len(line)
				self.lines.append(self.tokenizeLine())
