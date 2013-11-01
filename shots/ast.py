class ShotAttribute:
	def __init__(self, name, value=None):
		self.name = name
		self.value = value
	
	def __str__(self):
		if self.name == "css":
			self.name = "style"
		result = self.name
		if self.value:
			 result += "=" + self.value
		return result

class ShotTextNode:
	def __init__(self, text, depth=0):
		self.text = text
		self.depth = depth
	
	def __str__(self):
		result = ""
		for d in range(self.depth):
			result += "    "
		result += self.text
		return result

closeDirectives = ["block", "call", "filter", "macro", "raw"]

class ShotNode:
	def __init__(self, tag=None, parent=None, id=None, selfClosing=False, depth=0, multiline=True):
		self.id = id
		self.tag = tag
		self.classes = []
		self.attributes = []
		self.parent = parent
		self.children = []
		self.selfClosing = selfClosing
		
		self.depth = depth
		self.multiline = multiline

	def __str__(self):
		result = ""
		
		for d in range(self.depth):
			result += "    "
		
		if self.tag == "":
			for c in self.children:
				result += str(c)
		
		elif self.tag == "directive":
			if self.parent.tag == "comment":
				result = ""
			else:
				keyword = self.attributes[0].name
				text = self.attributes[0].value
			
				result += "{% " + text + " %}"
				if len(self.children) > 0:
					for c in self.children:
						result += "\n"
						kid = str(c)
						result += kid
					result += "\n"			
					for d in range(self.depth):
						result += "    "

				if keyword in closeDirectives:
					result += "{% end" + keyword + " %}"
				else:
					parent = self.parent
					currentIndex = parent.children.index(self)
					nextSibling = None if currentIndex+1 >= len(parent.children) else parent.children[currentIndex+1]

					deleteSpaces = False

					if keyword == "if" or keyword == "elif":
						if not nextSibling or (nextSibling.attributes[0].name != "elif" and nextSibling.attributes[0].name != "else"):
							result += "{% endif %}"
						else:
							deleteSpaces = True
					elif keyword == "for":
						if not nextSibling or nextSibling.attributes[0].name != "else":
							result += "{% endfor %}"
						else:
							deleteSpaces = True
					elif keyword == "else":
						prevSibling = parent.children[currentIndex-1]
						if prevSibling.attributes[0].name == "if" or prevSibling.attributes[0].name == "elif":
							result += "{% endif %}"
						elif prevSibling.attributes[0].name == "for":
							result += "{% endfor %}"
					
					if deleteSpaces:
						count = -1
						for d in range(self.depth):
							count -= 4
						result = result[:count]

		else:
			if self.tag == "shots-link":
				self.tag = "a"
				self.classes.append("shots-link")
				href = ""
				for attr in self.attributes:
					if attr.name == "to":
						self.attributes.append(ShotAttribute(name="href",value=attr.value))
						del self.attributes[self.attributes.index(attr)]
						break
		
			result += "<" + self.tag
			if self.id:
				result += " id=\"" + self.id + "\""
			if len(self.classes) > 0:
				result += " class=\"" + " ".join(self.classes) + "\""
			if len(self.attributes) > 0:
				for a in self.attributes:
					result += " " + str(a)
			result += ">"
			if not self.selfClosing:
				if self.multiline and len(self.children) > 0:
					for c in self.children:
						result += "\n"
						result += str(c)
					result += "\n"
					for d in range(self.depth):
						result += "    "
				else:
					for c in self.children:
						result += str(c).strip()
				result += "</" + self.tag + ">"
			
		return result
