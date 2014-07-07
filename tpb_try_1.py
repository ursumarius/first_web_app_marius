import urllib2
import json

def create_search_url(title, year):
    title = str(title)
    search = escape_urlobj(title+" "+year)
    return "http://pirateproxy.in/search/"+search+"/0/99/0"


##def remove_newline(input_str):
##    return '{'+input_str[3:-3]+'}'

#search for: 'title="Details for '
#save link starting from previous find, and looking for 'href="'.

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
    return count+len(title)+5


def create_matches(title, year):
    title = str(title)
    title_p = title
    for i in range(len(title)):
        if title[i]==' ' and len(title)>1 and i<len(title):
            print i
            title_p=title_p[:i]+"."+title_p[i+1:]
            
    return [title+" "+year, title_p+"."+year]
