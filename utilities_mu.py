
import re
from string import letters

import hmac
import hashlib
import random
import string
import json
import datetime

import time
import logging

def Post_as_dict(q):
    dict_out = {"subject": str(q.subject),
                "content":str(q.content),
                "created": q.created.strftime("%X, %d %b %Y"),
                "last_modified": q.last_modified.strftime("%X, %d %b %Y"),
                "test_escaping": 'hello"'}
    return dict_out

def make_json_str(cache_content, page, postid = 0):
    if page== "front":
        q = cache_content
        q=list(q)
        dict_out = {}
        for i in range(0,len(q),1):
            current_entry = Post_as_dict(q[i])
            dict_out["entry"+str(i)] = current_entry
        return json.dumps(dict_out)
  
    elif(page == "post"):
        q = Cached_post(postid)
        dict_out = {}
        current_entry = Post_as_dict(q)
        dict_out["entry0"] = current_entry
        return json.dumps(dict_out)
   
     
#####hash stuff
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(pw, salt= None):
    if not salt :
        salt = make_salt()
    h = hmac.new(salt,pw).hexdigest()
    return '%s|%s' % (h, salt)

def hash_str(salt,passw):
    return hmac.new(salt,passw).hexdigest()

def valid_pw(pw, h):
    try:
        salt = h.split("|")[1]
    except:
        salt = None
    newhash = make_pw_hash(pw, salt)
    if h == newhash:
        return True
    return False


