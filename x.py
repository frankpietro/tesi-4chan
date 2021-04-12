import flask
from flask import request
from time import time
from utilities import *

processLimit = 5


app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    return "<h1>Hello world!</h1>"


@app.route('/crawl', methods=['GET'])
def crawl():
    start = time()
    if 'ch' in request.args:
        if request.args['ch'] not in all_boards():
            return f"<h1>Error</h1><p>Channel {request.args['ch']} not existing </p>"

        if 'max' in request.args and int(request.args['max']) > 0:
            single_crawl(request.args['ch'], int(request.args['max']))
        else:
            single_crawl(request.args['ch'], processLimit)

        end = time()

        return f"<h1>Success</h1><p>Crawl of channel {request.args['ch']} executed in {end - start} seconds</p>"

    return "<h1>Error</h1><p>'ch' argument missing</p>"


app.run()
