#-------------------------
# AST Parts
#-------------------------

class ShotsAttribute:
	def __init__(self, name, value=None):
		self.name = name
		self.value = value
	
	def __str__(self):
		result = self.name
		if self.value:
			 result += "=" + self.value
		return result

class ShotsTextNode:
	def __init__(self, text, depth=0):
		self.text = text
		self.depth = depth
	
	def __str__(self):
		result = ""
		for d in range(self.depth):
			result += "\t"
		result += self.text
		return result

class ShotsNode:
	def __init__(self, tag=None, parent=None, id=None, selfClosing=False, depth=0, multiline=False):
		self.id = id
		self.tag = tag
		self.classes = []
		self.attributes = []
		self.parent = parent
		self.children = []
		self.selfClosing = selfClosing
		
		self.depth = depth
		self.multiline = multiline
		
		self.makingAnID = False
		self.lookingForAttributes = False
		self.addingClasses = False
		self.elementHasID = False
		self.definingInnerHTML = False
		self.makingStyleOrScript = False
		self.addingDelimiter = False
		self.addingDirective = False
		self.makingLiteralTextBlock = False
		self.willBeMakingLiteralTextBlock = False
		self.makingSrcOrHref = False

		self.finished = False

	def __str__(self):
		result = ""
		for d in range(self.depth):
			result += "\t"
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
			if self.multiline:
				for c in self.children:
					result += "\n"
					result += str(c)
				result += "\n"
				for d in range(self.depth):
					result += "\t"
			else:
				for c in self.children:
					result += str(c)
			result += "</" + self.tag + ">"
		return result
