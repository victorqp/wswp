import urllib.request as urlreq
import urllib.error as urlerr
import urllib.parse as urlparse
import urllib.robotparser as urlrp
import datetime
import time
import re
import socket
import http.client

class Downloader(object):
    def __init__(self, delay=5,
        user_agent='wswp', proxies=None,
        num_retries=1, cache=None, timeout=60):
        socket.setdefaulttimeout(timeout)
        self.throttle = Throttle(delay)
        self.user_agent = user_agent
        self.proxies = proxies
        self.num_retries = num_retries
        self.cache = cache

    def __call__(self, url):
        result = None
        if self.cache:
            try:
                result = self.cache[url]
            except KeyError:
                pass
            else:
                if self.num_retries > 0 and result['code'] != None and \
                    500 <= result['code'] < 600:
                    # server error so ignore result from cache 
                    # and re-downlad
                    result = None
        if result is None:
            # result was not downloaded from cache so still
            # need to download
            self.throttle.wait(url)
            proxy = random.choice(self.proxies) if self.proxies else None
            headers = {'User-agent': self.user_agent}
            result = self.download(url, headers, proxy, self.num_retries)
            if self.cache:
                self.cache[url] = result

        return result['html']

    def download(self, url, headers, proxy, num_retries, data = None):
        print('Downloading: ', url)
        request = urlreq.Request(url, headers=headers)
        opener = urlreq.build_opener()
    
        if proxy:
            proxy_params = {urlparse.urlparse(url).scheme: proxy}
            opener.add_handler(urlreq.ProxyHandler(proxy_params))
        try:
            #html = urlreq.urlopen(request).read()
            response = opener.open(request)
            try:
                html = response.read()
            except http.client.IncompleteRead as e:
                html = e.partial
            code = response.code
        except urlerr.URLError as e:
            print('Download error: ', e.reason)
            html = None
            code = None
            if hasattr(e, 'code'):
                code = e.code
                if num_retries > 0 and 500 <= e.code < 600:
                    return download(url, headers, proxy, self.num_retries-1)
                else:
                    pass

        return {'html': html, 'code': code}

class Throttle:
    """add delay between downloads to the same domain"""
    def __init__(self, delay):
        self.delay = delay
        self.domains = {}
        
    def wait(self, url):
        domain = urlparse.urlparse(url).netloc
        last_accessed = self.domains.get(domain)
        
        if self.delay > 0 and last_accessed is not None:
            sleep_secs = self.delay - (datetime.datetime.now() - 
                          last_accessed).seconds
            if sleep_secs > 0:
                time.sleep(sleep_secs)
        self.domains[domain] = datetime.datetime.now()

def download(url, user_agent='wswp', proxy=None, num_retries=2):
    print('Downloading: ', url)
    headers = {'User-agent': user_agent}
    request = urlreq.Request(url, headers=headers)
    opener = urlreq.build_opener()
    
    if proxy:
        proxy_params = {urlparse.urlparse(url).scheme: proxy}
        opener.add_handler(urlreq.ProxyHandler(proxy_params))
    try:
        #html = urlreq.urlopen(request).read()
        html = opener.open(request).read()
    except urlerr.URLError as e:
        print('Download error: ', e.reason)
        html = None
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                return download(url, user_agent, proxy, num_retries-1)
    return html

def get_links(html):
    # a regular expression to extract all links from the webpage
    webpage_regex = re.compile('<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
    # list of all links from the webpage
    return webpage_regex.findall(html)

def normalize(seed_url, link):
    """Normalize this URL by removing hash and adding domain
    """
    link, _ = urlparse.urldefrag(link) # remove hash to avoid duplicates
    return urlparse.urljoin(seed_url, link)