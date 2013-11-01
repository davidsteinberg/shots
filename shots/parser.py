from file_assistant import *

from ast import *
from tokenizer import *

_self_closers = ["area", "base", "br", "col", "command", "doctype", "embed", "hr", "img", "input", "keygen", "meta", "param", "source", "track", "wbr"]
_tags_for_head = ["base", "comment", "css", "favicon", "fetch", "js", "javascript", "meta", "noscript", "script", "style", "title"]
_directive_openers = ["block", "call", "elif", "else", "extends", "filter", "for", "from", "if", "import", "include", "macro", "raw", "set"]
_img_extensions = ["bmp", "gif", "jpeg", "jpg", "png"]

class ShotParser:

	def __init__(self, filename, included=False, extending=False, logging=False):
		self.tokenizer = ShotTokenizer(filename)
		self.included = included
		self.extending = extending
		self.logging = logging

		self.current_line_num = 0
		self.current_token_num = 0

		self.current_token = None
		self.prev_token_type = TOKEN_TYPE_UNKNOWN

		self.root_node = ShotNode(tag="",depth=-1)
		self.current_node = self.root_node
		self.next_node = None
		
		self.looking_for_head = True
		self.body_created = False
		self.force_one_space_deeper = False

	def log(self,message):
		if self.logging:
			print message

	def log_digestion(self,eaten):
		self.log("    - eat " + eaten)

	def log_creation(self,tag):
		self.log("make " + tag)

	def log_finished_creation(self,tag):
		self.log("finished making " + tag)
			
	def parse_error(self,string):
		line = []
		for t in self.tokenizer.lines[self.current_line_num].tokens:
			line.append(t.value)
		exit("Parse Error on line " + str(self.current_line_num+1) + " : " + " ".join(line) + "\n" + string)

	def reached_EOF(self):
		return self.current_line_num >= len(self.tokenizer.lines)

	def get_depth(self):
		depth = self.tokenizer.lines[self.current_line_num].depth
		if self.force_one_space_deeper:
			depth += 1
		return depth

	def get_token(self):
		if self.current_token_num >= len(self.tokenizer.lines[self.current_line_num].tokens):
			self.log_digestion("EOL")
			return ShotToken(type=TOKEN_TYPE_EOL)
		self.current_token_num += 1

		token = self.tokenizer.lines[self.current_line_num].tokens[self.current_token_num-1]
		self.log_digestion(TOKEN_TYPE_NUM_TO_NAME[token.type])

		return token

	def get_next_token(self):
		self.current_token = self.get_token()

	def include_file(self,type=""):
		self.get_next_token()
		
		filename = self.current_token.value
		quote_char = filename[0]
		filename = filename.replace(quote_char,"")
		
		file_ext = filename.split(".")[-1]
		if file_ext != type:
			filename += "." + type

		if filename[0] != "/" and filename[0] != "." and (len(filename) < 4 or filename[:4] != "http"):
			filename = get_static_path(filename)
		
		filename = quote_char + filename + quote_char
	
		if type == "css":
			node = ShotNode(tag="link",depth=self.get_depth(),parent=self.current_node,self_closing=True)

			href = ShotAttribute(name="href")
			href.value = filename
			node.attributes.append(href)

			rel = ShotAttribute(name="rel")
			rel.value = "\"stylesheet\""
			node.attributes.append(rel)

			return node
		elif type == "js":
			node = ShotNode(tag="script",depth=self.get_depth(),parent=self.current_node,multiline=False)
		
			src = ShotAttribute(name="src")
			src.value = filename
			node.attributes.append(src)
		
			return node

	def get_favicon_element(self):
		node = ShotNode(tag="link",depth=self.get_depth(),parent=self.current_node,self_closing=True)

		rel = ShotAttribute(name="rel")
		rel.value = "\"shortcut icon\""
		node.attributes.append(rel)
		
		self.get_next_token()
		
		if self.current_token.type == TOKEN_TYPE_ALPHA and self.current_token.value == "raw":
			self.get_next_token()
			url = self.current_token.value[1:-1]
		elif self.current_token.type == TOKEN_TYPE_QUOTE:
			url = get_static_path(self.current_token.value[1:-1])
		else:
			self.parse_error("expected raw or file path for favicon")
		
		href = ShotAttribute(name="href")
		href.value = "\"" + url + "\""
		node.attributes.append(href)
		
		file_ext = url.split(".")[-1]

		type = ShotAttribute(name="type")
		type.value = "\"image/"

		if file_ext == "ico":
			type.value += "x-icon"
		else:
			type.value = file_ext
		
		type.value += "\""

		node.attributes.append(type)

		return node

	def get_raw_script_or_style(self):
		
		body = []
		
		forcing = self.force_one_space_deeper
		self.force_one_space_deeper = False
		depth = self.get_depth()
		self.force_one_space_deeper = forcing

		self.current_line_num += 1
		if self.current_line_num < len(self.tokenizer.lines):
			line = self.tokenizer.lines[self.current_line_num]
	
			while line.depth > depth:
				for i in range(line.depth):
					body.append("    ")
				if forcing:
					body.append("    ")
				for token in line.tokens:
					if token.type == TOKEN_TYPE_TEXT:
						token.value = ":" + token.value
					elif token.type == TOKEN_TYPE_CLASS:
						token.value = "." + token.value
					elif token.type == TOKEN_TYPE_ID:
						token.value = "#" + token.value
					body.append(token.value + " ")
				body.append("\n")
		
				self.current_line_num += 1
				if self.current_line_num >= len(self.tokenizer.lines):
					break
				line = self.tokenizer.lines[self.current_line_num]
		
			self.current_line_num -= 1
		
		if len(body) > 0:
			del body[-1] # get rid of last newline, was causing problems

		return ''.join(body)

	def get_style_element(self):
		self.get_next_token()
		
		# raw css body
		if self.current_token.type == TOKEN_TYPE_EOL:
			node = ShotNode(tag="style",depth=self.get_depth(),parent=self.current_node)
			node.children.append(ShotTextNode(text=self.get_raw_script_or_style()))

		# single line body
		elif self.current_token.type == TOKEN_TYPE_TEXT:
			node = ShotNode(tag="style",depth=self.get_depth(),parent=self.current_node,multiline=False)
			node.children.append(ShotTextNode(text=self.current_token.value))

		# link to file
		elif self.current_token.type == TOKEN_TYPE_QUOTE:
			self.current_token_num -= 1
			return self.include_file(type="css")

		# scoped and media
		elif self.current_token.type == TOKEN_TYPE_ALPHA:
			node = ShotNode(tag="style",depth=self.get_depth(),parent=self.current_node)

			if self.current_token.value == "scoped":
				scoped = ShotAttribute(name="scoped")
				node.attributes.append(scoped)
		
			elif self.current_token.value == "media":
				attr = ShotAttribute(name="media")
				self.get_next_token()
				self.get_next_token()
				attr.value = self.current_token.value
				
				node.attributes.append(attr)
				
			else:
				self.parse_error("expected media or scoped in css attributes")

			self.get_next_token()
			
			if self.current_token.type == TOKEN_TYPE_EOL:
				node.children.append(ShotTextNode(text=self.get_raw_script_or_style()))
				
			else:
				node.multiline=False
				node.children.append(ShotTextNode(text=self.current_token.value))
			
		return node
		
	def get_script_element(self):
		self.get_next_token()
		
		# raw js body
		if self.current_token.type == TOKEN_TYPE_EOL:
			node = ShotNode(tag="script",depth=self.get_depth(),parent=self.current_node)
			node.children.append(ShotTextNode(text=self.get_raw_script_or_style()))

		# single line body
		elif self.current_token.type == TOKEN_TYPE_TEXT:
			node = ShotNode(tag="script",depth=self.get_depth(),parent=self.current_node,multiline=False)
			node.children.append(ShotTextNode(text=self.current_token.value))

		# link to file
		elif self.current_token.type == TOKEN_TYPE_QUOTE:
			self.current_token_num -= 1
			return self.include_file(type="js")

		# async and defer
		elif self.current_token.type == TOKEN_TYPE_ALPHA:
			node = ShotNode(tag="script",depth=self.get_depth(),parent=self.current_node,multiline=False)

			if self.current_token.value == "async" or self.current_token.value == "defer":
				scoped = ShotAttribute(name=self.current_token.value)
				node.attributes.append(scoped)

				self.get_next_token()

				attr = ShotAttribute(name="src")
				attr.value = self.current_token.value
				node.attributes.append(attr)

			else:
				self.parse_error("expected async or defer in js attributes")
			
		return node

	def get_break_element(self):
		self.get_next_token()
	
		if self.current_token.type == TOKEN_TYPE_NUMBER:
			node = ShotNode(tag="",depth=self.get_depth(),parent=self.current_node)
			for i in range(int(self.current_token.value)):
				node.children.append(ShotNode(tag="br",parent=self.current_node,self_closing=True))

		else:
			node = ShotNode(tag="br",depth=self.get_depth(),parent=self.current_node)
			node.self_closing = True
			
		return node

	def get_text(self):
		node = ShotTextNode(self.current_token.value,depth=self.get_depth())
		self.current_node.children.append(node)

	def get_directive(self):
		self.log_creation("directive")
	
		node = ShotNode(tag="directive",depth=self.get_depth(),parent=self.current_node)
		
		text = []

		while self.current_token.type != TOKEN_TYPE_EOL:
			if self.current_token.type == TOKEN_TYPE_TEXT:
				text.append(":" + self.current_token.value)
			elif self.current_token.type == TOKEN_TYPE_CLASS:
				text.append("." + self.current_token.value)
			elif self.current_token.type == TOKEN_TYPE_ID:
				text.append("#" + self.current_token.value)
			elif self.current_token.type == TOKEN_TYPE_EQUALS:
				text.append("=")
			elif self.current_token.type == TOKEN_TYPE_ARRAY_OPENER:
				text.append("[")
			elif self.current_token.type == TOKEN_TYPE_ARRAY_CLOSER:
				text.append("]")
			elif self.current_token.type == TOKEN_TYPE_COMMA:
				text.append(",")
			else:
				text.append(self.current_token.value)
			self.get_next_token()

		
		keyword = text[0]
		
		if keyword == "extends" or keyword == "include" or keyword == "import":

			if text[1][0] == "\"" or text[1][0] == "'":
				filename = text[1][1:-1]
				filename = get_template_path(shotify(filename))

				parser = ShotParser(filename, included=(True if keyword == "include" else False), logging=self.logging)
				
				filename = htmlify(filename)
		
				code = parser.generate_code()
				write_shot_to_file(filename,shot=code)
			
				text[1] = "\"" + filename + "\""
			
			if keyword == "extends":
				self.extending = True

				self.looking_for_head = False
				self.body_created = True

				self.current_node = self.root_node
				del self.current_node.children[:]
				node.parent = self.current_node

		attr = ShotAttribute(name=keyword,value=' '.join(text))
		node.attributes.append(attr)

		self.current_node.children.append(node)
		self.current_node = node
	
		self.log_finished_creation("directive")
		
	def get_comment(self):
		node = ShotTextNode(text="<!-- " + self.current_token.value  +" -->", depth=self.get_depth())
		self.current_node.children.append(node)

	def get_block_comment(self,secret=False):
		comment_body = []
		
		self.get_next_token()
		while self.current_token.type != TOKEN_TYPE_EOL:
			commentBody.append(self.current_token.value)
			self.get_next_token()
		
		comment_depth = self.get_depth()
		
		self.current_line_num += 1
		if self.current_line_num < len(self.tokenizer.lines):
			line = self.tokenizer.lines[self.current_line_num]
		
			while line.depth > comment_depth:
				for i in range(line.depth):
					comment_body.append("    ")
				for token in line.tokens:
					comment_body.append(token.value + " ")
				comment_body.append("\n")
			
				self.current_line_num += 1
				if self.current_line_num >= len(self.tokenizer.lines):
					break
				line = self.tokenizer.lines[self.current_line_num]
			
			self.current_line_num -= 1

		text = "" if secret else "<!--\n" + "".join(comment_body) + "-->"
		return ShotTextNode(text=text,depth=comment_depth)

	def get_node_with_tag(self):
		self.log_creation(self.current_token.value)
		
		# comment check
		if self.current_token.value == "comment":
			node = self.get_block_comment()
			
		elif self.current_token.value == "disable" or self.current_token.value == "secret":
			node = self.get_block_comment(secret=True)

		else:
#
#			OPTIONAL HEAD AND BODY TAGS
#
			if self.included:
				self.looking_for_head = False
				self.body_created = True

			elif self.body_created:
				self.looking_for_head = False
		
			elif self.looking_for_head:
				if self.current_token.value == "head":
					self.looking_for_head = False
				elif self.current_token.value != "doctype" and self.current_token.value != "html":
					head_element = ShotNode(tag="head",depth=0,parent=self.current_node)
					self.current_node.children.append(head_element)
					self.current_node = head_element
			
					self.looking_for_head = False
					self.force_one_space_deeper = True
				
					if self.current_token.value not in _tags_for_head:
						self.current_node = self.current_node.parent
						if self.current_token.value != "body":
							body_element = ShotNode(tag="body",depth=0,parent=self.current_node)
							self.current_node.children.append(body_element)
							self.current_node = body_element
						
						self.body_created = True
			elif not self.body_created:
				if self.current_token.value not in _tags_for_head:
					self.current_node = self.current_node.parent if self.current_node.parent else self.root_node
					if self.current_token.value == "body":
						self.force_one_space_deeper = False
					else:
						body_element = ShotNode(tag="body",depth=0,parent=self.current_node)
						self.force_one_space_deeper = True
						self.current_node.children.append(body_element)
						self.current_node = body_element
					
					self.body_created = True				
					
			# template directive check
			if self.current_token.value in _directive_openers:
				self.get_directive()
				return
	
			elif self.current_token.value == "favicon":
				node = self.get_favicon_element()

			elif self.current_token.value == "br":
				node = self.get_break_element()

			elif self.current_token.value == "style" or self.current_token.value == "css":
				node = self.get_style_element()

			elif self.current_token.value == "script" or self.current_token.value == "js" or self.current_token.value == "javascript":
				node = self.get_script_element()

			else:
				if self.current_token.value == "link":
					self.current_token.value = "shots-link"
			
				node = ShotNode(tag=self.current_token.value,depth=self.get_depth(),parent=self.current_node)
				if node.tag in _self_closers:
					node.self_closing = True
				
				self.current_node.children.append(node)
				self.current_node = node
				node = None
				
				block_text = False
				child_elem_next = False
				
				self.get_next_token()
				while self.current_token.type != TOKEN_TYPE_EOL:
				
					if self.current_token.type == TOKEN_TYPE_ALPHA:
						attr = ShotAttribute(name=self.current_token.value)
						self.get_next_token()
						
						if self.current_token.type != TOKEN_TYPE_EQUALS:
							self.current_node.attributes.append(attr)
							self.current_token_num -= 1

						else:
							self.get_next_token()
							
							if "[[" in self.current_token.value or "{{" in self.current_token.value:
								attr.value = self.current_token.value
								self.current_node.attributes.append(attr)
							
							elif attr.name == "src":
								if self.current_node.tag == "img":
									filename = self.current_token.value[1:-1]

									if filename[0] == "/" or filename[0] == "." or (len(filename) > 4 and filename[:4] == "http"):
										attr.value = self.current_token.value
										self.current_node.attributes.append(attr)

									file_ext = filename.split(".")[-1]

									if file_ext not in _img_extensions:
										for ext in _img_extensions:
											path = get_static_path(filename + "." + ext)
											if path != filename + "." + ext:
												attr.value = "\"" + path + "\""
												self.current_node.attributes.append(attr)
												break
									else:
										attr.value = self.current_token.value
										self.current_node.attributes.append(attr)
								
								elif self.current_node.tag == "audio" or self.current_node.tag == "video":
									sources = []
							
									if self.current_token.type == TOKEN_TYPE_ARRAY_OPENER:
										self.get_next_token()

										while self.current_token.type != TOKEN_TYPE_ARRAY_CLOSER:
											if self.current_token.type == TOKEN_TYPE_QUOTE:
												sources.append(self.current_token.value)

											self.get_next_token()

										self.get_next_token()
									
									elif self.current_token.type == TOKEN_TYPE_QUOTE:
										sources.append(self.current_token.value)

									else:
										self.parse_error("expected quote or array after audio or video src")
								
									for s in sources:
										sourced = False
									
										filename = s[1:-1]
										
										if filename[0] != "/" and filename[0] != "." and (len(filename) < 4 or filename[:4] != "http"):
											file_ext = filename.split(".")[-1]

											if file_ext == "mp3":
												file_ext = "mpeg"

											elif file_ext != "wav" and file_ext != "ogg":
												exts = None

												if self.current_node.tag == "audio":
													exts = ["mp3","wav","ogg"]
												else:
													exts = ["mp4","webm","ogg"]

												for ext in exts:
													path = get_static_path(filename + "." + ext)
													if path != filename + "." + ext:
														source = ShotNode(tag="source",depth=self.get_depth()+1,parent=self.current_node,self_closing=True)
														src = ShotAttribute(name="src",value="\"" + path + "\"")
														source.attributes.append(src)
									
														type = ShotAttribute(name="type")
														type.value = "\""+("audio" if self.current_node.tag == "audio" else "video") + "/" + (ext if ext != "mp3" else"mpeg") + "\""
														source.attributes.append(type)
									
														self.current_node.children.append(source)
										
												sourced = True

										if not sourced:
											source = ShotNode(tag="source",depth=self.get_depth()+1,parent=self.current_node,self_closing=True)
											src = ShotAttribute(name="src",value="\"" + get_static_path(filename) + "\"")
											source.attributes.append(src)
									
											type = ShotAttribute(name="type")
											type.value = "\""+("audio" if self.current_node.tag == "audio" else "video") + "/" + file_ext + "\""
											source.attributes.append(type)
									
											self.current_node.children.append(source)
								
								else:
									attr.value = self.current_token.value
									self.current_node.attributes.append(attr)
								
							elif self.current_token.type == TOKEN_TYPE_QUOTE:
								attr.value = self.current_token.value
								self.current_node.attributes.append(attr)

							else:
								self.parse_error("expected quote after attribute")
					
					elif self.current_token.type == TOKEN_TYPE_CLASS:
						self.current_node.classes.append(self.current_token.value)
					
					elif self.current_token.type == TOKEN_TYPE_ID:
						self.current_node.id = self.current_token.value
					
					elif self.current_token.type == TOKEN_TYPE_TEXT:
						if self.current_token.value == "":
							block_text = True
						else:
							if self.current_node.tag == "audio" or self.current_node.tag == "video":
								self.current_node.children.append(ShotTextNode(text=self.current_token.value,depth=self.get_depth()+1))
							else:
								self.current_node.children.append(ShotTextNode(text=self.current_token.value))
								self.current_node.multiline = False
						break
						
					elif self.current_token.type == TOKEN_TYPE_CHILD_ELEM_NEXT:
						child_elem_next = True
						break
				
					self.get_next_token()
				
				if block_text:
					elem_body = []
					
					forcing = self.force_one_space_deeper
					self.force_one_space_deeper = False
					elemDepth = self.get_depth()
					self.force_one_space_deeper = forcing
		
					self.current_line_num += 1
					if self.current_line_num < len(self.tokenizer.lines):
						line = self.tokenizer.lines[self.current_line_num]
		
						while line.depth > elemDepth:
							for i in range(line.depth):
								elem_body.append("    ")
							if forcing:
								elem_body.append("    ")
							for token in line.tokens:
								elem_body.append(token.value + " ")
							elem_body.append("\n")
			
							self.current_line_num += 1
							if self.current_line_num >= len(self.tokenizer.lines):
								break
							line = self.tokenizer.lines[self.current_line_num]
			
						self.current_line_num -= 1
			
					if len(elem_body) > 0:					
						del elem_body[-1] # get rid of last newline
					
					self.current_node.children.append(''.join(elem_body))
				
				elif child_elem_next:
					self.current_node.multiline = False
					self.current_node.depth -= 1

					self.get_next_node()

					self.current_line_num -= 1
					self.current_node = self.current_node.parent
					self.current_node.depth += 1
		
		if node:
			self.current_node.children.append(node)

	def get_node(self):
		if self.reached_EOF():
			return None

		while self.get_depth() <= self.current_node.depth:
			self.log_finished_creation(self.current_node.tag)
			if self.current_node.tag == "body" or self.current_node.tag == "head":
				self.force_one_space_deeper = False
			self.current_node = self.current_node.parent

		self.get_next_token()

		if self.current_token.type == TOKEN_TYPE_ALPHA:
			self.get_node_with_tag()

		elif self.current_token.type == TOKEN_TYPE_CLASS:
			self.current_token = ShotToken(value="div")
			self.current_token_num = 0
			self.get_node_with_tag()

		elif self.current_token.type == TOKEN_TYPE_ID:
			self.current_token = ShotToken(value="div")
			self.current_token_num = 0
			self.get_node_with_tag()

		elif self.current_token.type == TOKEN_TYPE_HTML_COMMENT:
			self.log_creation("line comment")
			self.get_comment()
			self.log_finished_creation("line comment")

		elif self.current_token.type == TOKEN_TYPE_SHOT_COMMENT:
			return True

		else:
#
#			OPTIONAL HEAD AND BODY TAGS
#
			if not self.included and not self.body_created:
				if self.looking_for_head:
					head = ShotNode(tag="head",depth=0,parent=self.current_node)
					self.current_node.children.append(head)
					
					self.looking_for_head = False
				elif self.current_node.tag == "head":
					self.current_node = self.current_node.parent
				
				body = ShotNode(tag="body",depth=0,parent=self.current_node)
				self.current_node.children.append(body)

				self.force_one_space_deeper = True

				self.current_node = body
				self.body_created = True

			if self.current_token.type == TOKEN_TYPE_TEXT:
				self.log_creation("text")
				self.get_text()
				self.log_finished_creation("text")
		
		return True

	def get_next_node(self):
		self.next_node = self.get_node()
		self.current_line_num += 1
		self.current_token_num = 0

	def tokenize(self):
		self.tokenizer.tokenize()

	def parse(self):
		self.get_next_node()
		while self.next_node:
			self.get_next_node()

	def generate_code(self):
		self.tokenize()
		self.parse()
	
		result = ""
		kids = self.root_node.children
		if len(kids) > 0:
			if self.extending or self.included:
				for k in kids:
					result += str(k)
			else:
				if not isinstance(kids[0],ShotTextNode) and kids[0].tag == "doctype":
					kids[0].tag = "!doctype"
					for k in kids:
						result += str(k)
				else:
					result = "<!doctype html>\n"
					if not isinstance(kids[0],ShotTextNode) and kids[0].tag == "html":
						for k in kids:
							result += str(k)
					else:
						node = ShotNode(tag="html",multiline=True)
						for k in kids:
							node.children.append(k)
						result += str(node)

		# last minute regex for template delimiters and == in directives
		result = re.sub(r"\[\[",r"{{",result)
		result = re.sub(r"\]\]",r"}}",result)
# 		result = re.sub(r"\|([^|]+)\|",r"{{ \1 }}",result)
# 		result = re.sub(r"{ ",r"{{ ",result)
# 		result = re.sub(r" }",r" }}",result)
		result = re.sub(r"= =",r"==",result)
		return result
