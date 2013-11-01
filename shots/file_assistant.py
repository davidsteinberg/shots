from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from os import sep, walk
from os.path import abspath, dirname, splitext

_template_dir = sep + "templates"
_static_dir = sep + "static"

_environment = Environment(loader=FileSystemLoader(sep))

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

def get_template(filename):
	return _environment.get_template(filename)

def get_template_path(filename):
	found = False
	current_dir = dirname(dirname(abspath(__file__))) + _template_dir
	for root, dirs, files in walk(current_dir):
		if filename in files:
			found = True
			filename = current_dir + sep + filename
			break
	if not found:
		raise TemplateNotFound(filename)
	
	return filename

def get_static_path(filename):
	found = False
	current_dir = dirname(dirname(abspath(__file__))) + _static_dir
	for root, dirs, files in walk(current_dir):
		if filename in files:
			found = True
			filename = _static_dir + root.replace(current_dir, "", 1) + sep + filename
			break
	if not found:
		print "Error: couldn't find static file " + filename
	
	return filename
