import flask
from flask import request, jsonify
from utilities import *

processLimit = 5


app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
@app.route('/test_connection', methods=['GET'])
def home():
    es_status = connect()
    ret = {'elasticsearch': es_status}
    return jsonify(ret)


@app.route('/crawl', methods=['GET'])
def crawl():
    es_status = connect()
    if es_status == 'not_connected':
        return {'_status': 'error', 'error_type': 'elasticsearch_not_connected'}

    if 'ch' in request.args:
        if request.args['ch'] not in all_boards():
            return jsonify({'_status': 'error', 'error_type': 'channel_not_existing'})

        if 'max' in request.args and int(request.args['max']) > 0:
            max_proc = int(request.args['max'])
        else:
            max_proc = processLimit

        proc_num, total_posts, execution_time = single_crawl(request.args['ch'], max_proc)

        return {
            '_status': 'success',
            'channel': request.args['ch'],
            'execution_time_seconds': execution_time,
            'parallel_process': proc_num,
            'total_posts': total_posts
        }

    return {'_status': 'error', 'error_type': 'channel_not_specified'}


app.run()