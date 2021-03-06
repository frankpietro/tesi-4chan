import requests
import multiprocessing
from elasticsearch import Elasticsearch
import logging
import re
from time import time
from log_functions import *
from nltk.corpus import stopwords

logging.getLogger("elasticsearch").setLevel(logging.CRITICAL)

crawlTime = 0

mapping = {
    "mappings": {
        "properties": {
            "no": {
                "type": "keyword"
            },
            "now": {
                "type": "date",
                "format": "MM/dd/yy(EEE)HH:mm:ss"
            },
            "resto": {
                "type": "keyword"
            },
            "time": {
                "type": "date",
                "format": "epoch_second"
            }
        }
    }
}

board_list = [
    '3', 'a', 'aco', 'adv', 'an', 'asp', 'b', 'bant', 'biz', 'c', 'cgl', 'ck',
    'cm', 'co', 'd', 'diy', 'e', 'f', 'fa', 'fit', 'g', 'gd', 'gif', 'h',
    'hc', 'his', 'hm', 'hr', 'i', 'ic', 'int', 'jp', 'k', 'lgbt', 'lit', 'm',
    'mlp', 'mu', 'n', 'news', 'o', 'out', 'p', 'po', 'pol', 'pw', 'qa', 'qst',
    'r', 'r9k', 's', 's4s', 'sci', 'soc', 'sp', 't', 'tg', 'toy', 'trash',
    'trv', 'tv', 'u', 'v', 'vg', 'vip', 'vm', 'vmg', 'vp', 'vr', 'vrpg',
    'vst', 'vt', 'w', 'wg', 'wsg', 'wsr', 'x', 'xs', 'y'
]

clean_r = re.compile(
    '<.*?>|&gt;&gt;[0-9]{1,8}|&([a-z0-9]+;|#[0-9]{1,6}|#x[0-9a-f]{1,6})|#p[0-9]{1,8};'
)

url_r = re.compile(r'(https?://\S+)')

stop_words = set(stopwords.words('english'))
stop_words.update({
    "what's", "everything", "+", "anyone", "nothing", "instead", "already",
    "-", "another", "whatever", "enough", "everyone", "else", "never", "fuck",
    "don't", "ago", "someone", "many", "without", "they're", "since", "gonna",
    "around", "there's", "getting", "every", "any", "ever", "dont", "oh",
    "probably", "always", "something", "anything",  "also", "literally", "im",
    "though", "shit", "actually", "going", "yes", "shit", "well", "yeah",
    "even", "fucking", "us", "can't", "this", "that", "got", "have", "go",
    'i', "i'd", "i've", "much", "could", "i'll", "i'm", "like", "one", "get",
    "that's", "go", "make", "still", "really", "post", "would",
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
})


# useful for Flask APIs
def error_json(error_type):
    return {'_status': 'error', 'error_type': error_type}


# inputs html, outputs plain text without tags or html entities
def clean_html(raw_html):
    return re.sub(
        clean_r,
        '',
        raw_html.replace('&#039;', '\'').replace('<br>', ' ').replace('&amp;', '&')
    )


def find_urls(raw_html):
    return re.findall(url_r, raw_html)


# checks Elasticsearch connection
def connect():
    try:
        Elasticsearch([{'host': 'localhost', 'port': '9200'}]).info()
        return "connected"
    except:
        return "not_connected"


# load data on ElasticSearch
def load(index, json_post):
    try:
        es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
        es.index(index=index, id=json_post['no'], body=json_post)
    except:
        log_warning(
            f"Error while loading post {json_post['no']} on Elasticsearch"
        )


# returns json data from a given page
def get_json(endpoint):
    response = requests.get(endpoint)

    if response.ok:
        json_data = response.json()
        return json_data
    elif response.status_code == 404:
        log_warning(f"Could not reach {endpoint}")
        return -1
    else:
        log_warning(
            f"Error {response.status_code} while trying to reach {endpoint}."
            f"Response: {response.content}"
        )
        return -1


# returns list of all boards
def all_boards():
    return board_list


# returns info about every post and reply on a certain page
def page_posts(index, board, threads):
    page_posts_number = 0
    for i in range(0, len(threads)):
        endpoint = f"https://a.4cdn.org/{board}/thread/{threads[i]['no']}.json"
        data = get_json(endpoint)

        if data == -1:
            return -1

        for j in range(0, len(data['posts'])):
            global crawlTime

            data['posts'][j]['crawlTime'] = crawlTime
            data['posts'][j]['board'] = board
            data['posts'][j]['endpoint'] = endpoint

            if "com" in data['posts'][j]:
                data['posts'][j]['plain_text'] = clean_html(
                    data['posts'][j]['com']
                )

                data['posts'][j]['urls'] = find_urls(
                    data['posts'][j]['plain_text']
                )

                all_words = data['posts'][j]['plain_text'].\
                    lower().replace('.', '').\
                    replace(',', '').replace('?', '').split()

                data['posts'][j]['all_words'] = all_words
                data['posts'][j]['main_words'] = [
                    w for w in all_words if w not in stop_words
                ]

            if "tim" in data['posts'][j] and data['posts'][j]['ext'] != ".swf":
                data['posts'][j]['img_link'] =\
                    f"https://i.4cdn.org/{board}/{data['posts'][j]['tim']}{data['posts'][j]['ext']}"

            load(index, data['posts'][j])
            page_posts_number += 1

    return page_posts_number


# allows multiple process to share resources
manager = multiprocessing.Manager()


# collects every post of a given channel
def single_crawl(index, channel, max_process):
    create_log_file()
    log_write(f"Crawling channel {channel}")

    global crawlTime
    crawlTime = datetime.now()

    start = time()

    try:
        es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
    except:
        log_warning("Failed to connect to Elasticsearch")
        log_abort()
        return 0, 0, 0

    if not es.indices.exists(index):
        log_write(f"Index {index} not existing. Creating")
        try:
            es.indices.create(index=index, body=mapping)
            log_write(f"Creation of index {index} successful")
        except:
            log_warning(f"Creation of index {index} failed. Aborting")
            return 0, 0, 0

    endpoint = f"https://a.4cdn.org/{channel}/threads.json"
    data = get_json(endpoint)
    if not data:
        log_abort()
        return 0, 0, 0

    pg = "page" if len(data) == 1 else "pages"
    log_write(f"Channel {channel} has {len(data)} {pg}")

    posts = manager.list()

    children = []

    process_num = len(data) if len(data) < max_process else max_process
    crawl_num = int((len(data) - 1) / max_process) + 1

    ch = "child" if process_num == 1 else "children"

    log_write(f"Parent process {os.getpid()} creating {process_num} {ch}")

    for i in range(0, process_num):
        pid = os.fork()
        if pid > 0:
            children.append(pid)
        else:
            log_write(
                f"Process {os.getpid()} working on board {channel} at page {i}"
            )

            posts_number = 0
            new_posts = page_posts(index, channel, data[i]['threads'])
            if new_posts != -1:
                posts_number += new_posts

            if len(data) > max_process:
                for k in range(1, crawl_num):
                    if max_process * k + i < len(data):
                        log_write(
                            f"Process {os.getpid()} working on board {channel}"
                            f" at page {max_process * k + i}"
                        )

                        new_posts = page_posts(
                            index,
                            channel,
                            data[max_process * k + i]['threads']
                        )

                        if new_posts != -1:
                            posts_number += new_posts

            log_write("Process {} exiting".format(os.getpid()))
            posts.append(posts_number)
            os._exit(0)

    for j, pr in enumerate(children):
        os.waitpid(pr, 0)

    log_end(f"Crawling of channel {channel} ended")

    tot_posts = sum(posts)

    end = time()
    execution_time = round(end - start, 3)

    return process_num, tot_posts, execution_time
