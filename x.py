import requests
import os
import multiprocessing
from elasticsearch import Elasticsearch
from datetime import datetime

crawlTime = 0


# load data on ElasticSearch
def load(json_post):
    es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
    es.index(index='prova_4chan', ignore=400, body=json_post)


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
    info_page = []

    for i in range(0, len(threads)):
        endpoint = f"https://a.4cdn.org/{board}/thread/{threads[i]['no']}.json"
        data = get_json(endpoint)

        info_thread = []
        if data:
            for j in range(0, len(data['posts'])):
                global crawlTime

                data['posts'][j]['crawlTime'] = crawlTime
                data['posts'][j]['board'] = board

                load(data['posts'][j])
                info_thread.append(data['posts'][j])

        info_page.append(info_thread)

    return info_page


# returns every info about everything in a board
def thread_list(board):
    endpoint = f"https://a.4cdn.org/{board}/threads.json"
    data = get_json(endpoint)

    info_board = []
    for i in range(0, len(data)):
        print(f"Process {os.getpid()} working on board {board}")
        info_board.append(page_posts(board, data[i]['threads']))

    print(info_board)

    print(f"End of board {board} analysis")


manager = multiprocessing.Manager()


# retrieves the whole 4chan platform
def crawl():
    global crawlTime
    crawlTime = datetime.now()

    boards = list(all_boards())

    ex_b = manager.list()

    while True:
        children = []
        for k in range(0, len(boards)):
            pid = os.fork()
            if pid > 0:
                print("This is the parent process {}".format(os.getpid()))
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
