import os



import webapp2
import jinja_util



import string
import json
import datetime
from google.appengine.api import memcache
import time
import logging
import utilities_mu
import models
import re
import time
from google.appengine.ext import db

Post = models.Post
Users = models.Users
signup = models.Users.signup
login_check = models.Users.login_check
correct_cookie = models.Users.correct_cookie
make_json_str = utilities_mu.make_json_str
Post_as_dict = utilities_mu.Post_as_dict
render_str = jinja_util.render_str
single_post = models.single_post

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


class HomePage(MovieHandler):
  def get(self):
        self.write("HomePage")
        
        
class MoviePage(MovieHandler):
    def get(self, movie_id):
       
        self.write("MoviePage")
        
class AddMovie(MovieHandler):
    def get(self, IMDB_link):
        #check if valid immediately as in post
        #if IMDB_link:
        #    IMDB_link = str(IMDB_link)
        IMDB_link = str(IMDB_link)    
        self.render("AddMovie.html", IMDB_link = IMDB_link)
    def post(self, IMDB_link):
        IMDB_entered = self.request.get("IMDB_link")
        #do validation according to API, save details in DB
        
class RemoveMovie(MovieHandler):
    def get(self, movie_id):
       
        self.write("RemoveMovie")
        
    #def post(self, path_ext):
    #    login = self.request.cookies.get("login", "error no cookie")
    #    loggedin,user = correct_cookie(login)
    #    if loggedin:
    #        
    #        q = Post.gql(("WHERE subject = :subject"), subject = str(path_ext))
    #        q = q.get()
    #        q.content = str(self.request.get('content'))
    #        q.put()
    #        time.sleep(0.1)
    #        self.redirect("/wiki/%s"%path_ext)
    #    else:
    #        self.redirect("/wiki/login")
    #    

PAGE_RE = r'((?:[a-zA-Z0-9_-]+/?)*)?'
app = webapp2.WSGIApplication([('/Movie/?%s?' % PAGE_RE, MoviePage),
                                ('/AddMovie/?%s?' % PAGE_RE, AddMovie),
                                ('/RemoveMovie/?%s?' % PAGE_RE, RemoveMovie),
                                ('/Homepage', HomePage),
                               ],
                              debug=True)