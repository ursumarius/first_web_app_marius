import string


filme = """The Giver
Wish I Was Here
Sin City: A Dame to Kill For
47 Ronin
Chef 
Kill your darlings
The Prototype
Interstellar
The zero theorem
The two faces of january
Reasonable Doubt
Jupiter Ascending
transcendence
Life on the Line
Closed Circuit
Godzilla
Enemy
The Pervert's Guide to Ideology
still mine
Blood ties
The rover
Lego movie
Strain (TV series)
Edge of tomorrow
Neighbors
Zodiac
Hours
Violet and daisy
Doomsday  (2013)
Monuments men
Non-stop
Kick ass 2
The wolverine
Under the skin
American Hustle 
rapture palooza
+1
Paranoia 
Simon Killer
Empire State
This is the end
The Family
A Single shot
Walking with dinosaurs
Chasing Mavericks 
Alter Egos
23 Minutes to Sunrise
Scenic Route
Maniac
Arthur newman
300
the canyons
in their skin
Phantom
the iceman
hotel noir
Wrong 2012
gambit
Spring Breakers
The Host
The factory
Resolution 
Ginger & Rosa (2012)
The Last Stand
The Lone Ranger
Small Appartments
Led Zeppelin
nesigur: jacobs ladder
What Dreams May Come
luv
snitch
the master
Someday This Pain Will Be Useful to You 
vacanta mare
nature calls\
World's Great Dad
Dogtooth 
Notes on a Scandal 
The Wave. Die Welle
People Like Us
bobbe thompson
Virginia 
Four
easy money
Assasination Games
Super
Point Blank
Kidnapped
Phantom
I am
The Trip
Truth In Numbers
Now

"""
def make_titles_with_plus(lista):
    list_out = []
    for title in filme.split("\n"):
        
        list_out.append(replace_plus(title))
    return list_out
    
def replace_plus(title):
    
    for i in range(0,len(title),1):
        if title[i] == " ":
            title = title[:i] + "+" + title[i+1:]
    return title

def make_links(txt_filme):
    list_plused = make_titles_with_plus(txt_filme)
    list_out = []
    for element in list_plused:
        list_out.append("http://filelist.ro/browse.php?search=%(name)s&cat=0&searchin=0&sort=0"%{"name":element})
    return list_out

def make_txt_links(txt_in):
    list_links = make_links(txt_in)
    finaltxt = ""
    for element in list_links:
        finaltxt += "\n<a href=%s>"%element
        finaltxt+= element
        finaltxt+= "</a></br>"
    return finaltxt

print make_txt_links(filme)

