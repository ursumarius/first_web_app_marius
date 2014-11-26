import re


def create_titles(title):
    title = str(title)
    title_p = title
    for i in range(len(title)):
        if title[i]==' ' and len(title)>1 and i<len(title):
            print i
            title_p=title_p[:i]+"."+title_p[i+1:]
    return [title, title_p]



year = "2014"
PAGE_RE = r'((?:[\s.a-zA-Z0-9_-]+/?)*)?'
title_found1 = "Divergent 2014 720p HDTS Line Audio x264 Pimp4003"
title_found2 = "Divergent 2014 TS Xvid Mp3-MiLLENiUM"


def find_match(found, title, year):
        titles = create_titles(title)
        for title in titles:
            PAGE_RE = r'(?:'+title+r'( |.)?(\(|\[)?'+year+r'(\)|\])?)' 
            
            matchObj = re.match( PAGE_RE,found, re.M|re.I)
            if matchObj:
               return True
        return None

title_found = "Expandables 3 Trailer"
re.search( r'trailer', title_found, re.M|re.I)

