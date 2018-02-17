import urllib.request as urlreq
import urllib.error as urlerr
import urllib.parse as urlparse
import urllib.robotparser as urlrp
import re
from . import utils

def link_crawler(seed_url, link_regex=None, delay=3, max_depth=-1, max_urls=-1, user_agent='wswp', proxies=None, num_retries=1, scrape_callback=None, cache=None, ignore_robots=False):
    crawl_queue = [seed_url]
    seen = {seed_url:0}
    rp = urlrp.RobotFileParser()
    rp.set_url(urlparse.urljoin(seed_url, '/robots.txt'))
    rp.read()
    D = utils.Downloader(delay=delay, user_agent=user_agent,
                  proxies=proxies, num_retries=num_retries, cache=cache)
    while crawl_queue:
        url = crawl_queue.pop()
        depth = seen[url]
        if ignore_robots or rp.can_fetch(user_agent, url):
            html = D(url)
            links = []
            if scrape_callback:
                links.extend(scrape_callback(url, html) or [])
            if depth != max_depth:
                if link_regex:
                    # filter for links matching our regular expression
                    links.extend(link for link in utils.get_links(html.decode()) if re.search(link_regex, link))
                for link in links:
                    # skip all login pages
                    if re.search('login|register', link):
                        continue
                    # form absolute link
                    link = urlparse.urljoin(seed_url, link)
                    # check if this link is already seen
                    if link not in seen:
                        seen[link] = depth + 1
                        crawl_queue.append(link)
        else:
            print('blocked by robots.txt, ', url)
                    
    return seen