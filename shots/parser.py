#-------------------------
# Parser
#-------------------------

from ast import *
from tokenizer import *

from os import sep, walk
from os.path import abspath, dirname

class ShotParser:

	selfClosers = ["area", "base", "br", "col", "command", "doctype", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source", "track", "wbr"]
	tagsForHead = ["base", "comment", "css", "favicon", "fetch", "include", "js", "javascript", "meta", "noscript", "script", "style", "title"]

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
		self.fillingHead = True
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
	
		if fileExt == "html":
			if fetch:
				fileName = "." + getTemplatePath(fileName)
				
			p = ShotParser(fileName,included=True)
			p.tokenize()
			p.parse()
			
			node = ShotNode(tag="",depth=self.getDepth(),parent=self.currentNode)
			for kid in p.rootNode.children:
				node.children.append(kid)
			
			return node
			
		else:
			if fetch:
				fileName = getStaticPath(fileName)
		
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

	def getDirective(self,closing=False):
		node = ShotNode(tag="templateDirective",depth=self.getDepth(),parent=self.currentNode)
		
		text = self.currentToken.value
		
		pieces = text.split(" ")
		keyword = pieces[0]
		
		if keyword == "extends":
			self.extending = True
			self.currentNode = self.rootNode
			del self.currentNode.children[:]
			node.parent = self.currentNode
		
		if keyword == "extends" or keyword == "include" or keyword == "import":
			filename = pieces[1][1:-1]
			shot = Shot(filename,logging=self.logging)
			text = text.replace(filename, locate(filename) + fileSuffix)
			shot.generateShot()
			
			self.lookingForHead = False
			self.fillingHead = False
			self.bodyCreated = True
		
		if not closing:
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
		self.logCreation(self.currentToken.value)
	
		if self.currentToken.value == "comment":
			node = self.getBlockComment()

		else:
#
#			OPTIONAL HEAD AND BODY TAGS
#
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
				node = self.getLinkElement()
				
			elif self.currentToken.value == "favicon":
				node = self.getFaviconElement()

			elif self.currentToken.value == "br":
				node = self.getBreakElement()

			elif self.currentToken.value == "style" or self.currentToken.value == "css":
				node = self.getStyleElement()

			elif self.currentToken.value == "script" or self.currentToken.value == "js" or self.currentToken.value == "javascript":
				node = self.getScriptElement()

			else:
				node = ShotNode(tag=self.currentToken.value,depth=self.getDepth(),parent=self.currentNode)
				if node.tag in ShotParser.selfClosers:
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
			if not self.bodyCreated:
				if self.lookingForHead:
					head = ShotNode(tag="head",depth=-1,parent=self.currentNode)
					self.currentNode.children.append(head)
				else:
					self.currentNode = self.currentNode.parent

				body = ShotNode(tag="body",depth=-1,parent=self.currentNode)
				self.currentNode.children.append(body)

				self.currentNode = body
				self.bodyCreated = True

			if self.currentToken.type == ShotToken.typeText:
				self.logCreation("text")
				self.getText()
				self.logFinishedCreation("text")

			elif self.currentToken.type == ShotToken.typeDirective:
				self.logCreation("directive")
				self.getDirective()
				self.logFinishedCreation("directive")
				
			elif self.currentToken.type == ShotToken.typeDirectiveSelfClosing:
				self.logCreation("self closing directive")
				self.getDirective(closing=True)
				self.logFinishedCreation("self closing directive")
		
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
			if self.extending:
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

		# last minute regex for template delimiters
		result = re.sub(r"\|([^|]+)\|",r"{{ \1 }}",result)
		return result


#-------------------------
# Finding Resources
#-------------------------

def getStaticPath(fileName):

	staticDir = "/static"

	found = False
	currentDir = dirname(dirname(abspath(__file__))) + staticDir
	for root, dirs, files in walk(currentDir):
		if fileName in files:
			found = True
			fileName = staticDir + root.replace(currentDir, "", 1) + sep + fileName
			break
	if not found:
		print "Error: couldn't find file " + fileName
	
	return fileName

from shot import fileSuffix, locate, Shot