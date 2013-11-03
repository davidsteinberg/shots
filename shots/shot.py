import sys

from file_assistant import *
from settings import settings
from parser import ShotParser

class Shot:
	def __init__(self, filename, logging=False):
		self.filename = get_template_path(shotify(filename))
		self.logging = logging

		if settings.developing or not isfile(htmlify(self.filename)):
			self.log("parsing " + self.filename)
			self.parser = ShotParser(self.filename, logging=self.logging)

		self.filename = htmlify(self.filename)

	def log(self, message):
		if self.logging:
			print message

	def generate_shot(self):
		if settings.developing or not isfile(self.filename):
			self.log("generating " + self.filename)
			code = self.parser.generate_code()
			self.log("\n    -- BEGIN GENERATED CODE --\n\n"+code+"\n\n    -- END GENERATED CODE --\n")
			write_shot_to_file(self.filename,shot=code)

	def render(self, **varArgs):
		self.generate_shot()
		template = get_template(self.filename)
		return template.render(**varArgs)

#-------------------------
# Main
#-------------------------

def main():
	before_jinja = False
	logging = False
	
	if len(sys.argv) < 2:
		exit("Usage : " + sys.argv[0] + " <filename> [-d]\n        " + sys.argv[0] + " requires at least a file name as a parameter, with an optional debug flag")
	elif len(sys.argv) > 2:
		if "-l" in sys.argv:
			logging = True
		if "-j" in sys.argv:
			before_jinja = True

	s = Shot(sys.argv[1], logging=logging)

	if before_jinja:
		print s.parser.generate_code()
	else:
		print s.render()

if __name__ == "__main__":
	main()
