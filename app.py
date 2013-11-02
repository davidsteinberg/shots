from flask import Flask
from shots import Shot, settings

app = Flask(__name__)

settings.app = app
settings.developing = True

@app.route('/')
@app.route('/<page>')
def router(page=None):
	if page:
		return Shot(page).render(page=page)
	else:
		return Shot('index',logging=True).render()

if __name__ == '__main__':
	app.debug = True
	app.run()

