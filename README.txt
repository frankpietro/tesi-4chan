This project features a Flask-based crawler for 4chan.

APIs: /test_connection, /crawl, /check_log, /delete_index


/test_connection - no parameters

Checks if there is a stable connection to Elasticsearch. Returns a JSON with this information only.

Example:
- localhost:5000/test_connection
- {
    "elasticsearch": "connected"
  }
  
  
/crawl - parameters: index, channel, max_proc

<index> is mandatory and is the name of the Elasticsearch index you want to load posts on. If it does not already exists, it is created with a mapping suited for 4chan posts.
<channel> is mandatory and is the tag of the channel you want to examine. It has to be one of the 79 (currently) existing channel, or an error is returned.
<max_proc> is optional - default value for this variable is 5 - and is the maximum number of working processes the parent process creates.

Main function of the project. Takes three inputs and proceeds to load every post of the channel <channel> on the Elasticsearch index <index>, using a multiprocess approach with no more than <max_proc> parallel processes.
During the execution, a log file is created and filled with logs about the execution. This log_file can be checked with /check_log.
Does not output anything before every process has ended his crawling job.
Returns either an error JSON if there is a non-recoverable error, or a JSON with informations about the execution such as execution time, effective parallel processes used and total post loaded.

Examples:
- localhost:5000/crawl?index=4chan_index&channel=f&max_proc=5
- {
    "_status": "success",
    "channel": "f",
    "execution_time_seconds": 24.652,
    "parallel_process": 1,
    "total_posts": 55
  }

- localhost:5000/crawl?index=4chan_index&channel=f&max_proc=5
- {
    "_status": "error",
    "error_type": "crawling_aborted"
  }

- localhost:5000/crawl?channel=f&max_proc=5
- {
    "_status": "error",
    "error_type": "index_not_specified"
  }
  

/check_log - no parameters

Checks the log file. Log entries can be info logs (I), warnings (W), end logs (F) or abort logs (A).
Log entry format is <tag> <timestamp> <information>.
If there is an end tag, returns an end JSON. Same thing with the abort tag.
If there are any warning tags, returns every one of them in a single JSON entry and the last one separately.
If there are only info tag, it returns an ok JSON.

Examples:
- localhost:5000/check_log
- {
    "_status": "crawling_ok"
  }

- localhost:5000/check_log
- {
    "_status": "crawling_ended"
  }

- localhost:5000/check_log
- {
    "_status": "crawling_aborted"
  }

- localhost:5000/check_log
- {
    "_status": "warning",
    "last_warning": "(W) 2021-04-17 18:51:46.160436 Error while loading post 36402 on Elasticsearch",
    "warning_log": "(W) 2021-04-17 18:51:46.160436 Error while loading post 36402 on Elasticsearch (W) 2021-04-17 18:51:46.159604 Error while loading post 35952 on Elasticsearch (W) 2021-04-17 18:51:46.158771 Error while loading post 35945 on Elasticsearch"
  }


/delete_index - parameter: index

<index> is mandatory and is the name of the Elasticsearch index you want to delete.

Does what it says. Returns either a succes or a fail message.
Possible error messages: "elasticsearch_not_connected", "deletion_failed", "index_not_existing", "index_not_specified"

Examples:
- localhost:5000/delete_index?index=4chan_index
- {
    "_status": "ok",
    "deleted_index": "4chan_index"
  }

- localhost:5000/delete_index?index=4chan
- {
    "_status": "error",
    "error_type": "index_not_existing"
  }


