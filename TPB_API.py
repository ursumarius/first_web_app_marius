import os
import webapp2
import string
import json
import urllib2
import utilities_mu
import logging
import re

escape_urlobj = utilities_mu.escape_urlobj



#creates the title using "." instead of space. returns normal and with "."
def create_titles(title):
    title = str(title)
    title_p = title
    for i in range(len(title)):
        if title[i]==' ' and len(title)>1 and i<len(title):
            print i
            title_p=title_p[:i]+"."+title_p[i+1:]
    return [title, title_p]

#matches the title+year based on the findings, returns True if found
def find_match(found, title, year):
    titles = create_titles(title)
    for title in titles:
        PAGE_RE = r'(?:'+title+r'( |.)?(\(|\[)?'+year+r'(\)|\])?)' 
        matchObj = re.match( PAGE_RE,found, re.M|re.I)
        if matchObj:
           return True
    return None

#outputs the search_url according to the movie details and proxy
def create_search_url(title, year, proxy):
    title = str(title)
    search_term = escape_urlobj(title+" "+year)
    return proxy+"/search/"+search_term+"/0/99/200"

#simulates a probably evenly distributed spread of hits among the proxies, returns the index of proxy to be queried
def pick_index(title, length_proxies):
    if len(title)>4:
        return (ord(title[-1]) + ord(title[-2]) + ord(title[-3]))%length_proxies
    else:
        return 0

def inspect_tpb(title, year, proxies, diff_proxy = None):
    
    proxy_index = pick_index(title, len(proxies))
    
    if (diff_proxy is not None) and (diff_proxy == proxy_index):
        proxy_index = (proxy_index + 1) % (len(proxies))
    
    proxy = proxies[proxy_index]
    search_url = create_search_url(title, year, proxy)
    
    try:
        logging.error("Enter access of TPB")
        t = urllib2.urlopen(search_url)
        t = t.read()
        index = 9000
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
                    logging.error("Found")
                    return search_url
                    
                hit = 1
        logging.error("Not Found")
        return None
        
    
    except:
        logging.error("Enter exception of TPB")
        if diff_proxy:
            logging.error("Error")
            return "Error"
        
        else:
            logging.error("Not Found")
            return inspect_tpb(title, year, proxies, proxy_index)

