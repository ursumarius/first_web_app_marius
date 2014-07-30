#!/usr/bin/env python

import re
import utilities_mu
import jinja_util
from collections import namedtuple
from google.appengine.ext import db
import logging
import datetime

render_str = jinja_util.render_str
valid_pw = utilities_mu.valid_pw
make_pw_hash = utilities_mu.make_pw_hash

class Series(db.Model):
    Title = db.StringProperty(required = True)
    ReleaseDate = db.DateProperty(required = False)
    Created = db.DateTimeProperty(auto_now_add = True)
    Last_modified = db.DateTimeProperty(auto_now = True)
    @classmethod
    def NewSeries(cls, Title, ReleaseDate):
        if not ReleaseDate:
            ReleaseDate = datetime.date.today()
        q = Series.gql("Where Title= :title", title=Title)
        p = list(q)
        if not p:
            q = Series(Title = Title, ReleaseDate = ReleaseDate)
            q.put() #assume successful entry if good values
            return True
        return False
    

class MovieListing(db.Model):
    Title = db.StringProperty(required = True)
    IMDB_link = db.LinkProperty(required = True)
    Followed = db.IntegerProperty(required = True)
    Poster_link = db.LinkProperty(required = False)
    
    Creators = db.StringProperty(required = False)
    Actors = db.StringProperty(required = False)
    
    
    FoundTorrent = db.IntegerProperty(required = False)
    TorrentLink1 = db.StringProperty(required = False)
    Last_found_check = db.DateProperty(required = True)
    
    ReleaseDate = db.DateProperty(required = False)
    Created = db.DateTimeProperty(auto_now_add = True)
    Last_modified = db.DateTimeProperty(auto_now = True)
    
    @classmethod
    def FollowedChange(cls, movie_id, truth):
        db_key = db.Key.from_path('MovieListing', movie_id)
        q = db.get(db_key)
        if q and (truth == 1 or truth == 0 ):
            
            q.Followed = int(truth)
            q.put()
            #logging.error("Followed in db = %s"%str(q.Followed))
            return True
        else:
            return False
        
    @classmethod
    def FoundTorrentChange(cls, title, url, truth):
        q = MovieListing.gql("Where Title= :title", title=title)
        p = list(q)
        if p[0]:
            p[0].FoundTorrent = truth
            p[0].TorrentLink1 = url
            p[0].Last_found_check = datetime.date.today()
            p[0].put()
            #logging.error("Followed in db = %s"%str(q.Followed))
            return True
        else:
            return False
    @classmethod   
    def TorrentLink1Edit(cls, movie_id, newlink):
        db_key = db.Key.from_path('MovieListing', movie_id)
        q = db.get(db_key)
        if q and newlink:
            q.TorrentLink1 = str(newlink)
            q.put()
            #logging.error("Followed in db = %s"%str(q.Followed))
            return True
        else:
            return False
        
    @classmethod
    def NewListing(cls, Title, IMDB_link, Poster_link, ReleaseDate, Followed = 1, Creators = "", Actors = "",
                   FoundTorrent = 0, TorrentLink1 = "", Last_found_check = datetime.date.today()):
        #assume all data is valid (e.g. link is link) -- how to handler errors while entering in DB?
        
        q = MovieListing.gql("Where Title= :title", title=Title)
        p = list(q)
        if not p:
            q = MovieListing(Title = Title, IMDB_link = IMDB_link, Poster_link = Poster_link, Followed = Followed,
                     Creators = Creators, Actors = Actors, FoundTorrent = FoundTorrent, 
                     TorrentLink1 = str(TorrentLink1), Last_found_check = Last_found_check,
                     ReleaseDate = ReleaseDate)
            q.put() #assume successful entry if good values
            return True
        return False
       
        
        

    def render(self):
        return render_str("Movie_listing.html", listing = self)


   
def single_listing( listing_id):
    db_key = db.Key.from_path('MovieListing', int(listing_id) )
    return db.get(db_key)    
           
           
           
           
class System_tools(db.Model):
    name = db.StringProperty(required = True)
    value = db.StringProperty(required = False)
    Created = db.DateTimeProperty(auto_now_add = True)
    Last_modified = db.DateTimeProperty(auto_now = True)
    
    
    
class Users(db.Model):
    username = db.StringProperty(required = True)
    password_hash = db.StringProperty(required = True)
    email = db.StringProperty()
    #pass hash = db.StringProperty(required = True)
    
  
    
#sign stuff 
    @classmethod
    def correct_password(self, username_in,password_in):
        q = Users.gql(("WHERE username = :user"), user = str(username_in))
        password_hash_db = ""
        for entry in q:
            password_hash_db = str(entry.password_hash)
            
        if valid_pw(password_in, password_hash_db):
            return password_hash_db
        
    
    @classmethod
    def free_username(cls, username):
        q = cls.gql(("WHERE username = :user"), user = str(username))
        for entry in q:
            return False
        return True
    @classmethod
    def correct_cookie(cls,cookie_value):
        try:
            CookieUser = cookie_value.split("-")[0]
            CookieHash = cookie_value.split("-")[1]
        except:
            return False,""
        q = cls.gql(("WHERE username = :user"), user = str(CookieUser))
        password_hash_db = ""
        for entry in q:
            password_hash_db = str(entry.password_hash)
            
        return CookieHash == password_hash_db,CookieUser
    @classmethod
    def signup(cls, username, password, verify, email):
        have_error = False
        params = {}
        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True
        
        if (cls.free_username(username) == False):
            params['error_username'] = "Username already taken"
            have_error = True
            
        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True
        password_hash = make_pw_hash(password)
        return have_error, params, password_hash
    @classmethod
    def login_check(cls, username, password):
        have_error = False
        params = {}
        if cls.free_username(username)==True:
            have_error = True
            params['error_username'] = "That's not a valid username."
        cookie_hash = cls.correct_password(username,password)
        if not cookie_hash:
            params['error_password'] = "Wrong password."
            have_error = True
        
        return have_error, params,cookie_hash



USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
        return username and USER_RE.match(username) 
    
PASS_RE = re.compile(r"^.{3,20}$")

def valid_password(password):
        return password and PASS_RE.match(password)
    
EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
 
def valid_email(email):
        return not email or EMAIL_RE.match(email)
    



 

    


    
