from flask import Flask
from flask import render_template
import json

app = Flask(__name__)

@app.route('/')
def index():
    ctx = {}
    return render_template('index.html', ctx=ctx)

@app.route('/full')
def full():
    # get obj
    ctx = {'title': 'All settings'}
    with open('config.json', 'r') as f:
        ctx['settings'] = json.load(f)
    return render_template('editor.html', ctx=ctx)


@app.route('/hamans')
def humans():
    pass


@app.route('/beasts')
def beasts():
    pass

if __name__ == '__main__':
    app.debug = True
    app.run()
