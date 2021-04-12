import requests
import os
import multiprocessing
from elasticsearch import Elasticsearch
from datetime import datetime
import flask
from flask import request
from time import time

crawlTime = 0
processLimit = 5


# load data on ElasticSearch
def load(json_post):
    es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
    es.index(index='4chan_index', ignore=400, body=json_post)


# returns json data from a given page
def get_json(endpoint):
    response = requests.get(endpoint)

    if response.ok:
        json_data = response.json()
        return json_data
    elif response.status_code == 404:
        json_data = None
        return json_data
    else:
        print("Status Code: ", response.status_code)
        print("Response Content: ", response.content)


# returns list of all boards
def all_boards():
    endpoint = "https://a.4cdn.org/boards.json"
    data = get_json(endpoint)

    board_list = []
    for k in range(0, len(data['boards'])):
        board_list.append(data['boards'][k]['board'])

    return board_list


# returns info about every post and reply on a certain page
def page_posts(board, threads):
    for i in range(0, len(threads)):
        endpoint = f"https://a.4cdn.org/{board}/thread/{threads[i]['no']}.json"
        data = get_json(endpoint)

        if data:
            for j in range(0, len(data['posts'])):
                global crawlTime

                data['posts'][j]['crawlTime'] = crawlTime
                data['posts'][j]['board'] = board

                if "tim" in data['posts'][j] and data['posts'][j]['ext'] != ".swf":
                    data['posts'][j]['img_link'] = f"https://i.4cdn.org/{board}/{data['posts'][j]['tim']}{data['posts'][j]['ext']}"

                load(data['posts'][j])


# returns every info about everything in a board
def thread_list(board):
    endpoint = f"https://a.4cdn.org/{board}/threads.json"
    data = get_json(endpoint)

    for i in range(0, len(data)):
        print(f"Process {os.getpid()} working on board {board} at page {i}")
        print("Crawling...")
        page_posts(board, data[i]['threads'])

    print(f"End of board {board} analysis")


# allows multiple process to share an array
manager = multiprocessing.Manager()


# retrieves the whole 4chan platform
def full_crawl():
    global crawlTime

    crawlTime = datetime.now()

    boards = list(all_boards())

    ex_b = manager.list()

    while True:
        children = []
        for k in range(0, len(boards)):
            pid = os.fork()
            if pid > 0:
                children.append(pid)
            else:
                print("This is the child process {}".format(os.getpid()))
                print(f"Board associated: {boards[k]}")
                thread_list(boards[k])
                ex_b.append(boards[k])
                ex_b.sort()
                print(f"Examined {len(ex_b)} boards: {ex_b}. {len(boards)-len(ex_b)} remaining")
                print("Process {} exiting".format(os.getpid()))
                os._exit(0)

        for i, pr in enumerate(children):
            os.waitpid(pr, 0)

        break


# collects every post of a given channel
def single_crawl(channel, max_process):
    global crawlTime

    crawlTime = datetime.now()

    endpoint = f"https://a.4cdn.org/{channel}/threads.json"
    data = get_json(endpoint)

    print(f"The board {channel} has {len(data)} pages")

    children = []

    process_num = len(data) if len(data) < max_process else max_process
    crawl_num = int((len(data)-1)/max_process) + 1

    for i in range(0, process_num):
        pid = os.fork()
        if pid > 0:
            print("This is the parent process {}".format(os.getpid()))
            children.append(pid)
        else:
            print(f"Process {os.getpid()} working on board {channel} at page {i}")
            page_posts(channel, data[i]['threads'])
            if len(data) > max_process:
                for k in range(1, crawl_num):
                    if max_process*k+i < len(data):
                        print(f"Process {os.getpid()} working on board {channel} at page {max_process*k+i}")
                        page_posts(channel, data[max_process*k+i]['threads'])
            print("Process {} exiting".format(os.getpid()))
            os._exit(0)

    for j, pr in enumerate(children):
        os.waitpid(pr, 0)


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
