import urllib
import urllib2
import json
import functools

def buildUrl(url, params = []):
    if(len(params) > 0):
        if url.find('?') < 0:
            # no '?' in the url
            url += '?'
            first = True
        else:
            first = False
        for key, value in params:
            if(first):
                first = False
            else:
                url += '&'

            url += urllib.quote(key) + '=' + urllib.quote(str(value))

    return url

class UrlOpenFactory(object):

    @property
    def httpParams(self):
        # we have to send anyting... so why not json?
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            }

    def createRequest(self, url, data = None):
        return urllib2.Request(url, data, self.httpParams)

    def urlopen(self, url, data = None):
        return urllib2.urlopen(self.createRequest(url, data)).read()

class JsonUrlOpenFactory(UrlOpenFactory):

    @property
    def httpParams(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            }

    def urlopen(self, url, data = None):
        return json.loads(super(JsonUrlOpenFactory, self).urlopen(url, json.dumps(data) if not data is None else None))

def dumpHttpError(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except urllib2.HTTPError as e:
            with open('httpError', 'w') as out:
                out.write('\n'.join(e.read().split('\\n')))

            raise e

    return wrapper
