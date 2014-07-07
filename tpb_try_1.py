import urllib2
import json


def escape_urlobj(title):
    title = str(title)
    for i in range(len(title)):
        if title[i]==' ' and len(title)>1 and i<len(title):
            print i
            title=title[:i]+"%20"+title[i+1:]
    return title

def create_search_url(title, year, proxy):
    title = str(title)
    search = escape_urlobj(title+" "+year)
    return proxy+search+"/0/99/0"

def compute_length_match(title):
    count = 0
    for element in title:
        if element == " ":
            count+=1
    return count+len(title)+6


##def create_matches(title, year):
##    title = str(title)
##    title_p = title
##   
##    for i in range(len(title)):
##        if title[i]==' ' and len(title)>1 and i<len(title):
##            print i
##            title_p=title_p[:i]+"."+title_p[i+1:]
##    
##    return [title+" "+year, title_p+"."+year, ]

def searches_3(title, year):
    proxy = "http://pirateproxy.in"
    proxy_search = proxy+"/search/"
    search_url = create_search_url(title, year, proxy_search)
    t = urllib2.urlopen(search_url)
    t = t.read()
    index = 9000
    out_dict = {}
    key = 1
    out_list = []
    index_list = []
    m = compute_length_match(title)
    for i in range(3):
        index = t.find("Details for",index)
        index_list.append(index)
        title = t[index+12: index+12+m]
        index = index - 150
        index = t.find('href="',index)
        index2 = t.find('"',index+6)
        link = proxy + t[index+6: index2]
        out_dict = {"#": key, "title":title,"link":link}
        out_list.append(out_dict)
        key = key+3
        index = index + 3* 1100

    return out_list, search_url
    
