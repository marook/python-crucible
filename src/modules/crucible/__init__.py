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

    def getReviews(self, filter):
        '''
        Get a filtered list of reviews.
        For filter use e.g. "allOpenReviews", "open", ...

        Example https://my.crucible.server/crucible/rest-service/reviews-v1/filter/{filter}
        '''
        url = self._buildReviewUrl('filter/' + filter)

        logging.debug('Calling crucible service %s', url)

        return self.jsonUrlOpenFactory.urlopen(url)['reviewData']

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

    def getReviewItems(self, rid):
        '''
        id: review id, e.g. "CR-362"
        '''
        url = self._buildReviewUrl(rid, 'reviewitems')

        logging.debug('Calling crucible service %s', url)

        response = self.jsonUrlOpenFactory.urlopen(url)
        return response['reviewItem']

    def getReviewItemComments(self, rid, riId, render=False):
        '''
        rid:    review id
        riId:   review item id
        render: indicate whether to render the wiki text in the returned
                comments. If set to "true", the comments will contain a
                <messageAsHtml> element containing the wiki rendered html
        '''
        if render:
            render = '?render=true'
        else:
            render = ''
        url = self._buildReviewUrl(rid, 'reviewitems/%s/comments%s' % (riId, render))

        logging.debug('Calling crucible service %s', url)

        response = self.jsonUrlOpenFactory.urlopen(url)
        return response['comments']

    #def addReviewItemComment(self, rid, riId, message, fromLineRange, toLineRange, draft=False, deleted=False, defectRaised=false, defectApproved=false, readStatus="UNREAD", ):
    def addReviewItemComment(self, rid, riId, message, toLineRange):
        '''
        rid:         review id
        riId:        review item id
        message:     message of the comment with Wiki syntax
        toLineRange: either one line (as integer or string) or a range as string (e.g., '5-12")

        returns: a dict of the newly created comment as shown at https://docs.atlassian.com/fisheye-crucible/latest/wadl/crucible.html#rest-service:reviews-v1:id:reviewitems:riId:comments
        '''
        url = self._buildReviewUrl(rid, 'reviewitems/%s/comments' % (riId))

        logging.debug('Calling crucible service %s', url)

        data = {
            "message": message,
            "toLineRange": toLineRange
        }
        # TODO: add more fields as optional parameters of this function and if
        # set append to this dict

        response = self.jsonUrlOpenFactory.urlopen(url, data = data)
        return response

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
