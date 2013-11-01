from fileHandler import getStaticPath, splitext

from ast import *
from tokenizer import *

selfClosers = ["area", "base", "br", "col", "command", "doctype", "embed", "hr", "img", "input", "keygen", "meta", "param", "source", "track", "wbr"]
tagsForHead = ["base", "comment", "css", "favicon", "fetch", "js", "javascript", "meta", "noscript", "script", "style", "title"]
directiveOpeners = ["block", "call", "elif", "else", "extends", "filter", "for", "from", "if", "import", "include", "macro", "raw", "set"]

class ShotParser:

	def __init__(self, filename, included=False, extending=False, logging=False):
		self.tokenizer = ShotTokenizer(filename)
		self.included = included
		self.extending = extending
		self.logging = logging

		self.currentLineNum = 0
		self.currentTokenNum = 0

		self.currentToken = None
		self.prevTokenType = ShotToken.typeUnknown

		self.rootNode = ShotNode(tag="",depth=-1)
		self.currentNode = self.rootNode
		self.nextNode = None
		
		self.lookingForHead = True
		self.bodyCreated = False

	def log(self,message):
		if self.logging:
			print message

	def logDigestion(self,eaten):
		self.log("    - eat " + eaten)

	def logCreation(self,tag):
		self.log("make " + tag)

	def logFinishedCreation(self,tag):
		self.log("finished making " + tag)
			
	def parseError(self,string):
		exit("Parse Error on line " + str(self.currentLineNum+1) + ", token " + str(self.currentTokenNum) + " : " + string)

	def reachedEOF(self):
		return self.currentLineNum >= len(self.tokenizer.lines)

	def getToken(self):
		if self.currentTokenNum >= len(self.tokenizer.lines[self.currentLineNum].tokens):
			self.logDigestion("EOL")
			return ShotToken(type=ShotToken.typeEOL)
		self.currentTokenNum += 1

		token = self.tokenizer.lines[self.currentLineNum].tokens[self.currentTokenNum-1]
		self.logDigestion(ShotToken.typeNumToName[token.type])

		return token

	def getNextToken(self):
		self.currentToken = self.getToken()

	def includeFile(self,fetch=False):
		self.getNextToken()
		
		fileName = self.currentToken.value
		quoteChar = fileName[0]
		fileName = fileName.replace(quoteChar,"")
		
		fileExt = fileName.split(".")[-1]
	
		fileName = quoteChar + getStaticPath(fileName) + quoteChar
	
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
			node = ShotNode(tag="script",depth=self.getDepth(),parent=self.currentNode,multiline=False)
		
			src = ShotAttribute(name="src")
			src.value = fileName
			node.attributes.append(src)
		
			return node
		else:
			self.parseError("couldn't find file extension on " + ("fetch" if fetch else "includ") + "ed file")

	def getFaviconElement(self):
		node = ShotNode(tag="link",depth=self.getDepth(),parent=self.currentNode,selfClosing=True)

		rel = ShotAttribute(name="rel")
		rel.value = "\"shortcut icon\""
		node.attributes.append(rel)
		
		self.getNextToken()
		
		if self.currentToken.type == ShotToken.typeAlpha and self.currentToken.value == "raw":
			self.getNextToken()
			url = self.currentToken.value[1:-1]
		elif self.currentToken.type == ShotToken.typeQuote:
			url = getStaticPath(self.currentToken.value[1:-1])
		else:
			self.parseError("expected raw or file path for favicon")
		
		href = ShotAttribute(name="href")
		href.value = "\"" + url + "\""
		node.attributes.append(href)
		
		fileExt = url.split(".")[-1]

		type = ShotAttribute(name="type")
		type.value = "\"image/"

		if fileExt == "ico":
			type.value += "x-icon"
		else:
			type.value=fileExt
		
		type.value += "\""

		node.attributes.append(type)

		return node

	def getRawScriptOrStyle(self):
	
		body = []
		
		depth = self.getDepth()
	
		self.currentLineNum += 1
		if self.currentLineNum < len(self.tokenizer.lines):
			line = self.tokenizer.lines[self.currentLineNum]
	
			while line.depth > depth:
				for i in range(line.depth):
					body.append("    ")
				for token in line.tokens:
					if token.type == ShotToken.typeText:
						token.value = ":" + token.value
					elif token.type == ShotToken.typeClass:
						token.value = "." + token.value
					elif token.type == ShotToken.typeID:
						token.value = "#" + token.value
					body.append(token.value + " ")
				body.append("\n")
		
				self.currentLineNum += 1
				if self.currentLineNum >= len(self.tokenizer.lines):
					break
				line = self.tokenizer.lines[self.currentLineNum]
		
			self.currentLineNum -= 1

		del body[-1] # get rid of last newline, was causing problems
		return ''.join(body)

	def getStyleElement(self):
		self.getNextToken()
		
		# raw css body
		if self.currentToken.type == ShotToken.typeEOL:
			node = ShotNode(tag="style",depth=self.getDepth(),parent=self.currentNode)
			node.children.append(ShotTextNode(text=self.getRawScriptOrStyle()))

		# single line body
		elif self.currentToken.type == ShotToken.typeText:
			node = ShotNode(tag="style",depth=self.getDepth(),parent=self.currentNode,multiline=False)
			node.children.append(ShotTextNode(text=self.currentToken.value))

		# link to file
		elif self.currentToken.type == ShotToken.typeQuote:
			self.currentTokenNum -= 1
			return self.includeFile()

		# scoped and media
		elif self.currentToken.type == ShotToken.typeAlpha:
			node = ShotNode(tag="style",depth=self.getDepth(),parent=self.currentNode)

			if self.currentToken.value == "scoped":
				scoped = ShotAttribute(name="scoped")
				node.attributes.append(scoped)
		
			elif self.currentToken.value == "media":
				attr = ShotAttribute(name="media")
				self.getNextToken()
				self.getNextToken()
				attr.value = self.currentToken.value
				
				node.attributes.append(attr)
				
			else:
				self.parseError("expected media or scoped in css attributes")

			self.getNextToken()
			
			if self.currentToken.type == ShotToken.typeEOL:
				node.children.append(ShotTextNode(text=self.getRawScriptOrStyle()))
				
			else:
				node.multiline=False
				node.children.append(ShotTextNode(text=self.currentToken.value))
			
		return node
		
	def getScriptElement(self):
		self.getNextToken()
		
		# raw js body
		if self.currentToken.type == ShotToken.typeEOL:
			node = ShotNode(tag="script",depth=self.getDepth(),parent=self.currentNode)
			node.children.append(ShotTextNode(text=self.getRawScriptOrStyle()))

		# single line body
		elif self.currentToken.type == ShotToken.typeText:
			node = ShotNode(tag="script",depth=self.getDepth(),parent=self.currentNode,multiline=False)
			node.children.append(ShotTextNode(text=self.currentToken.value))

		# link to file
		elif self.currentToken.type == ShotToken.typeQuote:
			self.currentTokenNum -= 1
			return self.includeFile()

		# async and defer
		elif self.currentToken.type == ShotToken.typeAlpha:
			node = ShotNode(tag="script",depth=self.getDepth(),parent=self.currentNode,multiline=False)

			if self.currentToken.value == "async" or self.currentToken.value == "defer":
				scoped = ShotAttribute(name=self.currentToken.value)
				node.attributes.append(scoped)

				self.getNextToken()

				attr = ShotAttribute(name="src")
				attr.value = self.currentToken.value
				node.attributes.append(attr)

			else:
				self.parseError("expected async or defer in js attributes")
			
		return node

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

	def getDirective(self):
		self.logCreation("directive")
	
		node = ShotNode(tag="directive",depth=self.getDepth(),parent=self.currentNode)
		
		text = []

		while self.currentToken.type != ShotToken.typeEOL:
			if self.currentToken.type == ShotToken.typeText:
				text.append(":" + self.currentToken.value)
			elif self.currentToken.type == ShotToken.typeClass:
				text.append("." + self.currentToken.value)
			elif self.currentToken.type == ShotToken.typeID:
				text.append("#" + self.currentToken.value)
			elif self.currentToken.type == ShotToken.typeEquals:
				text.append("=")
			elif self.currentToken.type == ShotToken.typeArrayOpener:
				text.append("[")
			elif self.currentToken.type == ShotToken.typeArrayCloser:
				text.append("]")
			elif self.currentToken.type == ShotToken.typeComma:
				text.append(",")
			else:
				text.append(self.currentToken.value)
			self.getNextToken()
		
		keyword = text[0]
		
		if keyword == "extends" or keyword == "include" or keyword == "import":

			if text[1][0] == "\"" or text[1][0] == "'":
				filename = text[1][1:-1]

				shot = Shot(filename, included=(True if keyword == "include" else False), logging=self.logging)
			
				newfilename, ext = splitext(shot.filename)
				text[1] = "\"" + newfilename + ".html\""
				shot.generateShot()
			
			if keyword == "extends":
				self.extending = True

				self.lookingForHead = False
				self.bodyCreated = True

				self.currentNode = self.rootNode
				del self.currentNode.children[:]
				node.parent = self.currentNode

		attr = ShotAttribute(name=keyword,value=' '.join(text))
		node.attributes.append(attr)

		self.currentNode.children.append(node)
		self.currentNode = node
	
		self.logFinishedCreation("directive")
		
	def getComment(self):
		node = ShotTextNode(text="<!-- "+self.currentToken.value+" -->",depth=self.getDepth())
		self.currentNode.children.append(node)

	def getBlockComment(self,secret=False):
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

		text = "" if secret else "<!--\n"+"".join(commentBody)+"-->"
		return ShotTextNode(text=text,depth=commentDepth)

	def getNodeWithTag(self):
		self.logCreation(self.currentToken.value)
		
		# comment check
		if self.currentToken.value == "comment":
			node = self.getBlockComment()
			
		elif self.currentToken.value == "disable" or self.currentToken.value == "secret":
			node = self.getBlockComment(secret=True)

		else:
#
#			OPTIONAL HEAD AND BODY TAGS
#
			if self.included:
				self.lookingForHead = False
				self.bodyCreated = True

			elif self.bodyCreated:
				self.lookingForHead = False
		
			elif self.lookingForHead:
				if self.currentToken.value == "head":
					self.lookingForHead = False
				elif self.currentToken.value != "doctype" and self.currentToken.value != "html":
					headElement = ShotNode(tag="head",depth=-1,parent=self.currentNode)
					self.currentNode.children.append(headElement)
					self.currentNode = headElement
			
					self.lookingForHead = False
				
					if self.currentToken.value not in tagsForHead:
						self.currentNode = self.currentNode.parent
						if self.currentToken.value != "body":
							bodyElement = ShotNode(tag="body",depth=-1,parent=self.currentNode)
							self.currentNode.children.append(bodyElement)
							self.currentNode = bodyElement
						
						self.bodyCreated = True

			else:
				if self.currentToken.value == "body":
					self.bodyCreated = True
					
			# template directive check		
			if self.currentToken.value in directiveOpeners:
				self.getDirective()
				return
	
			if self.currentToken.value == "favicon":
				node = self.getFaviconElement()

			elif self.currentToken.value == "br":
				node = self.getBreakElement()

			elif self.currentToken.value == "style" or self.currentToken.value == "css":
				node = self.getStyleElement()

			elif self.currentToken.value == "script" or self.currentToken.value == "js" or self.currentToken.value == "javascript":
				node = self.getScriptElement()

			else:
				if self.currentToken.value == "link":
					self.currentToken.value = "shots-link"
			
				node = ShotNode(tag=self.currentToken.value,depth=self.getDepth(),parent=self.currentNode)
				if node.tag in selfClosers:
					node.selfClosing = True
				
				self.currentNode.children.append(node)
				self.currentNode = node
				node = None
				
				blockText = False
				childElemNext = False
				
				self.getNextToken()
				while self.currentToken.type != ShotToken.typeEOL:
				
					if self.currentToken.type == ShotToken.typeAlpha:
						attr = ShotAttribute(name=self.currentToken.value)
						self.getNextToken()
						
						if self.currentToken.type != ShotToken.typeEquals:
							self.currentNode.attributes.append(attr)
							self.currentTokenNum -= 1

						else:
							self.getNextToken()
							
							if (self.currentNode.tag == "audio" or self.currentNode.tag == "video") and attr.name == "src":
								sources = []
							
								if self.currentToken.type == ShotToken.typeArrayOpener:
									self.getNextToken()

									while self.currentToken.type != ShotToken.typeArrayCloser:
										if self.currentToken.type == ShotToken.typeQuote:
											sources.append(self.currentToken.value)

										self.getNextToken()

									self.getNextToken()
									
								elif self.currentToken.type == ShotToken.typeQuote:
									sources.append(self.currentToken.value)

								else:
									self.parseError("expected quote or array after audio or video src")
								
								for s in sources:
									source = ShotNode(tag="source",depth=self.getDepth()+1,parent=self.currentNode,selfClosing=True)

									fileName = s[1:-1]
									fileExt = fileName.split(".")[-1]
									if fileExt == "mp3":
										fileExt = "mpeg"

									src = ShotAttribute(name="src",value="\"" + getStaticPath(fileName) + "\"")
									source.attributes.append(src)
									
									type = ShotAttribute(name="type")
									type.value = "\""+("audio" if self.currentNode.tag == "audio" else "video")+"/"+fileExt+"\""
									source.attributes.append(type)
									
									self.currentNode.children.append(source)
								
							elif self.currentToken.type == ShotToken.typeQuote:
								attr.value = self.currentToken.value
								self.currentNode.attributes.append(attr)

							else:
								self.parseError("expected quote after attribute")
					
					elif self.currentToken.type == ShotToken.typeClass:
						self.currentNode.classes.append(self.currentToken.value)
					
					elif self.currentToken.type == ShotToken.typeID:
						self.currentNode.id = self.currentToken.value
					
					elif self.currentToken.type == ShotToken.typeText:
						if self.currentToken.value == "":
							blockText = True
						else:
							if self.currentNode.tag == "audio" or self.currentNode.tag == "video":
								self.currentNode.children.append(ShotTextNode(text=self.currentToken.value,depth=self.getDepth()+1))
							else:
								self.currentNode.children.append(ShotTextNode(text=self.currentToken.value))
								self.currentNode.multiline = False
						break
						
					elif self.currentToken.type == ShotToken.typeChildElemNext:
						childElemNext = True
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
				
				elif childElemNext:
					self.currentNode.multiline = False
					self.currentNode.depth -= 1

					self.getNextNode()

					self.currentLineNum -= 1
					self.currentNode = self.currentNode.parent
					self.currentNode.depth += 1
		
		if node:
			self.currentNode.children.append(node)

	def getDepth(self):
		return self.tokenizer.lines[self.currentLineNum].depth

	def getNode(self):
		if self.reachedEOF():
			return None

		while self.getDepth() <= self.currentNode.depth:
			self.logFinishedCreation(self.currentNode.tag)
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
			self.logCreation("line comment")
			self.getComment()
			self.logFinishedCreation("line comment")

		else:
#
#			OPTIONAL HEAD AND BODY TAGS
#
			if not self.included and not self.bodyCreated:
				if self.lookingForHead:
					head = ShotNode(tag="head",depth=-1,parent=self.currentNode)
					self.currentNode.children.append(head)
					
					self.lookingForHead = False
				elif self.currentNode.tag == "head":
					self.currentNode = self.currentNode.parent
				
				body = ShotNode(tag="body",depth=-1,parent=self.currentNode)
				self.currentNode.children.append(body)

				self.currentNode = body
				self.bodyCreated = True

			if self.currentToken.type == ShotToken.typeText:
				self.logCreation("text")
				self.getText()
				self.logFinishedCreation("text")
		
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

	def generateCode(self):
		self.tokenize()
		self.parse()
	
		result = ""
		kids = self.rootNode.children
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
		result = re.sub(r"\|([^|]+)\|",r"{{ \1 }}",result)
		result = re.sub(r"= =",r"==",result)
		return result

# at the bottom to avoid import loop

from shot import Shot