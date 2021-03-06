import os
from datetime import datetime


def create_log_file():
    if os.path.exists("logfile.txt"):
        os.remove("logfile.txt")
    f = open("logfile.txt", "x")
    f.close()


def log_write(message):
    log_mess("(I)", message)


def log_warning(message):
    log_mess("(W)", message)


def log_end(message):
    log_mess("(F)", message)


def log_abort():
    log_mess("(A)", "Crawling aborted")


def log_mess(tag, message):
    timestamp = str(datetime.now())
    f = open("logfile.txt", "a")
    f.write(f"{tag} {timestamp} {message}\n")
    f.close()
