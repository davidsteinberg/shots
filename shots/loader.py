import codecs

from jinja2.loaders import BaseLoader
from jinja2.exceptions import TemplateNotFound

from os import sep, walk
from os.path import abspath, dirname, getmtime, join

from parser import ShotParser

class ShotLoader(BaseLoader):

	templateDir = "/templates"

	def __init__(self, path=None):
		self.path = path

	def get_source(self, environment, filename):
		
		print "load " + filename
		
		found = False
		currentDir = dirname(dirname(abspath(__file__))) + ShotLoader.templateDir
		for root, dirs, files in walk(currentDir):
			if filename in files:
				found = True
				filename = currentDir + sep + filename
				break
		if not found:
			raise TemplateNotFound(filename)
	
		parser = ShotParser(filename)
		contents = parser.generateCode()
		
		mtime = getmtime(filename)

		def uptodate():
			try:
				return getmtime(filename) == mtime
			except OSError:
				return False

		return contents, filename, uptodate
