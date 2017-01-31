from secrets import CONSUMER_KEY, CONSUMER_SECRET, TOKEN, TOKEN_SECRET
API_HOST = 'api.yelp.com'
DEFAULT_TERM = 'Thai'
DEFAULT_LOCATION = 'Seattle, WA'
SEARCH_LIMIT = 5
SEARCH_PATH = '/v2/search/'
BUSINESS_PATH = '/v2/business/'

import base64
import cgi
import Cookie
import email.utils
import hashlib
import hmac
import logging
import time

import json
import jinja2
import webapp2, urllib, urllib2, os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)+"/lib/python2.7/site-packages"))
logging.info(sys.path)
import oauth2

JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

## THE NEXT SEVERAL FUNCTIONS ARE FROM https://github.com/Yelp/yelp-api/
def request(host, path, url_params=None):
    """Prepares OAuth authentication and sends the request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        urllib2.HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = 'http://{0}{1}?'.format(host, path)

    consumer = oauth2.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
    oauth_request = oauth2.Request(method="GET", url=url, parameters=url_params)

    oauth_request.update(
        {
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': oauth2.generate_timestamp(),
            'oauth_token': TOKEN,
            'oauth_consumer_key': CONSUMER_KEY
        }
    )
    token = oauth2.Token(TOKEN, TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
    signed_url = oauth_request.to_url()
    
    print 'Querying {0} ...'.format(url)

    conn = urllib2.urlopen(signed_url, None)
    try:
        response = json.loads(conn.read())
    finally:
        conn.close()

    return response

def search(term, location):
    """Query the Search API by a search term and location.
    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.
    Returns:
        dict: The JSON response from the request.
    """
    
    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT
    }
    return request(API_HOST, SEARCH_PATH, url_params=url_params)

def get_business(business_id):
    """Query the Business API by a business ID.
    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path)

def query_api(term, location):
    """Queries the API by the input values from the user.
    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
    """
    response = search(term, location)

    businesses = response.get('businesses')

    if not businesses:
        print 'No businesses for {0} in {1} found.'.format(term, location)
        return

    business_id = businesses[0]['id']
    
    print '{0} businesses found, querying business info for the top result "{1}" ...'.format(
        len(businesses),
        business_id
    )
    
    response=[]
    for biz in range(len(businesses)):
        response.append(get_business(businesses[biz]['id']))
    #response = get_business(business_id)
    return response

class mainHandler(webapp2.RequestHandler):
    def get(self):
        logging.info("In MainHandler")
        template_values={}
        template = JINJA_ENVIRONMENT.get_template('greetform.html')
        self.response.write(template.render(template_values))
    

class greetResponseHandler(webapp2.RequestHandler):
    def post(self):

        vals = {}
        vals['page_title']="Yelp Search Results"
        term = self.request.get('username')
        go = self.request.get('gobtn') 
        logging.info(term)
        logging.info(go)
        if term:
            # if form filled in, greet them using this data
            
            resp = query_api(term,"Seattle, WA") 
            #resp2 = pretty(resp)
            #resdata = json.load(resp)#is this line necessary?
           
            vals['jsonData']= resp      
            template = JINJA_ENVIRONMENT.get_template('greetresponse.html')
            self.response.write(template.render(vals))
            
        else:
            #if not, then show the form again with a correction to the user
            vals['prompt'] = "Please enter a tag"
            template = JINJA_ENVIRONMENT.get_template('greetform.html')
            self.response.write(template.render(vals)) 
            
                 
application = webapp2.WSGIApplication([('/gresponse',greetResponseHandler),('/.*',mainHandler)], debug=True)
