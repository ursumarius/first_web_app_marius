import urllib2
import os
import webapp2
import string
import json

#prepare query url for IMDB API
def create_details_url(imdb_id, title= None, year=None):
    url_open = "http://www.omdbapi.com/?i="+imdb_id
    if title:
        title=escape_urlobj(title)
        url_open = url_open+"&t="+title
    if year:
        url_open = url_open+"&y="+year
    return url_open

#outputs json file with details on movie based on an IMDB id
def create_json_details(imdb_id, title=None, year=None):
    url_open = create_details_url(imdb_id, title= None, year=None)
    contents = urllib2.urlopen(url_open)
    contents_str = contents.read()
    return json.loads(contents_str)
