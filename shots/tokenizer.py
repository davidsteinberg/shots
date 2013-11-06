import re

from settings import settings

def _enumerate(*enums):
	result = dict(zip(enums, range(len(enums))))
	result["NAMES"] = dict((num, name) for name, num in result.iteritems())
	return type("Enum", (), result)

TOKEN_TYPE = _enumerate(
	"ALPHA",
	"ARRAY_CLOSER",
	"ARRAY_OPENER",
	"CHILD_ELEM_NEXT",
	"CLASS",
	"COMMA",
	"DIRECTIVE",
	"EOL",
	"EQUALS",
	"HTML_LINE_COMMENT",
	"HTML_BLOCK_COMMENT",
	"ID",
	"NUMBER",
	"QUOTE",
	"SHOT_LINE_COMMENT",
	"SHOT_BLOCK_COMMENT",
	"SIBLING_ELEM_NEXT",
	"TEXT",
	"UNKNOWN"
)

_directive_openers = ["block", "call", "def", "elif", "else", "extends", "filter", "for", "from", "if", "import", "include", "macro", "raw", "set"]

class ShotToken:
	def __init__(self,value="",type=TOKEN_TYPE.UNKNOWN):
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
		self.file_lines = []
		
	def get_char(self):
		if self.current_pos_in_line >= self.current_line_len:
			return self.EOL
		c = self.current_line[self.current_pos_in_line]
		self.current_pos_in_line += 1
		return c
	
	def get_next_char(self):
		self.current_char = self.get_char()
		
	def peek_next_char(self):
		if self.current_pos_in_line >= self.current_line_len:
			return self.EOL
		return self.current_line[self.current_pos_in_line]

	def get_token(self, peeking=False):
		if self.current_char == self.EOL:
			return ShotToken(type=TOKEN_TYPE.EOL)
	
		# gobble whitespace
		while self.current_char == " " or self.current_char == "\t":
			self.get_next_char()
	
		# alpha
		if self.current_char.isalpha() or self.current_char == "_" or ((self.current_char == "{" or self.current_char == "[") and self.peek_next_char() == self.current_char):
			
			t = ShotToken(type=TOKEN_TYPE.ALPHA)
		
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
		
		# number
		elif self.current_char.isdigit():
			t = ShotToken(type=TOKEN_TYPE.NUMBER)
		
			number = []
			while self.current_char.isdigit():
				number.append(self.current_char)
				self.get_next_char()
		
			t.value = "".join(number)

		# quote
		elif self.current_char == "'" or self.current_char == "\"":
			t = ShotToken(type=TOKEN_TYPE.QUOTE)
		
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
				t = ShotToken(type=TOKEN_TYPE.CHILD_ELEM_NEXT)
			else:
				t = ShotToken(type=TOKEN_TYPE.TEXT)
			
				text = []
			
				if self.current_char == self.EOL:
					t.value = ""
				else:
					self.get_next_char()
					while self.current_char != self.EOL:					
						if not peeking:
							if self.current_char == "+":
								if text[-1] == "\\":
									text[-1] = "+"
								else:
									break
					
						text.append(self.current_char)
						self.get_next_char()
			
					t.value = "".join(text)
					
		# other text
		elif self.current_char == "|":
			t = ShotToken(type=TOKEN_TYPE.TEXT)
		
			text = []
		
			self.get_next_char()
		
			if self.current_char == self.EOL:
				t.value = ""
			else:
				self.get_next_char()
				while self.current_char != self.EOL:
					if not peeking:
						if self.current_char == "+":
							if text[-1] == "\\":
								text[-1] = "+"
							else:
								break

					text.append(self.current_char)					
					self.get_next_char()
		
				t.value = "".join(text)

		# child element next
		elif self.current_char == ">":
			t = ShotToken(type=TOKEN_TYPE.CHILD_ELEM_NEXT)
			self.get_next_char()
			
		# sibling element next
		elif self.current_char == "+":
			t = ShotToken(type=TOKEN_TYPE.SIBLING_ELEM_NEXT)
			self.get_next_char()

		# class
		elif self.current_char == ".":
			t = ShotToken(type=TOKEN_TYPE.CLASS)
		
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
			t = ShotToken(type=TOKEN_TYPE.ID)
			
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
				t = ShotToken(type=TOKEN_TYPE.SHOT_LINE_COMMENT)
				self.get_next_char()
			else:
				t = ShotToken(type=TOKEN_TYPE.HTML_LINE_COMMENT)
			
			comment = []

			self.get_next_char()
			while self.current_char != self.EOL:
				comment.append(self.current_char)
				self.get_next_char()
			
			t.value = "".join(comment)

		# equals (for attributes)
		elif self.current_char == "=":
			t = ShotToken(type=TOKEN_TYPE.EQUALS)
			self.get_next_char()

		# array tokens (for audio and video src)
		elif self.current_char == "[":
			t = ShotToken(type=TOKEN_TYPE.ARRAY_OPENER)
			self.get_next_char()
			
		elif self.current_char == "]":
			t = ShotToken(type=TOKEN_TYPE.ARRAY_CLOSER)
			self.get_next_char()
			
		elif self.current_char == ",":
			t = ShotToken(type=TOKEN_TYPE.COMMA)
			self.get_next_char()
		
		# unknown
		else:
			t = ShotToken(type=TOKEN_TYPE.UNKNOWN,value=self.current_char)
			self.get_next_char()

		return t

	def get_content_block(self,depth=0):
		line_depth = depth + 1

		while line_depth > depth:
			self.current_line_num += 1

			if self.current_line_num >= len(self.file_lines):
				break
		
			self.current_line = self.file_lines[self.current_line_num]

			if not re.match(r"^\s*$",self.current_line):
				self.current_line_len = len(self.current_line)

				self.current_pos_in_line = 0

				additional_depth = 0

				self.get_next_char()
				while self.current_char == " " or self.current_char == "\t":
					if self.current_char == "\t":
						additional_depth += settings.tab_width - 1					
					self.get_next_char()

				line_depth = self.current_pos_in_line - 1 + additional_depth
				if line_depth <= depth:
					self.current_line_num -= 1
					break

				line = ShotLine(depth=line_depth)
			
				line_body = []

				while self.current_char != self.EOL:
					line_body.append(self.current_char)
					self.get_next_char()
			
				t = ShotToken(type=TOKEN_TYPE.TEXT,value="".join(line_body))
				line.tokens.append(t)

				self.lines.append(line)

	def get_next_token(self):
		self.current_token = self.get_token()
		
	def peek_next_token(self):
		current_pos = self.current_pos_in_line
		next_token = self.get_token(peeking=True)
		self.current_pos_in_line = current_pos

		if next_token.type != TOKEN_TYPE.EOL:
			self.current_pos_in_line -= 1
		self.get_next_char()

		return next_token
		
	def tokenize_line(self):

		additional_depth = 0

		# find opening whitespace
		self.get_next_char()
		while self.current_char == " " or self.current_char == "\t":
			if self.current_char == "\t":
				additional_depth += settings.tab_width - 1
			self.get_next_char()
		
		depth = self.current_pos_in_line - 1 + additional_depth
		
		line = ShotLine(depth=depth)

		self.get_next_token()
		while self.current_token.type != TOKEN_TYPE.EOL:
		
			if self.current_token.type == TOKEN_TYPE.ALPHA:
				if self.current_token.value in _directive_openers and len(line.tokens) == 0:
					if self.current_token.value == "def":
						self.current_token.value = "macro"
				
					self.current_token.type = TOKEN_TYPE.DIRECTIVE
				
					line.tokens.append(self.current_token)
				
					directive = [self.current_token.value]
				
					while self.current_char != self.EOL:
						directive.append(self.current_char)
						self.get_next_char()
						
					text = "".join(directive)
					
					if directive[0] == "macro":
						text = re.sub(r"\(, ", "(", re.sub(r"\)([^)]*)$", r", caller=None)\1", text))
				
					t = ShotToken(type=TOKEN_TYPE.TEXT, value=text)
					line.tokens.append(t)

					break

				elif self.current_token.value == "comment" or self.current_token.value == "secret":

					if self.current_token.value == "comment":
						line.tokens.append(ShotToken(type=TOKEN_TYPE.HTML_BLOCK_COMMENT))

					elif self.current_token.value == "secret":
						line.tokens.append(ShotToken(type=TOKEN_TYPE.SHOT_BLOCK_COMMENT))
				
					comment_body = []

					self.get_next_char()
					while self.current_char != self.EOL:
						comment_body.append(self.current_char)
						self.get_next_char()
						
					t = ShotToken(type=TOKEN_TYPE.TEXT,value="".join(comment_body))
					line.tokens.append(t)
					
					self.lines.append(line)
					self.get_content_block(depth)
					return None
				
				elif self.current_token.value == "css" or self.current_token.value == "js":
					line.tokens.append(self.current_token)

					self.get_next_token()

					if self.current_token.type == TOKEN_TYPE.EOL:
						self.lines.append(line)
						self.get_content_block(depth)
						return None

				elif len(line.tokens) == 0:
					next_token = self.peek_next_token()
					
					if next_token.type == TOKEN_TYPE.EQUALS:
						t = ShotToken(type=TOKEN_TYPE.DIRECTIVE, value="set")
						line.tokens.append(t)
						
						directive = ["set ", self.current_token.value]
				
						while self.current_char != self.EOL:
							directive.append(self.current_char)
							self.get_next_char()
				
						t = ShotToken(type=TOKEN_TYPE.TEXT, value="".join(directive))
						line.tokens.append(t)
						
					elif next_token.value == "(":
						t = ShotToken(type=TOKEN_TYPE.DIRECTIVE, value="call")
						line.tokens.append(t)
						
						directive = ["call ", self.current_token.value]
				
						while self.current_char != self.EOL:
							directive.append(self.current_char)
							self.get_next_char()
				
						t = ShotToken(type=TOKEN_TYPE.TEXT, value="".join(directive))
						line.tokens.append(t)
					
					else:
						line.tokens.append(self.current_token)
						self.get_next_token()
					
				else:
					line.tokens.append(self.current_token)
					self.get_next_token()
				
			elif self.current_token.type == TOKEN_TYPE.TEXT:
				line.tokens.append(self.current_token)

				self.get_next_token()
				
				if self.current_token.type == TOKEN_TYPE.EOL:
					self.lines.append(line)
					self.get_content_block(depth)
					return None
				else:
					line.tokens.append(self.current_token)
					self.get_next_token()

			else:
				line.tokens.append(self.current_token)
				self.get_next_token()
		
		return line
		
	def tokenize(self):
		self.file_lines = [line.rstrip('\n') for line in open(self.filename)]

		while self.current_line_num < len(self.file_lines):
			self.current_line = self.file_lines[self.current_line_num]

			if not re.match(r"^\s*$",self.current_line):
				self.current_line_len = len(self.current_line)

				self.current_pos_in_line = 0

				next_line = self.tokenize_line()
				if next_line:
					self.lines.append(next_line)

			self.current_line_num += 1
