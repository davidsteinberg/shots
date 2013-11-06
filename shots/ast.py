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
			result += " "
		result += self.text
		return result

_close_directives = ["block", "call", "filter", "macro", "raw"]

class ShotNode:
	def __init__(self, tag=None, parent=None, id=None, self_closing=False, depth=0, multiline=True):
		self.id = id
		self.tag = tag
		self.classes = []
		self.attributes = []
		self.parent = parent
		self.children = []
		self.self_closing = self_closing
		
		self.depth = depth
		self.multiline = multiline

	def __str__(self):
		result = ""
		
		for d in range(self.depth):
			result += " "
		
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
						result += " "

				if keyword in _close_directives:
					result += "{% end" + keyword + " %}"
				else:
					parent = self.parent
					current_index = parent.children.index(self)
					next_sibling = None if current_index+1 >= len(parent.children) else parent.children[current_index+1]

					delete_spaces = False

					if keyword == "if" or keyword == "elif":
						if not next_sibling or isinstance(next_sibling,ShotTextNode) or len(next_sibling.attributes) == 0 or (next_sibling.attributes[0].name != "elif" and next_sibling.attributes[0].name != "else"):
							result += "{% endif %}"
						else:
							delete_spaces = True
					elif keyword == "for":
						if not next_sibling or isinstance(next_sibling,ShotTextNode) or len(next_sibling.attributes) == 0 or next_sibling.attributes[0].name != "else":
							result += "{% endfor %}"
						else:
							delete_spaces = True
					elif keyword == "else":
						prev_sibling = parent.children[current_index-1]
						if prev_sibling.attributes[0].name == "if" or prev_sibling.attributes[0].name == "elif":
							result += "{% endif %}"
						elif prev_sibling.attributes[0].name == "for":
							result += "{% endfor %}"
					
					if delete_spaces:
						count = -1
						for d in range(self.depth):
							count -= 1
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
			if not self.self_closing:
				if self.multiline and len(self.children) > 0:
					for c in self.children:
						result += "\n"
						result += str(c)
					result += "\n"
					for d in range(self.depth):
						result += " "
				else:
					for c in self.children:
						result += str(c).strip()
				result += "</" + self.tag + ">"
			
		return result
