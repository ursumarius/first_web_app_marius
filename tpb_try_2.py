import urllib2
import json
import re


def inspect_tpb(title, year):
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
    
    proxy = "http://pirateproxy.in"
    proxy_search = proxy+"/search/"
    search_url = create_search_url(title, year, proxy_search)
    try:
        t = urllib2.urlopen(search_url)
        t = t.read()
        index = 9000
        m = compute_length_match(title)
        for i in range(3):
            index = t.find("Details for",index)
            title_found = t[index+12: index+12+m]
            index = index + 3* 1100
            #try match, and return search_url if found, else loop more
            if find_match(title_found, title, year):
                return search_url
        return None
    except:
        return "Error"
    
