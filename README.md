Shots
=====

Shots is a templating language for Flask that strives for simplicity and speed.

Adding Shots to a Flask app is super simple.

1. Download the shots package
2. Put it in the same directory as app.py (or whatever your main file is called)
3. Write some Shots for your app and save them in your normal templates/ directory
4. In app.py, instead of calling render_template, instantiate a Shot and render it (passing any parameters you want)
5. Run your app

Check out [the docs](http://flaskshots.herokuapp.com/docs) for language details.

Here is one of the smallest Shots you can have:

###index.shot

```html
title : A Little Shot

h1 : This is a little Shot
```

###app.py

```python
from flask import Flask
from shots import Shot

app = Flask(__name__)

@app.route('/')
def index():
	return Shot('index').render()
	
if __name__ == '__main__':
	app.run()
```

###Look under the hood

To see the HTML output of a Shot, run:

```bash
python shots/shot.py {{ filename relative to templates folder }} [-d]
```

The -j (for jinja) flag will let you see a template before Jinja2 has processed it.  
The -l (for log) flag will let you see the step-by-step process of the parser.
