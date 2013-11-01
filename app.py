from flask import Flask
from shots import Shot

app = Flask(__name__)

@app.route('/')
@app.route('/<page>')
def index(page=None):
	if page:
		return Shot(page).render(page=page)
	else:
		return Shot('index').render()

if __name__ == '__main__':
	app.debug = True
	app.run()

