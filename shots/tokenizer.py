import re

TOKEN_TYPE_ALPHA = 0
TOKEN_TYPE_ARRAY_CLOSER = 1
TOKEN_TYPE_ARRAY_OPENER = 2
TOKEN_TYPE_CHILD_ELEM_NEXT = 3
TOKEN_TYPE_CLASS = 4
TOKEN_TYPE_COMMA = 5
TOKEN_TYPE_DIRECTIVE = 6
TOKEN_TYPE_EOL = 7
TOKEN_TYPE_EQUALS = 8
TOKEN_TYPE_HTML_LINE_COMMENT = 9
TOKEN_TYPE_ID = 10
TOKEN_TYPE_NUMBER = 11
TOKEN_TYPE_QUOTE = 12
TOKEN_TYPE_SHOT_LINE_COMMENT = 13
TOKEN_TYPE_TEXT = 14
TOKEN_TYPE_UNKNOWN = 15

TOKEN_TYPE_NUM_TO_NAME = [
	"alpha",
	"array closer",
	"array opener",
	"child elem next",
	"class",
	"comma",
	"directive",
	"EOL",
	"equals",
	"html comment",
	"id",
	"number",
	"quote",
	"shot comment",
	"text",
	"unknown"
]

_directive_openers = ["block", "call", "elif", "else", "extends", "filter", "for", "from", "if", "import", "include", "macro", "raw", "set"]

class ShotToken:
	def __init__(self,value="",type=TOKEN_TYPE_UNKNOWN):
		self.value = value
		self.type = type
	
	def __str__(self):
		return self.value

class ShotLine:
	def __init__(self,depth=0):
		self.depth = depth
		self.tokens = []

class ShotTokenizer:
	def __init__(self, filename):

		self.filename = filename

		self.current_char = " "		
		self.current_token = None
		self.current_pos_in_line = 0

		self.EOL = "-1"

		self.current_line = ""
		self.current_line_num = 0
		self.current_line_len = 0

		self.lines = []
		
	def get_char(self):
		if self.current_pos_in_line >= self.current_line_len:
			return self.EOL
		c = self.current_line[self.current_pos_in_line]
		if c == "\n" or c == "\r":
			return self.EOL
		self.current_pos_in_line += 1
		return c
	
	def get_next_char(self):
		self.current_char = self.get_char()
		
	def peek_next_char(self):
		if self.current_pos_in_line >= self.current_line_len:
			return self.EOL
		c = self.current_line[self.current_pos_in_line]
		if c == "\n" or c == "\r":
			return self.EOL
		return c

	def get_token(self):
		if self.current_char == self.EOL:
			return ShotToken(type=TOKEN_TYPE_EOL)
	
		# gobble whitespace
		while self.current_char == " " or self.current_char == "\t":
			self.get_next_char()
	
		# alpha
		if self.current_char.isalpha() or self.current_char == "_" or ((self.current_char == "{" or self.current_char == "[") and self.peek_next_char() == self.current_char):
			
			t = ShotToken(type=TOKEN_TYPE_ALPHA)
		
			identifier = [self.current_char]

			templating = False
			
			if self.current_char == "{" or self.current_char == "[":
				templating = True
				self.get_next_char()
				identifier.append(self.current_char)
				
			self.get_next_char()
			while self.current_char.isalnum() or self.current_char == "_" or self.current_char == "-" or templating or ((self.current_char == "}" or self.current_char == "]") and self.peek_next_char() == self.current_char) or ((self.current_char == "{" or self.current_char == "[") and self.peek_next_char() == self.current_char):
				identifier.append(self.current_char)
				if self.current_char == "}" or self.current_char == "]" or self.current_char == "{" or self.current_char == "[":
					templating = not templating
					self.get_next_char()
					identifier.append(self.current_char)
				self.get_next_char()

			t.value = "".join(identifier)
			
			if t.value in _directive_openers:
				directive = [t.value]
				
				while self.current_char != self.EOL:
					directive.append(self.current_char)
					self.get_next_char()
				
				t.type = TOKEN_TYPE_DIRECTIVE
				t.value = "".join(directive)
				
			elif t.value == "comment" or t.value == "secret":
				# eat til end of line and block
				# should store each line with its depth and then the whole line as its sole token
				pass
				
			elif t.value == "css" or t.value == "js":
				# eat til end of block
				# should store each line with its depth and then the whole line as its sole token
				pass
		
		# number
		elif self.current_char.isdigit():
			t = ShotToken(type=TOKEN_TYPE_NUMBER)
		
			number = []
			while self.current_char.isdigit():
				number.append(self.current_char)
				self.get_next_char()
		
			t.value = "".join(number)

		# quote
		elif self.current_char == "'" or self.current_char == "\"":
			t = ShotToken(type=TOKEN_TYPE_QUOTE)
		
			quote_char = self.current_char
			quote = [quote_char]
			
			self.get_next_char()
			while self.current_char != quote_char:
				quote.append(self.current_char)
				self.get_next_char()
				if self.current_char == quote_char:
					if quote[-1] == "\\":
						quote.append(self.current_char)
						self.get_next_char()

			self.get_next_char()

			quote.append(quote_char)
			t.value = "".join(quote)

		# text
		elif self.current_char == ":":
			self.get_next_char()
			if self.current_char == ":":
				self.get_next_char()
				t = ShotToken(type=TOKEN_TYPE_CHILD_ELEM_NEXT)
			else:
				t = ShotToken(type=TOKEN_TYPE_TEXT)
			
				text = []
			
				if self.current_char == self.EOL:
					t.value = ""
				else:
					self.get_next_char()
					while self.current_char != self.EOL:
						text.append(self.current_char)
						self.get_next_char()
			
					t.value = "".join(text)
		
		# class
		elif self.current_char == ".":
			t = ShotToken(type=TOKEN_TYPE_CLASS)
		
			class_name = []
			
			templating = False

			self.get_next_char()
			while self.current_char.isalnum() or self.current_char == "_" or self.current_char == "-" or templating or ((self.current_char == "{" or self.current_char == "[") and self.peek_next_char() == self.current_char):
				class_name.append(self.current_char)
				if self.current_char == "}" or self.current_char == "]" or self.current_char == "{" or self.current_char == "[":
					templating = not templating
					self.get_next_char()
					class_name.append(self.current_char)

				self.get_next_char()

			t.value = "".join(class_name)
	
		# id
		elif self.current_char == "#":
			t = ShotToken(type=TOKEN_TYPE_ID)
			
			id = []

			templating = False

			self.get_next_char()
			while self.current_char.isalnum() or self.current_char == "_" or self.current_char == "-" or templating or ((self.current_char == "{" or self.current_char == "[") and self.peek_next_char() == self.current_char):
				id.append(self.current_char)
				if self.current_char == "}" or self.current_char == "]" or self.current_char == "{" or self.current_char == "[":
					templating = not templating
					self.get_next_char()
					id.append(self.current_char)
				self.get_next_char()

			t.value = "".join(id)

		# comments
		elif self.current_char == "!":
			self.get_next_char()

			if self.current_char == "!":
				t = ShotToken(type=TOKEN_TYPE_SHOT_LINE_COMMENT)
				self.get_next_char()
			else:
				t = ShotToken(type=TOKEN_TYPE_HTML_LINE_COMMENT)
			
			comment = []

			self.get_next_char()
			while self.current_char != self.EOL:
				comment.append(self.current_char)
				self.get_next_char()
			
			t.value = "".join(comment)

		# equals (for attributes)
		elif self.current_char == "=":
			t = ShotToken(type=TOKEN_TYPE_EQUALS)
			self.get_next_char()

		# array tokens (for audio and video src)
		elif self.current_char == "[":
			t = ShotToken(type=TOKEN_TYPE_ARRAY_OPENER)
			self.get_next_char()
			
		elif self.current_char == "]":
			t = ShotToken(type=TOKEN_TYPE_ARRAY_CLOSER)
			self.get_next_char()
			
		elif self.current_char == ",":
			t = ShotToken(type=TOKEN_TYPE_COMMA)
			self.get_next_char()
		
		# unknown
		else:
			t = ShotToken(type=TOKEN_TYPE_UNKNOWN,value=self.current_char)
			self.get_next_char()

		return t

	def get_next_token(self):
		self.current_token = self.get_token()
		
	def tokenize_line(self):
		self.current_pos_in_line = 0

		# find opening whitespace
		self.get_next_char()
		while self.current_char == " " or self.current_char == "\t":
			self.get_next_char()
		
		# TODO : should tabs and spaces count the same?
		# should you be able to set the space width of a tab, and it would count that much?
		
		line = ShotLine(depth=self.current_pos_in_line-1)

		self.get_next_token()
		while self.current_token.type != TOKEN_TYPE_EOL:
			line.tokens.append(self.current_token)
			self.get_next_token()
		
		return line
		
	def tokenize(self):
		for line in open(self.filename,"r"):
			self.current_line_num += 1
			if not re.match(r"^\s*$",line):
				self.current_line = line
				self.current_line_len = len(line)
				self.lines.append(self.tokenize_line())
