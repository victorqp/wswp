import urllib.request as urlreq
import urllib.error as urlerr
import urllib.parse as urlparse
import urllib.robotparser as urlrp
import re
import datetime
import time
import sys
sys.path.append('../')
from common.utils import *
from common.db_cache import *
from common.process_crawler import *
import csv
from zipfile import ZipFile
from io import BytesIO, TextIOWrapper

class AlexaCallback():
    def __init__(self, max_urls=50):
        self.max_urls = max_urls;
        self.seed_url = 'http://s3.amazonaws.com/alexa-static/top-1m.csv.zip'
        
    def __call__(self, url, html):
        if url == self.seed_url:
            urls = []
            with ZipFile(BytesIO(html)) as zf:
                csv_filename = zf.namelist()[0]
                for _, website in csv.reader(TextIOWrapper(zf.open(csv_filename))):
                    urls.append('http://' + website)
                    if len(urls) == self.max_urls:
                        break
        
            return urls


if __name__ == '__main__':
    scrape_callback = AlexaCallback()
    start = time.time()
    process_crawler(scrape_callback.seed_url, scrape_callback=scrape_callback, max_threads=10, timeout=10)
    end = time.time()
    print("process download: %.2f seconds" % (end-start))