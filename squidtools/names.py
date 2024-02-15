# Generic library for
import spacy
from collections import Counter
import en_core_web_sm
nlp = en_core_web_sm.load()

def isNormalizedName(namestr):
    # It's probably a normalized name if there is exactly one comma
    if len(namestr.split(',')) == 2:
        return True
    return False

def processNormalizedName(namestr):
    components = namestr.split(',')
    lastname = components[0]
    f_comps = components[1].split(' ')
    firstname = f_comps[1]
    middle = f_comps[2] if len(f_comps) >= 2 else None
    middleInitial = middle[0] if middle else None

def isSuffix(suffix):
    SUFFIXES = ["jr", "sr", "i", "ii", "iii", "iv", "v"]
    suf = suffix.tolowercase().replace('.', '')
    return suf in SUFFIXES

def isInitial(init):
    ini = init.tolowercase().replace('.', '')
    return len(ini) == 1

def processUnnormalizedName(namestr):
    firstname = None
    middleInitial = None
    middle = None
    lastname = None
    suffix = None
    components = namestr.split(',')
    if isSuffix(components[-1]):
        suffix = components[-1]
        components.remove(components[-1])
    if (len(components) == 2):
        firstname = components[0]
        lastname = components[1]
    if (len(components) == 3):
        firstname = components[0]
        middle = components[1]
        middleInitial = middle[0]
        if (isInitial(middle)):
            middle = None
        lastname = components[2]
    return {
        'first': firstname, 
        'middleInitial': middleInitial, 
        'middle': middle, 
        'lastname': lastname, 
        'suffix': suffix
    }

def processName(name):
    if isNormalizedName(name):
        return processNormalizedName(name)
    else:
        return processUnnormalizedName(name)


def compareNames(name1, name2):
    name1_p = processName(name1)
    name2_p = processName(name2)



def byline(byline):
    # Given a byline, extract the name string
    ents = [x.text for x in nlp(byline).ents]
    return ents