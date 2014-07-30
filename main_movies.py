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

Series = models.Series
NewSeries = models.Series.NewSeries
NewListing = models.MovieListing.NewListing
TorrentLink1Edit = models.MovieListing.TorrentLink1Edit
FollowedChange = models.MovieListing.FollowedChange
FoundTorrentChange = models.MovieListing.FoundTorrentChange
MovieListing = models.MovieListing
System_tools = models.System_tools
Users = models.Users
signup = models.Users.signup
login_check = models.Users.login_check
correct_cookie = models.Users.correct_cookie
make_json_str = utilities_mu.make_json_str
render_str = jinja_util.render_str
#single_post = models.single_post

class MovieHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        
        q = System_tools.gql("Where name= :title", title="Updatekeep")
        p = list(q)
        if p:
            kw['system_tools_object'] = p[0]
            logging.error(kw)
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

#def title_make_valid(title):
#    title_in = title
#    PAGE_RE = r'((?:[\s\.\:\!\'\&a-zA-Z0-9_-]+/?)*)?'
#    title_out = ""
#    for element in title_in:
#        if not re.match( PAGE_RE,element, re.M|re.I):
#            element = "."
#        title_out = title_out+element
#    return title_out

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
            
            matchObj = re.match( PAGE_RE,found, re.M|re.I)
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
            if not (re.search( r'TS', title_found, re.M)
                    or re.search( r'trailer', title_found, re.M|re.I)
                    or re.search( r' cam ', title_found, re.M|re.I)
                    or re.search( r' camrip ', title_found, re.M|re.I)):
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

class Blank(MovieHandler):
    def get(self):
        self.redirect("/Homepage")
        
class HomePage(MovieHandler):
    def get(self, ext):
        def create_dict_Movielisting(q):
            dict_out = {"Title": str(q.Title),
                        "IMDB_link":str(q.IMDB_link),
                        "Followed": str(q.Followed),
                        "Poster_link": str(q.Poster_link),
                        "Creators": q.Creators,
                        "Actors": (q.Actors),
                        "FoundTorrent": str(q.FoundTorrent),
                        "TorrentLink1": str(q.TorrentLink1),
                        "Last_found_check": str(q.Last_found_check.strftime("%d %b %Y")),
                        "ReleaseDate": str(q.ReleaseDate.strftime("%d %b %Y"))}
            return dict_out
        def create_dict_Series(q):
            dict_out = {"Title": str(q.Title),
                        "ReleaseDate": str(q.ReleaseDate.strftime("%d %b %Y"))}
            return dict_out
        
        logging.error(ext)
        sort_by = self.request.get("sortby")
        logging.error("received sorting by %s"%sort_by)
        sorting_column = "FoundTorrent"
        order = "desc"
        if (sort_by == "availability"):
            sorting_column = "FoundTorrent"
            order =  "desc"
        if (sort_by == "releasedate"):
            sorting_column = "ReleaseDate"   
            order = "asc"
        q = MovieListing.gql("Where Followed= 1 Order by %s %s"%(sorting_column,order))
        p = list(q)
        s = models.Series.gql("")
        se = list(s)
        if ext:
            
            dict_out = {}
            for i in range(0,len(p),1):
                current_entry = create_dict_Movielisting(p[i])
                dict_out["Movie"+str(i)] = current_entry
            for i in range(0,len(se),1):
                current_entry = create_dict_Series(se[i])
                dict_out["Series"+str(i)] = current_entry
            if not dict_out.get("Movie"+str(len(p)-1)):
                self.write("Error while creating")
            self.write(json.dumps(dict_out))
        else:    
            self.render("front.html", listing = p, page_heading = "Homepage - Marius", listing_length = len(p))
        
    def post(self, ext):
        self.write("Updating")
        q = models.MovieListing.gql("Where Followed= :one", one=1)
        p = list(q)
        number_of_titles = len(p)
        for listing in p:
            if listing.FoundTorrent == 0:
                update_torrent(listing.Title)
                
                self.write("\nDone%s / %s"%(p.index(listing), number_of_titles))
                time.sleep(2)
        
        q = System_tools.gql("Where name= :title", title="Updatekeep")
        p = list(q)
        if p:
            p[0].value = "1"
            p[0].put()
        else:
            q=System_tools(name="Updatekeep", value="1")
            q.put()
        
        
        
      
class AddMovie(MovieHandler):
    def get(self, IMDB_link):
        #check if valid immediately as in post
        #check if already exists by title and imdblink
        #if IMDB_link:
        
        IMDB_link = str(IMDB_link)  
        self.render("AddMovie.html", page_heading = "Add Movie - Marius", IMDB_link = IMDB_link)
        
    def post(self, IMDB_link):
        
        IMDB_entered = str(self.request.get("IMDB_link"))
        id_index = IMDB_entered.find("title/")+6
        imdb_id= IMDB_entered[id_index:id_index+9]
        #logging.error("id=%s"%imdb_id)
        #exception handling here, what if not found?
        
        j = create_json_details(imdb_id)
        Title = j["Title"]
        IMDB_link = "http://www.imdb.com/title/"+j["imdbID"]
        Poster_link = j["Poster"]
        if Poster_link == "N/A":
            Poster_link = None 
        Creators = j["Director"]+", "+j["Writer"]
        Actors = j["Actors"]
        if j["Released"] == "N/A":
            ReleaseDate = datetime.date.today() 
        else:
            ReleaseDate = datetime.datetime.strptime(j["Released"], "%d %b %Y").date()
        
            
    #do validation according to API, save details in DB
        
        if not NewListing(Title = Title, IMDB_link = IMDB_link,
                          Poster_link = Poster_link, Creators = Creators,
                          Actors = Actors, ReleaseDate = ReleaseDate):
            self.render("AddMovie.html", page_heading = "Add Movie - Marius", error_IMDB_link = "Error with DB, maybe already entered")
        else:
            self.redirect("/AddMovie")
        
            #self.render("AddMovie.html", error_IMDB_link = "Error with IMDB API")
            
class AddMovie_json(MovieHandler):
    def get(self):
        self.render("AddMovie_json.html", page_heading = "Add Movies JSON - Marius",)
        
    def post(self):
        JSON_entered = str(self.request.get("IMDB_link"))
        JSON_movies = json.loads(JSON_entered)
        i = 1
        Movienr = 0
        Errors = []
            
        while i:
            Movie_id = "Movie"+str(Movienr)
            j = JSON_movies.get(Movie_id)#from json now
            if not j:
                i = 0
            else:
                Title = j["Title"]
                IMDB_link = j["IMDB_link"]
                Followed = j["Followed"]
                Poster_link = j["Poster_link"]
                Creators = j["Creators"]
                Actors = j["Actors"]
                FoundTorrent = j["FoundTorrent"]
                TorrentLink1 = j["TorrentLink1"]
                Last_found_check = datetime.datetime.strptime(j["Last_found_check"], "%d %b %Y").date()
                ReleaseDate = datetime.datetime.strptime(j["ReleaseDate"], "%d %b %Y").date()
                if TorrentLink1 == "None":
                    TorrentLink1 = None
                if Poster_link == "None":
                    Poster_link = None
            
    #do validation according to API, save details in DB
        
                if not NewListing(Title = Title, IMDB_link = IMDB_link, Followed = int(Followed),
                                  Poster_link = Poster_link, Creators = Creators,
                                  Actors = Actors, FoundTorrent = int(FoundTorrent), TorrentLink1 = TorrentLink1,
                                  Last_found_check = Last_found_check, ReleaseDate = ReleaseDate):
                    Errors.append(IMDB_link)
                Movienr+=1
        self.write("These were not entered (may be already there/ bad data parsing) = " + str(Errors))
                
            
            
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
 
class Series(MovieHandler):
    def get(self):
        q = models.Series.gql("")
        p = list(q)
        if not p:
            p=[]
        self.render("series.html", series = p, page_heading = "Series - Marius", listing_length = len(p))
        
    def post(self):
        Title_entered = str(self.request.get("Title"))
        ReleaseDate = str(self.request.get("ReleaseDate"))
        if ReleaseDate:
            logging.error("REleasedate incoming")
            try:
                ReleaseDate = datetime.datetime.strptime(ReleaseDate, "%d %b %Y").date()
                if not NewSeries(Title = Title_entered, ReleaseDate = ReleaseDate):
                    self.render("series.html", page_heading = "Series - Marius", error_series_name = "Error with DB, maybe already entered")
                else:
                    self.redirect("/Series")
            except:
                
                self.render("series.html", page_heading = "Series - Marius", error_series_name = "Invalid Date format")
        else:
            if not NewSeries(Title = Title_entered, ReleaseDate = ReleaseDate):
                self.render("series.html", page_heading = "Series - Marius", error_series_name = "Error with DB, maybe already entered")
            else:
                self.redirect("/Series") 
class Update(MovieHandler):
    def post(self):
        logging.error("Update post request")
        data = json.loads(self.request.body)
        self.write(json.dumps({'output': "Post request received and responded", "index":data["index"]}))
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
            self.render("Movie_listing_details.html", page_heading = p[0].Title +" - Marius", listing = p[0])
        else:
            self.write("Title Not Found")
    def post(self, movie_name):
        post_falseflag = self.request.get("falseflag")
        post_checktorrent = self.request.get("checktorrent")
        #logging.error("falseflag=%s"%post_falseflag)
        #logging.error("checktorrent=%s"%post_checktorrent)
        if post_checktorrent:
            update_torrent(movie_name) #possiblity for some nice js message popup
            time.sleep(1)
            self.redirect("/Details/%s"%movie_name)
        if post_falseflag:
            q = models.MovieListing.gql("Where Title= :title", title=str(movie_name))
            p = list(q)
            
            p[0].FoundTorrent = 0
            p[0].put()
            self.redirect("/Details/%s"%movie_name)
        
PAGE_RE = r'((?:[\s\.\:\!\'\&a-zA-Z0-9_-]+/?)*)?'
JSON_ext = r'(?:(\.json))?'
app = webapp2.WSGIApplication([('/AddMovie_json/?', AddMovie_json),
                                ('/AddMovie/?%s?' % PAGE_RE, AddMovie),
                                ('/RemoveMovie/?%s?' % PAGE_RE, RemoveMovie),
                                ('/Details/?%s?' % PAGE_RE, DetailsMovie),
                                ('/Homepage%s?'% JSON_ext, HomePage),
                                ('/Update/', Update),
                                ('/Series/?', Series),
                                ('/?', Blank)
                               ],
                              debug=True)