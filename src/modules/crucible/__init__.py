import logging
import json
import urllib
import urllib2
import crucible.rest

class ReviewDataWrapper(object):

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.data)

class ReviewData(object):

    def __init__(self, projectKey, name, description = ''):
        self.projectKey = projectKey
        self.name = name
        self.description = description

    def toCrucibleStruct(self):
        return {
            'reviewData': {
                'projectKey': self.projectKey,
                'name': self.name,
                'description': self.description,
                }
            }

    def __str__(self):
        return str(self.toCrucibleStruct())

class RevisionData(object):

    def __init__(self, source, path, revisions):
        '''
        Example values:
        - source: 'CMX'
        - path: 'trunk/src/.../MyFile.java'
        - revisions: [1, 2, 3,]
        '''
        self.source = source
        self.path = path
        self.revisions = revisions

    def toCrucibleStruct(self):
        return {
            "revisionData" : [
                {
                    "source" : self.source,
                    "path" : self.path,
                    "rev" : self.revisions,
                    }
                ]
            }

class Api(object):
    '''python API for crucible REST services.

    The REST API description is below http://docs.atlassian.com/fisheye-crucible/latest/wadl/crucible.html.

    Some further fisheye commands are documented below http://docs.atlassian.com/fisheye-crucible/latest/wadl/fisheye.html.
    '''

    def __init__(self, apiBaseUrl, urlOpenFactory = rest.UrlOpenFactory(), jsonUrlOpenFactory = rest.JsonUrlOpenFactory()):
        self.apiBaseUrl = apiBaseUrl
        self.urlOpenFactory = urlOpenFactory
        self.jsonUrlOpenFactory = jsonUrlOpenFactory

        self.token = None

    @property
    def _defaultParams(self):
        p = []

        if(not self.token is None):
            p.append(('FEAUTH', self.token))

        return p

    def login(self, user, pw):
        url = self.apiBaseUrl + '/rest-service/auth-v1/login?userName=%s&password=%s' % (urllib.quote(user), urllib.quote(pw))
 
        self.token = self.jsonUrlOpenFactory.urlopen(url)['token']

        return True

    def _buildReviewUrl(self, id, subPath = None):
        baseUrl = self.apiBaseUrl + '/rest-service/reviews-v1'

        if(not id is None):
            baseUrl += '/' + id

        if(not subPath is None):
            baseUrl += '/' + subPath

        return rest.buildUrl(baseUrl, self._defaultParams)

    def getReview(self, id):
        '''
        Example https://my.crucible.server/crucible/rest-service/reviews-v1/CR-1300
        '''
        url = self._buildReviewUrl(id)

        logging.debug('Calling crucible service %s', url)

        return ReviewDataWrapper(self.jsonUrlOpenFactory.urlopen(url))

    def createReview(self, review):
        url = self._buildReviewUrl(None)

        logging.debug('Calling crucible service %s', url)

        response = self.jsonUrlOpenFactory.urlopen(url, data = review.toCrucibleStruct())

        return response['permaId']['id']

    def addReviewer(self, id, userName):
        url = self._buildReviewUrl(id, 'reviewers')

        logging.debug('Calling crucible service %s', url)

        self.urlOpenFactory.urlopen(url, data = userName)

    @rest.dumpHttpError
    def addReviewItemRevision(self, id, revisionData):
        '''
        REST docs: http://docs.atlassian.com/fisheye-crucible/latest/wadl/crucible.html#d2e1354
        '''

        url = self._buildReviewUrl(id, 'reviewitems/revisions')

        response = self.jsonUrlOpenFactory.urlopen(url, data = revisionData.toCrucibleStruct())

    def queryAsRows(self, repositoryName, query, maxReturn = 100):
        '''
        REST API docs: http://docs.atlassian.com/fisheye-crucible/latest/wadl/fisheye.html#d2e212
        '''

        params = list(self._defaultParams)

        params.append(('query', query))
        params.append(('maxReturn', maxReturn))

        url = rest.buildUrl('%s/rest-service-fe/search-v1/queryAsRows/%s' % (self.apiBaseUrl, repositoryName), params)

        return [row['item'] for row in self.jsonUrlOpenFactory.urlopen(url)['row']]

class PrintApi(object):

    def __init__(self, out):
        self.out = out

    def login(self, user, pw):
        pass

    def writeln(self, msg):
        self.out.write('[CRUCIBLE] %s\n' % (msg,))

    def createReview(self, review):
        self.writeln('Created review %s' % (review,))

        return 'CR-XXXX'

    def addReviewer(self, id, userName):
        self.writeln('Added reviewer %s to review %s' % (userName, id))
