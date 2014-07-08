import os
import webapp2
import jinja_util
import string
import json
import urllib2
import datetime
from google.appengine.api import memcache
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
     
 
#stuff for IMDB API################

def escape_urlobj(title):
    title = str(title)
    for i in range(len(title)):
        if title[i]==' ' and len(title)>1 and i<len(title):
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

# stuff for IMDB API END##################################
# stuff for TPB API##################################

def inspect_tpb(title, year, diff_proxy = None):
    def create_titles(title):
        title = str(title)
        title_p = title
        for i in range(len(title)):
            if title[i]==' ' and len(title)>1 and i<len(title):
                print i
                title_p=title_p[:i]+"."+title_p[i+1:]
        return [title, title_p]
    
    def find_match(found, title, year):
        titles = create_titles(title)
        for title in titles:
            PAGE_RE = r'(?:'+title+r'( |.)?(\(|\[)?'+year+r'(\)|\])?)' 
            
            matchObj = re.search( PAGE_RE,found, re.M|re.I)
            if matchObj:
               return True
        return None
    
    def escape_urlobj(title):
        title = str(title)
        for i in range(len(title)):
            if title[i]==' ' and len(title)>1 and i<len(title):
                print i
                title=title[:i]+"%20"+title[i+1:]
        return title
    
    def compute_length_match(title):
        count = 0
        for element in title:
            if element == " ":
                count+=1
        return count+len(title)+6
    def create_search_url(title, year, proxy):
        title = str(title)
        search = escape_urlobj(title+" "+year)
        return proxy+search+"/0/99/200"
    
    def pick_index(title, length_proxies):
        if len(title)>4:
            return (ord(title[-1]) + ord(title[-2]) + ord(title[-3]))%length_proxies
        else:
            return 0

   
    proxies = ["http://pirateproxy.in", "http://thebootlegbay.com", "http://thepiratebay.mg", "http://myproxypirate.com"]
    proxy_index = pick_index(title, len(proxies))
    if (diff_proxy is not None) and (diff_proxy == proxy_index):
        proxy_index = (proxy_index + 1) % (len(proxies))
    
    proxy = proxies[proxy_index]
    proxy_search = proxy+"/search/"
    search_url = create_search_url(title, year, proxy_search)
    try:
        t = urllib2.urlopen(search_url)
        t = t.read()
        index = 9000
        m = compute_length_match(title)
        hit = 0
        for i in range(3):
            index = t.find("Details for",index)
            if index == -1:
                return None
            index2 = t.find('">', index)
            title_found = t[index+12: index2]
            index = index + 3* 1100
            if not (re.search( r'TS', title_found, re.M) or re.search( r'trailer', title_found, re.M|re.I)):
                if hit == 1 and find_match(title_found, title, year):
                    return search_url
                hit = 1
        return None
    except:
        if diff_proxy is not None:
            return "Error"
        else:
            return inspect_tpb(title, year, proxy_index)

def update_torrent(movie_name):
    
    q = models.MovieListing.gql("Where Title= :title", title=str(movie_name))
    p = list(q)
    obj_movie = p[0]
    findings = inspect_tpb(obj_movie.Title, obj_movie.ReleaseDate.strftime("%Y"))
    if findings != "Error":
        truth = 0
        if findings:
            truth = 1
        FoundTorrentChange(movie_name, findings, truth)
        return True
    return False
#stuff for TPB API END##################################

class HomePage(MovieHandler):
    def get(self):
        q = models.MovieListing.gql("Where Followed= :one Order by FoundTorrent desc", one=1)
        p = list(q)
        #logging.error("list(q)=%s"%p)
        self.render("front.html", listing = p)
        
    def post(self):
        #self.write("Updating")
        q = models.MovieListing.gql("Where Followed= :one", one=1)
        p = list(q)
        number_of_titles = len(p)
        for listing in p:
            if listing.FoundTorrent == 0:
                update_torrent(listing.Title)
                logging.error("One done")
                #self.write("\nDone%s / %s"%(p.index(listing), number_of_titles))
                time.sleep(2)
        
        
      
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
        #logging.error("id=%s"%imdb_id)
        #exception handling here, what if not found?
        try:
            j = create_json_details(imdb_id)
            Title = j["Title"]
            IMDB_link = "http://www.imdb.com/title/"+j["imdbID"]
            Poster_link = j["Poster"]
            Creators = j["Director"]+", "+j["Writer"]
            Actors = j["Actors"]
            ReleaseDate = datetime.datetime.strptime(j["Released"], "%d %b %Y").date()
        #do validation according to API, save details in DB
            
            if not NewListing(Title = Title, IMDB_link = IMDB_link,
                              Poster_link = Poster_link, Creators = Creators,
                              Actors = Actors, ReleaseDate = ReleaseDate):
                self.render("AddMovie.html", error_IMDB_link = "Error with DB")
            else:
                self.redirect("/Homepage")
        except:
            self.render("AddMovie.html", error_IMDB_link = "Error with IMDB API")
            
        
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
    def post(self, movie_name):
        
        update_torrent(movie_name) #possiblity for some nice js message popup
        time.sleep(1)
        self.redirect("/Details/%s"%movie_name)   
        
PAGE_RE = r'((?:[\s\.\:\!\'a-zA-Z0-9_-]+/?)*)?'
app = webapp2.WSGIApplication([('/AddMovie/?%s?' % PAGE_RE, AddMovie),
                                ('/RemoveMovie/?%s?' % PAGE_RE, RemoveMovie),
                                ('/Details/?%s?' % PAGE_RE, DetailsMovie),
                                ('/Homepage', HomePage),
                               ],
                              debug=True)