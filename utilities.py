import requests
import os
import multiprocessing
from elasticsearch import Elasticsearch
from datetime import datetime
import logging

logging.getLogger("elasticsearch").setLevel(logging.CRITICAL)

crawlTime = 0


def connect():
    try:
        Elasticsearch([{'host': 'localhost', 'port': '9200'}]).info()
        return "connected"
    except:
        return "not_connected"


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
    page_posts_number = 0
    for i in range(0, len(threads)):
        endpoint = f"https://a.4cdn.org/{board}/thread/{threads[i]['no']}.json"
        data = get_json(endpoint)

        if data:
            for j in range(0, len(data['posts'])):
                global crawlTime

                data['posts'][j]['crawlTime'] = crawlTime
                data['posts'][j]['board'] = board

                if "tim" in data['posts'][j] and data['posts'][j]['ext'] != ".swf":
                    data['posts'][j][
                        'img_link'] = f"https://i.4cdn.org/{board}/{data['posts'][j]['tim']}{data['posts'][j]['ext']}"

                load(data['posts'][j])
                page_posts_number += 1

    return page_posts_number


# allows multiple process to share an array
manager = multiprocessing.Manager()


# collects every post of a given channel
def single_crawl(channel, max_process):
    global crawlTime

    crawlTime = datetime.now()

    endpoint = f"https://a.4cdn.org/{channel}/threads.json"
    data = get_json(endpoint)

    print(f"The board {channel} has {len(data)} pages")

    posts = manager.list()

    children = []

    process_num = len(data) if len(data) < max_process else max_process
    crawl_num = int((len(data) - 1) / max_process) + 1

    for i in range(0, process_num):
        pid = os.fork()
        if pid > 0:
            print("This is the parent process {}".format(os.getpid()))
            children.append(pid)
        else:
            print(f"Process {os.getpid()} working on board {channel} at page {i}")
            posts_number = 0
            posts_number += page_posts(channel, data[i]['threads'])
            if len(data) > max_process:
                for k in range(1, crawl_num):
                    if max_process * k + i < len(data):
                        print(f"Process {os.getpid()} working on board {channel} at page {max_process * k + i}")
                        posts_number += page_posts(channel, data[max_process * k + i]['threads'])
            print("Process {} exiting".format(os.getpid()))
            posts.append(posts_number)
            os._exit(0)

    for j, pr in enumerate(children):
        os.waitpid(pr, 0)

    tot_posts = sum(posts)

    return process_num, tot_posts
