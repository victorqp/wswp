import os
import re
import urllib.parse as urlparse
import pickle
import zlib
from datetime import datetime, timedelta

class DiskCache:
    def __init__(self, cache_dir='cache', expires=timedelta(days=30), compress=False):
        self.cache_dir = cache_dir
        self.expires = expires
        self.compress = compress

    def url_to_path(self, url):
        """Create file system path for this URL
        """
        components = urlparse.urlsplit(url)
        # append index.html to empty paths
        path = components.path
        if not path:
            path = '/index.html'
        elif path.endswith('/'):
            path += 'index.html'
        filename = components.netloc + path + components.query
        # replace invalid characters
        filename = re.sub('[^/0-9a-zA-Z\-.,:_]', '_', filename)
        # restrict max number of characters
        filename = '/'.join(segment[:255] for segment in filename.split('/'))
        full_path = os.path.join(self.cache_dir, filename)
        if os.path.exists(full_path) and os.path.isdir(full_path):
            # if the same name already exists as a dir, add index.html in the end
            full_path += '/index.html'
        return full_path

    def __getitem__(self, url):
        path = self.url_to_path(url)
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, 'rb') as fp:
                data = fp.read()
                if self.compress:
                    data = zlib.decompress(data)
                result, timestamp = pickle.loads(data)
                if self.has_expired(timestamp):
                    raise KeyError(url + ' has expired')
                return result
        else:
            raise KeyError(url + ' does not exist')

    def __setitem__(self, url, result):
        path = self.url_to_path(url)
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        timestamp = datetime.utcnow()
        data = pickle.dumps((result, timestamp))
        if self.compress:
            data = zlib.compress(data)
        
        with open(path, 'wb') as fp:
            fp.write(data)

    def has_expired(self, timestamp):
        return datetime.utcnow() > timestamp + self.expires