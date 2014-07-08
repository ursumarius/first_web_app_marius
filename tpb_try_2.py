import urllib2
import json
import re

def test():
    lis= []
    lis.append(inspect_tpb("The Grand Budapest Hotel", "2014"))
    lis.append(inspect_tpb("Drive", "2011"))
    lis.append(inspect_tpb("Pain and Gain", "2013"))
    lis.append(inspect_tpb("The beaver", "2011"))
    lis.append(inspect_tpb("the expendables 3", "2014"))
    lis.append(inspect_tpb("a long way down", "2014"))
    lis.append(inspect_tpb("The anomaly", "2014"))
    lis.append(inspect_tpb("the equalizer", "2014"))
    return lis


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
