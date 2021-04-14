import flask
from flask import request
from utilities import *

processLimit = 5


app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
@app.route('/test_connection', methods=['GET'])
def home():
    es_status = connect()
    return {'elasticsearch': es_status}


@app.route('/crawl', methods=['GET'])
def crawl():
    es_status = connect()
    if es_status == 'not_connected':
        return {'_status': 'error', 'error_type': 'elasticsearch_not_connected'}

    if 'ch' in request.args:
        if request.args['ch'] not in all_boards():
            return {'_status': 'error', 'error_type': 'channel_not_existing'}

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


@app.route('/create_log', methods=['GET'])
def log():
    create_log_file()
    return {'log': 'created'}


@app.route('/delete_index', methods=['GET'])
def delete_index():
    if 'index' in request.args:
        try:
            es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
        except:
            return {'_status': 'error', 'error_type': 'elasticsearch_not_connected'}
        if es.indices.exists(request.args):
            try:
                es.indices.delete(request.args['index'])
            except:
                return {'_status': 'error', 'error_type': 'deletion_failed'}

            return {'_status': 'ok', 'deleted_index': request.args['index']}

        return {'_status': 'error', 'error_type': 'index_not_existing', 'index': f"{request.args['index']}"}

    return {'_status': 'error', 'error_type': 'index_not_specified'}


@app.route('/check_log', methods=['GET'])
def check_log():
    if not os.path.exists("logfile.txt"):
        return {'_status': 'no_log_file'}

    f = open("logfile.txt", "r")
    logs = f.readlines()
    for log_line in reversed(logs):
        if log_line.startswith("(S)"):
            return {'_status': 'no_current_crawling'}
        if log_line.startswith("(E)"):
            return {'_status': 'error', 'error_log': log_line}

    return {'_status': 'crawling_ok'}


app.run()
