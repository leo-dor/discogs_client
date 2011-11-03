import requests
import json
import oauth2
import urllib
import urlparse

from discogs_client import models, BASE_URL
from discogs_client.exceptions import ConfigurationError, HTTPError

REQUEST_TOKEN_URL = BASE_URL + '/oauth/request_token'
AUTHORIZE_URL = 'http://appdev1.prod.discogs.com:8085/oauth/authorize'
ACCESS_TOKEN_URL = BASE_URL + '/oauth/access_token'

class Client(object):
    def __init__(self, user_agent, consumer_key=None, consumer_secret=None, access_token=None, access_secret=None):
        self.user_agent = user_agent
        self.verbose = False
        self.authenticated = False

        self._consumer = None
        self._oauth_client = None
        self._token = None

        if consumer_key and consumer_secret:
            self._consumer = oauth2.Consumer(consumer_key, consumer_secret)

            if access_token and access_secret:
                self._token = oauth2.Token(access_token, access_secret)
                self.authenticated = True

            self._oauth_client = oauth2.Client(self._consumer, self._token)

    def get_authorize_url(self, callback_url=None):
        # Forget existing tokens
        self._oauth_client = oauth2.Client(self._consumer)

        params = {}
        if callback_url:
            params['oauth_callback'] = callback_url
        postdata = urllib.urlencode(params)

        resp, content = self._oauth_client.request(REQUEST_TOKEN_URL, 'POST', body=postdata)
        if resp['status'] != '200':
            raise HTTPError('Invalid response from request token URL.', int(resp['status']))
        self._token = dict(urlparse.parse_qsl(content))

        params = {'oauth_token': self._token['oauth_token']}
        query_string = urllib.urlencode(params)

        return '?'.join((AUTHORIZE_URL, query_string))

    def get_access_token(self, verifier):
        token = oauth2.Token(
            self._token['oauth_token'],
            self._token['oauth_token_secret'],
        )
        token.set_verifier(verifier)
        self._oauth_client = oauth2.Client(self._consumer, token)

        resp, content = self._oauth_client.request(ACCESS_TOKEN_URL, 'POST')
        self._token = dict(urlparse.parse_qsl(content))

        token = oauth2.Token(
            self._token['oauth_token'],
            self._token['oauth_token_secret'],
        )
        self._oauth_client = oauth2.Client(self._consumer, token)
        self.authenticated = True

        return self._token['oauth_token'], self._token['oauth_token_secret']

    def _check_user_agent(self):
        if self.user_agent:
            self._headers['user-agent'] = user_agent
        else:
            raise ConfigurationError('Invalid or no User-Agent set.')

    def _request(self, method, url, data=None):
        if self.verbose:
            print ' '.join((method, url))

        if self.authenticated:
            if data:
                body = urllib.urlencode(data)
                resp, content = self._oauth_client.request(url, method, body)
            else:
                resp, content = self._oauth_client.request(url, method)
            status_code = int(resp['status'])
        else:
            response = requests.request(method, url, data=data)
            content = response.content
            status_code = response.status_code

        if status_code == 204:
            return None

        body = json.loads(content)

        if 200 <= status_code < 300:
            return body
        else:
            raise HTTPError(body['message'], status_code)

    def _get(self, url):
        return self._request('GET', url)

    def _delete(self, url):
        return self._request('DELETE', url)

    def _post(self, url, data):
        return self._request('POST', url, data)

    def _patch(self, url, data):
        return self._request('PATCH', url, data)

    def _put(self, url, data):
        return self._request('PUT', url, data)

    def search(self, *query, **fields):
        if query:
            fields['q'] = ' '.join(query)

        return models.MixedObjectList(
            self,
            _update_qs(BASE_URL + '/database/search', fields),
            'results'
        )

    def artist(self, id):
        return models.Artist(self, {'id': id})

    def release(self, id):
        return models.Release(self, {'id': id})

    def master(self, id):
        return models.Master(self, {'id': id})

    def label(self, id):
        return models.Label(self, {'id': id})

    def user(self, username):
        return models.User(self, {'username': username})

    def listing(self, id):
        return models.Listing(self, {'id': id})

    def identity(self):
        resp = self._get(BASE_URL + '/oauth/identity')
        return models.User(self, resp)

    def fee_for(self, price, currency='USD'):
        resp = self._get(BASE_URL + '/marketplace/fee/%f/%s' % (float(price), currency))
        return models.Price(self, {'value': resp['value'], 'currency': resp['currency']})

