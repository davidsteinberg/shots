from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from os import sep, walk
from os.path import abspath, dirname, splitext

templateDir = sep + "templates"
staticDir = sep + "static"

environment = Environment(loader=FileSystemLoader(sep))

def getTemplate(filename):
	return environment.get_template(filename)

def getTemplatePath(filename):
	found = False
	currentDir = dirname(dirname(abspath(__file__))) + templateDir
	for root, dirs, files in walk(currentDir):
		if filename in files:
			found = True
			filename = currentDir + sep + filename
			break
	if not found:
		raise TemplateNotFound(filename)
	
	return filename

def getStaticPath(fileName):
	found = False
	currentDir = dirname(dirname(abspath(__file__))) + staticDir
	for root, dirs, files in walk(currentDir):
		if fileName in files:
			found = True
			fileName = staticDir + root.replace(currentDir, "", 1) + sep + fileName
			break
	if not found:
		print "Error: couldn't find static file " + fileName
	
	return fileName
