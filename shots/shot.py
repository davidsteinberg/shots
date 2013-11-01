import sys

from file_assistant import *
from parser import ShotParser

class Shot:
	def __init__(self, filename, overwrite=True, included=False, logging=False):
		filename = shotify(filename)

		self.filename = getTemplatePath(filename)
		self.overwrite = overwrite
		self.included = included
		self.logging = logging

		if self.overwrite or not isfile(self.filename):
			self.parser = ShotParser(self.filename, included=self.included, logging=self.logging)

		self.filename = htmlify(self.filename)

	def log(self, message):
		if self.logging:
			print message

	def generateShot(self):
		self.log("generating " + self.filename)
	
		if self.overwrite or not isfile(self.filename):
			code = self.parser.generateCode()
			self.log("\nCODE\n\n"+code+"\n\nEND CODE\n")
			write_shot_to_file(self.filename,shot=code)
			
	def render(self, **varArgs):
		self.generateShot()
		template = getTemplate(self.filename)
		return template.render(**varArgs)

#-------------------------
# Main
#-------------------------

def main():
	beforeJinja = False
	logging = False
	
	if len(sys.argv) < 2:
		exit("Usage : " + sys.argv[0] + " <filename> [-d]\n        " + sys.argv[0] + " requires at least a file name as a parameter, with an optional debug flag")
	elif len(sys.argv) > 2:
		if "-l" in sys.argv:
			logging = True
		if "-j" in sys.argv:
			beforeJinja = True

	s = Shot(sys.argv[1], overwrite=True, logging=logging)

	if beforeJinja:
		print s.parser.generateCode()
	else:
		print s.render()

if __name__ == "__main__":
	main()
