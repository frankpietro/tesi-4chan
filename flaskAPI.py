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
        return error_json('elasticsearch_not_connected')

    if 'index' not in request.args:
        return error_json('index_not_specified')

    if 'channel' in request.args:
        if request.args['channel'] not in all_boards():
            return error_json('channel_not_existing')

        if 'max_proc' in request.args and int(request.args['max_proc']) > 0:
            max_proc = int(request.args['max_proc'])
        else:
            max_proc = processLimit

        proc_num, total_posts, execution_time = single_crawl(request.args['index'], request.args['channel'], max_proc)

        if proc_num == 0:
            return error_json('crawling_aborted')

        return {
            '_status': 'success',
            'channel': request.args['channel'],
            'execution_time_seconds': execution_time,
            'parallel_process': proc_num,
            'total_posts': total_posts
        }

    return error_json('channel_not_specified')


@app.route('/check_log', methods=['GET'])
def check_log():
    if not os.path.exists("logfile.txt"):
        return {'_status': 'no_log_file'}

    f = open("logfile.txt", "r")
    logs = f.readlines()
    errors = ''
    for log_line in reversed(logs):
        if log_line.startswith("(S)"):
            return {'_status': 'crawling_ended'}
        if log_line.startswith("(A)"):
            return {'_status': 'crawling_aborted'}
        if log_line.startswith("(E)"):
            errors += log_line

    if errors != '':
        return {'_status': 'warning', 'error_log': errors}

    return {'_status': 'crawling_ok'}


@app.route('/delete_index', methods=['GET'])
def delete_index():
    if 'index' in request.args:
        try:
            es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
        except:
            return error_json('elasticsearch_not_connected')
        if es.indices.exists(request.args['index']):
            try:
                es.indices.delete(request.args['index'])
            except:
                return error_json('deletion_failed')

            return {'_status': 'ok', 'deleted_index': request.args['index']}

        return {'_status': 'error', 'error_type': 'index_not_existing', 'index': request.args['index']}

    return error_json('index_not_specified')


app.run()
