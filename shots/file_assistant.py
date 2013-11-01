from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from os import sep, walk
from os.path import abspath, dirname, splitext

_template_dir = "templates"
_static_dir = "static"

_environment = Environment(loader=FileSystemLoader(sep))

def shotify(filename):
	filename, ext = splitext(filename)
	if ext and ext != ".shot":
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

_dirpath = dirname(dirname(abspath(__file__)))

def _search_for_file_in_dir(dir,filename=""):
	if filename == "":
		print "Error: searching for a blank filename"
		return

	found = False

	for dirpath, dirs, files in walk(_dirpath + sep + dir):
		if filename in files:
			return dirpath + sep + filename
			found = True
			break

		if not found:
			for d in dirs:
				path = _search_for_file_in_dir(dir + sep + d,filename)
				if path:
					return path

	return None

def get_template_path(filename):
	path = _search_for_file_in_dir(_template_dir,filename)
	if path:
		return path

	raise TemplateNotFound(filename)

def get_static_path(filename):
	path = _search_for_file_in_dir(_static_dir,filename)
	if path:
		return path

	print "Error: couldn't find static file " + filename
	return filename
