import os
import webapp2
import jinja_util
import string
import json
import urllib2
import datetime
from google.appengine.api import memcache
import time
import logging
import utilities_mu
import models
import re
import time
from google.appengine.ext import db


NewListing = models.MovieListing.NewListing
TorrentLink1Edit = models.MovieListing.TorrentLink1Edit
FollowedChange = models.MovieListing.FollowedChange
FoundTorrentChange = models.MovieListing.FoundTorrentChange
MovieListing = models.MovieListing
Users = models.Users
signup = models.Users.signup
login_check = models.Users.login_check
correct_cookie = models.Users.correct_cookie
make_json_str = utilities_mu.make_json_str
Post_as_dict = utilities_mu.Post_as_dict
render_str = jinja_util.render_str
#single_post = models.single_post

class MovieHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
     
    #def post_wiki(self, post = None, update = False):
    #    key = "top"
    #    posts = memcache.get(key)
    #    old_posts = posts
    #    timeupdated = time.time()
    #    memcache.set("timeupdated", timeupdated)
    #    if not posts or (update):
    #        posts = self.update_cache(post)
    #       
    #    return posts,memcache.get("timeupdated")
    #def Cached_post(self,post_id):
    #    key = post_id
    #    post = memcache.get(key)
    #    if post is None:
    #        post = single_post(post_id)
    #        memcache.set(key, post)
    #        timeupdated = time.time()
    #        memcache.set("timeupdated%s"%post_id, timeupdated)
    #    return post,memcache.get("timeupdated%s"%post_id)
    #
    #def update_cache(self, post):
    #    value = memcache.get("top")
    #    if not value:
    #        value = []
    #    elif len(value) == 10:
    #        value.pop()
    #    if post:
    #        value.insert(0,post)
    #    memcache.set("top",value)
    #    return value

def escape_urlobj(title):
    title = str(title)
    for i in range(len(title)):
        if title[i]==' ' and len(title)>1 and i<len(title)-1:
            print i
            title=title[:i]+"%20"+title[i+1:]
    return title

def create_details_url(imdb_id, title= None, year=None):
    url_open = "http://www.omdbapi.com/?i="+imdb_id
    if title:
        title=escape_urlobj(title)
        url_open = url_open+"&t="+title
    if year:
        url_open = url_open+"&y="+year
    return url_open

def create_json_details(imdb_id, title=None, year=None):
    url_open = create_details_url(imdb_id, title= None, year=None)
    contents = urllib2.urlopen(url_open)
    contents_str = contents.read()
    return json.loads(contents_str)

class HomePage(MovieHandler):
  def get(self):
        q = models.MovieListing.gql("Where Followed= :one", one=1)
        p = list(q)
        #logging.error("list(q)=%s"%p)
        self.render("front.html", listing = p)
        
        
class MoviePage(MovieHandler):
    def get(self, movie_id):
       
        self.write("MoviePage")
        
class AddMovie(MovieHandler):
    def get(self, IMDB_link):
        #check if valid immediately as in post
        #check if already exists by title and imdblink
        #if IMDB_link:
        
        IMDB_link = str(IMDB_link)  
        self.render("AddMovie.html", IMDB_link = IMDB_link)
        
    def post(self, IMDB_link):
        IMDB_entered = str(self.request.get("IMDB_link"))
        id_index = IMDB_entered.find("title/")+6
        imdb_id= IMDB_entered[id_index:id_index+9]
        logging.error("id=%s"%imdb_id)
        j = create_json_details(imdb_id)
        Title = j["Title"]
        IMDB_link = "http://www.imdb.com/title/"+j["imdbID"]
        Poster_link = j["Poster"]
        Creators = j["Director"]+", "+j["Writer"]
        Actors = j["Actors"]
        ReleaseDate = j["Released"]
        #do validation according to API, save details in DB
        
        if not NewListing(Title = Title, IMDB_link = IMDB_link,
                          Poster_link = Poster_link, Creators = Creators, Actors = Actors, ReleaseDate = ReleaseDate):
            self.render("AddMovie.html", error_IMDB_link = "This is not a link")
        else:
            self.redirect("/Homepage")
        
        
class RemoveMovie(MovieHandler):
    def get(self, movie_id):
        if movie_id:
            if (FollowedChange(int(movie_id), 0)):
                logging.error("Changed")
                time.sleep(0.5) #needed for nice db time lag, possibly with cache not needed.
                self.redirect("/Homepage")
            else:
                logging.error("Couldnt change")
                self.write('<div style="font-family: verdana;">Wrong link</div>')
        else:
            self.write('<div style="font-family: verdana;">Wrong link</div>')
        #if (FoundTorrentChange(int(movie_id), 1)):
        #    logging.error("Changed torrent")
        #else:
        #    logging.error("Couldnt change torrent")
        #
        #if (TorrentLink1Edit(int(movie_id), "www.asd.com")):
        #    logging.error("Changed torrentlink")
        #else:
        #    logging.error("Couldnt change torrentlink")

class DetailsMovie(MovieHandler):
    def get(self, movie_name):
        #problem with redirecting titles with space.
        logging.error("movie_name=~%s~'"%movie_name)
        q = models.MovieListing.gql("Where Title= :title", title=str(movie_name))
        p = list(q)
        #logging.error("p = %s"%p)
        if p:
            self.render("Movie_listing_details.html", listing = p[0])
        else:
            self.write("Title Not Found")
   
PAGE_RE = r'((?:[\sa-zA-Z0-9_-]+/?)*)?'
app = webapp2.WSGIApplication([('/Movie/?%s?' % PAGE_RE, MoviePage),
                                ('/AddMovie/?%s?' % PAGE_RE, AddMovie),
                                ('/RemoveMovie/?%s?' % PAGE_RE, RemoveMovie),
                                ('/Details/?%s?' % PAGE_RE, DetailsMovie),
                                ('/Homepage', HomePage),
                               ],
                              debug=True)