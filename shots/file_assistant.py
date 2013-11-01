from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from os import sep, walk
from os.path import abspath, dirname, splitext

templateDir = sep + "templates"
staticDir = sep + "static"

environment = Environment(loader=FileSystemLoader(sep))

def shotify(filename):
	filename, ext = splitext(filename)
	if ext and ext != "shot":
		filename += "." + ext
	filename += ".shot"
	return filename
	
def htmlify(filename):
	filename, ext = splitext(filename)
	filename += ".html"
	return filename

def write_shot_to_file(filename,shot=""):
	f = open(filename, "w")
	f.write(shot)
	f.close()

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
