from flask import Flask
from shots import Shot

app = Flask(__name__)

@app.route('/')
def index():
	return Shot('index.html').render()

if __name__ == '__main__':
	app.debug = True
	app.run()

