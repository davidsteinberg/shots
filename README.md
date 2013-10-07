Shots
=====

Shots is a templating language for Flask (and Python/Jinja in general) that strives for simplicity and speed.

Adding Shots to a Flask app is super simple.

1. Download shots.py
2. Put it in the same directory as 'app.py' (or whatever your main file is called)
3. Write some Shots for your app and save them in the templates folder
4. In app.py, instead of calling render_template(...), instantiate a Shot and .render() it
5. Run your app

Here is one of the smallest Shots you can have:

###index.html

```html
head : title : 'My First Shot'
body : 'This is my first Shot'
```

###app.py

```python
from flask import Flask
from shots import Shot

app = Flask(__name__)

@app.route('/')
def index():
	return Shot("index.html").render()
	
if __name__ == '__main__':
	app.run()
```

Check out [the docs](http://flaskshots.herokuapp.com/docs) for more details.

