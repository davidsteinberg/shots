from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from os import makedirs, sep, walk
from os.path import abspath, dirname, exists, isfile, splitext

from settings import settings

_environment = Environment(loader=FileSystemLoader("/"),extensions=["jinja2.ext.do","jinja2.ext.loopcontrols"])

_dirpath = dirname(dirname(abspath(__file__)))

def get_template_dir():
    if settings.app:
        template_dir = settings.app.template_folder
    elif settings.template_dir:
        template_dir = settings.template_dir
    return template_dir

def get_static_dir():
    if settings.app:
        static_dir = settings.app.static_folder.replace(_dirpath + sep,"")
    elif settings.static_dir:
        static_dir = settings.static_dir
    return static_dir

def shotify(filename):
    filename, ext = splitext(filename)
    if ext and ext != ".shot":
        filename += "." + ext
    filename += ".shot"
    return filename
    
def htmlify(filename):
    template_dir = get_template_dir()

    html_dir = _dirpath + sep + template_dir + sep + (settings.html_dir)
    if not exists(html_dir):
        makedirs(html_dir)

    path = html_dir
    
    dir_chain = filename.replace(_dirpath + sep + template_dir + sep,"").split("/")
    for d in range(len(dir_chain)-1):
        path += sep + dir_chain[d]
        if not exists(path):
            makedirs(path)

    # this is safe, because we have definitely added the ".shot" ending at this point
    filename, ext = splitext(filename)
    filename += ".html"
    return filename.replace(template_dir,template_dir + sep + "html")

def write_shot_to_file(filename,shot=""):
    f = open(filename, "w")
    f.write(shot)
    f.close()

def get_template(filename):
    return _environment.get_template(filename)

def _search_for_file_in_dir(dir,filename=""):
    if filename == "":
        print "Error: searching for a blank filename"
        return

    for dirpath, dirs, files in walk(_dirpath + sep + dir):
        if filename in files:
            return dirpath + sep + filename

        for d in dirs:
            path = _search_for_file_in_dir(dir + sep + d,filename)
            if path:
                return path

    return None

def get_template_path(filename):
    path = _search_for_file_in_dir(get_template_dir(),filename)
    if path:
        return path

    raise TemplateNotFound(filename)

def get_static_path(filename):
    path = _search_for_file_in_dir(get_static_dir(),filename)
    if path:
        return path.replace(_dirpath,"")

    print "Error: couldn't find static file " + filename
    return filename

def get_lib_path(filename):
    lib_dir = get_template_dir() + sep + (settings.lib_dir)
    path = _search_for_file_in_dir(lib_dir,filename)
    if path:
        return path

    print "Error: couldn't find lib " + filename
    return filename
