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
import TPB_API
import IMDB_API
import re
import time
from google.appengine.ext import db


inspect_tpb = TPB_API.inspect_tpb
create_json_details = IMDB_API.create_json_details
Series = models.Series
NewSeries = models.Series.NewSeries
NewListing = models.MovieListing.NewListing
TorrentLink1Edit = models.MovieListing.TorrentLink1Edit
FollowedChange = models.MovieListing.FollowedChange
FoundTorrentChange = models.MovieListing.FoundTorrentChange
MovieListing = models.MovieListing
PirateProxies = models.PirateProxies
AddProxy = models.PirateProxies.AddProxy
System_tools = models.System_tools
Users = models.Users
signup = models.Users.signup
login_check = models.Users.login_check
correct_cookie = models.Users.correct_cookie
make_json_str = utilities_mu.make_json_str
render_str = jinja_util.render_str
#single_post = models.single_post

#basic function used for all child handlers
class MovieHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        
        #in order to know when the last update was done, and display it
        q = System_tools.gql("Where name= :title", title="Updatekeep")
        p = list(q)
        if p:
            kw['system_tools_object'] = p[0]
            
        self.write(self.render_str(template, **kw))
    #makes use of the TPB API, if found will modify the DB
    def update_torrent(movie_name):
        
        q = models.MovieListing.gql("Where Title= :title", title=str(movie_name))
        p = list(q)
        obj_movie = p[0]
        proxies = PirateProxies.GetProxies()
        findings = inspect_tpb(obj_movie.Title, obj_movie.ReleaseDate.strftime("%Y"), proxies)
        
        if findings != "Error":
            
            truth = 0
            if findings:
                truth = 1
                
            FoundTorrentChange(movie_name, findings, truth)
            
            return True
        return False


#if path is empty, will redirect to homepage
class Blank(MovieHandler):
    def get(self):
        self.redirect("/Homepage")
        
#Homepage handler
class HomePage(MovieHandler):
    def get(self, ext):
        
        AddProxy("http://thepiratebay.se/") #just add, initialize the table so then can add by developer console
                
        #creates a dictionary containing data of the movie_listing, used for Json
        def create_dict_Movielisting(movie_listing_obj):
            dict_out = {"Title": str(movie_listing_obj.Title),
                        "IMDB_link":str(movie_listing_obj.IMDB_link),
                        "Followed": str(movie_listing_obj.Followed),
                        "Poster_link": str(movie_listing_obj.Poster_link),
                        "Creators": movie_listing_obj.Creators,
                        "Actors": (movie_listing_obj.Actors),
                        "FoundTorrent": str(movie_listing_obj.FoundTorrent),
                        "TorrentLink1": str(movie_listing_obj.TorrentLink1),
                        "Last_found_check": str(movie_listing_obj.Last_found_check.strftime("%d %b %Y")),
                        "ReleaseDate": str(movie_listing_obj.ReleaseDate.strftime("%d %b %Y"))}
            
            return dict_out
        
        #creates a dictionary for the series , used for Json
        def create_dict_Series(series_listing_obj):
            dict_out = {"Title": str(series_listing_obj.Title), "ReleaseDate": str(series_listing_obj.ReleaseDate.strftime("%d %b %Y"))}
            return dict_out
        
        #deciding sorting
        sort_by = self.request.get("sortby")
        sorting_column = "FoundTorrent"
        order = "desc"
        
        if (sort_by == "availability"):
            sorting_column = "FoundTorrent"
            order =  "desc"
            
        if (sort_by == "releasedate"):
            sorting_column = "ReleaseDate"   
            order = "asc"
            
        movie_cursor = MovieListing.gql("Where Followed= 1 Order by %s %s"%(sorting_column,order))
        movie_listing_list= list(movie_cursor)
        series_cursor = models.Series.gql("")
        series_list = list(series_cursor)
        
        #JSON creation, movielisting, series
        if ext:
            dict_out = {}
            
            for i in range(0,len(movie_listing_list),1):
                current_entry = create_dict_Movielisting(movie_listing_list[i])
                dict_out["Movie"+str(i)] = current_entry
                
            for i in range(0,len(series_list),1):
                current_entry = create_dict_Series(series_list[i])
                dict_out["Series"+str(i)] = current_entry
                
            if not dict_out.get("Movie"+str(len(movie_listing_list)-1)):
                self.write("Error while creating")
                
            self.write(json.dumps(dict_out))
            
        else:
            self.render("front.html", listing = movie_listing_list, page_heading = "Homepage - Marius", listing_length = len(movie_listing_list))
        
    #the post is exclusively for checking torrents availability
    def post(self, ext):
        
        movie_cursor = models.MovieListing.gql("Where Followed= :one", one=1)
        p = list(movie_cursor)
        number_of_titles = len(p)
        
        for listing in p:
            
            if listing.FoundTorrent == 0:  
                update_torrent(listing.Title)
                time.sleep(2)

        last_check_cursor = System_tools.gql("Where name= :title", title="Updatekeep")
        last_check_obj_list = list(last_check_cursor)
        
        if last_check_obj_list:
            last_check_obj_list[0].value = "1"
            last_check_obj_list[0].put()
            
        else:
            last_check_cursor=System_tools(name="Updatekeep", value="1")
            last_check_cursor.put()
            
        self.write("Done")
        
        
#dialog for adding movies using imdb link
class AddMovie(MovieHandler):
    def get(self, IMDB_link):
        
        IMDB_link = str(IMDB_link)  #support for immediate addition from url path
        self.render("AddMovie.html", page_heading = "Add Movie - Marius", IMDB_link = IMDB_link)
        
    def post(self, IMDB_link):
        
        IMDB_entered = str(self.request.get("IMDB_link"))
        id_index = IMDB_entered.find("title/")+6
        imdb_id= IMDB_entered[id_index:id_index+9]
           
        imdb_json = create_json_details(imdb_id)
        
        if imdb_json["Response"] == "True":
            
            Title = imdb_json["Title"]
            IMDB_link = "http://www.imdb.com/title/"+imdb_json["imdbID"]
            Poster_link = imdb_json["Poster"]
            if Poster_link == "N/A":
                Poster_link = None 
            Creators = imdb_json["Director"]+", "+imdb_json["Writer"]
            Actors = imdb_json["Actors"]
            if imdb_json["Released"] == "N/A":
                ReleaseDate = datetime.date.today() 
            else:
                ReleaseDate = datetime.datetime.strptime(imdb_json["Released"], "%d %b %Y").date()
            
                
            #do validation according to API, save details in DB
            if not NewListing(Title = Title, IMDB_link = IMDB_link,
                              Poster_link = Poster_link, Creators = Creators,
                              Actors = Actors, ReleaseDate = ReleaseDate):
                self.render("AddMovie.html", page_heading = "Add Movie - Marius", error_IMDB_link = "Error with DB, maybe already entered")
            else:
                self.redirect("/AddMovie")
        
        else:
            self.render("AddMovie.html", page_heading = "Add Movie - Marius", error_IMDB_link = "Invalid ID")
            
#used when input is in JSON
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
            imdb_json = JSON_movies.get(Movie_id)#from json now
            if not imdb_json:
                i = 0
            else:
                Title = imdb_json["Title"]
                IMDB_link = imdb_json["IMDB_link"]
                Followed = imdb_json["Followed"]
                Poster_link = imdb_json["Poster_link"]
                Creators = imdb_json["Creators"]
                Actors = imdb_json["Actors"]
                FoundTorrent = imdb_json["FoundTorrent"]
                TorrentLink1 = imdb_json["TorrentLink1"]
                Last_found_check = datetime.datetime.strptime(imdb_json["Last_found_check"], "%d %b %Y").date()
                ReleaseDate = datetime.datetime.strptime(imdb_json["ReleaseDate"], "%d %b %Y").date()
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
                
        #respond with relevant info
        if Errors:
            self.write("These were not entered (may be already there/ bad data parsing) = " + str(Errors))
        else:
            self.write("Success")
            

#handles "stop following" button
class RemoveMovie(MovieHandler):
    def get(self, movie_id):
        
        if movie_id:
            
            if (FollowedChange(int(movie_id), 0)):
                time.sleep(0.5) #needed for nice db time lag, possibly with cache not needed.
                self.redirect("/Homepage")
                
            else:
                self.write('<div style="font-family: verdana;">Wrong link</div>')
        
        else:
            self.write('<div style="font-family: verdana;">Wrong link</div>')
 
#displays Series
class Series(MovieHandler):
    def get(self):
        series_cursor = models.Series.gql("")
        series_list = list(series_cursor)
        if not series_list:
            series_list=[]
        self.render("series.html", series = series_list, page_heading = "Series - Marius", listing_length = len(series_list))
        
    def post(self):
        Title_entered = str(self.request.get("Title"))
        ReleaseDate = str(self.request.get("ReleaseDate"))
        
        if ReleaseDate:
           
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
                

#this was left after experimenting with JS
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

#details per every movie
class DetailsMovie(MovieHandler):
    
    def get(self, queryparam):
        #problem with redirecting titles with space.
        movie_name = queryparam[queryparam.find("-")+1:]
        logging.error("movie_name=<%s>'"%movie_name)
        ident = queryparam[0:queryparam.find("-")]
        logging.error("ident=<%s>'"%ident)
        movie_listing_obj = models.MovieListing.get_by_id(int(ident))
        
        if movie_listing_obj:
            self.render("Movie_listing_details.html", page_heading =movie_listing_obj.Title +" - Marius", listing = movie_listing_obj)
        else:
            self.write("Title Not Found")
            
    def post(self, queryparam):
        post_falseflag = self.request.get("falseflag")
        post_checktorrent = self.request.get("checktorrent")
        movie_name = queryparam[queryparam.find("-")+1:]
        #logging.error("falseflag=%s"%post_falseflag)
        #logging.error("checktorrent=%s"%post_checktorrent)
        
        movie_cursor = models.MovieListing.gql("Where Title= :title", title=str(movie_name))
        movie_listing_list = list(movie_cursor)
        logging.error("ID=%s"%movie_listing_list[0].key().id())
        logging.error("NAME=%s"%movie_name)
        if post_checktorrent:
            update_torrent(movie_name) #possiblity for some nice js message popup
            time.sleep(1)
            
        if post_falseflag:
            
            movie_listing_list[0].FoundTorrent = 0
            movie_listing_list[0].put()
        self.redirect("/Details/%s-%s"%(movie_listing_list[0].key().id(),movie_name))
        
PAGE_RE = r'((?:[\?\s\.\:\!\'\&a-zA-Z0-9_-]+/?)*)?'
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