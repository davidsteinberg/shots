from flask import Flask
from shots import Shot

app = Flask(__name__)

@app.route('/')
def index():
	things = ["fun", "thinking"]
	return Shot('index.html').render(topStuff=things)

@app.route('/bootstrap')
def bootstrap():
	return Shot('bootstrap.html').render()

if __name__ == '__main__':
	app.debug = True
	app.run()

