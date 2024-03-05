# Generic library for
import spacy
from collections import Counter
import en_core_web_sm
import string
import Levenshtein


nlp = en_core_web_sm.load()

# Remove spaces and punctuation 
def clean(name, remove_punct=True):
    n = name.lower().strip()
    if remove_punct:
        return n.translate(str.maketrans('', '', string.punctuation)).strip()
    else:
        return n

def isSuffix(suffix):
    SUFFIXES = ["jr", "sr", "i", "ii", "iii", "iv", "v"]
    return clean(suffix) in SUFFIXES

def isInitial(init):
    return len(clean(init)) == 1

def isNormalizedName(namestr):
    # It's probably a normalized name if there is exactly one comma
    if len(namestr.split(',')) == 2:
        return True
    return False

def unnormalize(name):
    if ',' in name:
        names = name.split(',')
        joined = ' '.join(names[1:] + [names[0]])
        return joined.replace('  ', ' ').strip()
    return name

def lev_dist(name1, name2):
    name1 = clean(unnormalize(name1))
    name2 = clean(unnormalize(name2))
    return Levenshtein.distance(name1, name2)

def parseNormalizedName(namestr):
    assert isNormalizedName(namestr)
    suffix = None
    middleInitial = None
    components = namestr.split(',')
    lastname = components[0]
    f_comps = components[1].strip().split(' ')

    # Simplest case, "Zheng, Sylvan"
    if len(f_comps) == 1:
        firstname = f_comps[0]
    elif len(f_comps) == 2 and isInitial(f_comps[1]):
        # Zheng, Sylvan A.
        firstname = f_comps[0]
        middleInitial = f_comps[1]
    elif len(f_comps) == 2 and isSuffix(f_comps[1]):
        firstname = f_comps[0]
        suffix = f_comps[1]
    elif len(f_comps) == 2:
        # Dangerous assumption, first middle format
        firstname = f_comps[0]
        middleInitial = f_comps[1][0]
    else:
        return None

    return {
        'firstname': firstname, 
        'middleInitial': middleInitial, 
        'lastname': lastname, 
        'suffix': suffix
    }

def parseRawName(namestr):
    firstname = None
    middleInitial = None
    lastname = None
    suffix = None

    components = clean(namestr).split(' ')
    # Check the last element suffix
    if isSuffix(components[-1]):
        suffix = components[-1]
        components.remove(components[-1])

    # For 2 word names, we assume first last format
    # Last name cannot be a single letter though
    if len(components) == 2 and not isInitial(components[1]):
        firstname = components[0]
        lastname = components[1]
    # For 3 word names with a single middle letter
    # we assume first middle_init last format
    elif len(components) == 3 and isInitial(components[1]):
        firstname = components[0]
        middleInitial = components[1]
        lastname = components[2]
    else:
        # For other 3 word names, possibilities include
        # double-first names (Mary Kate Olsen)
        # double-last names (Simon de Bouvair)
        # first middle last (Homer Jay Simpson)
        # And don't even get me started on 4-word names
        # I dont think we can make any assumptions about these
        return None

   
    return {
        'firstname': firstname, 
        'middleInitial': middleInitial, 
        'lastname': lastname, 
        'suffix': suffix
    }

def parseName(name):
    if isNormalizedName(name):
        return parseNormalizedName(name)
    else:
        return parseRawName(name)


def parseAndCompareNames(name1, name2):
    no1 = parseName(name1)
    no2 = parseName(name2)
    if no1 is None or no2 is None:
        return None

    def cmp_part(no1, no2, part):
        if no1[part] is None or no2[part] is None:
            return 0.2
        return 1 if clean(no1[part]) == clean(no2[part]) else 0
    
    return {
        'firstname': cmp_part(no1, no2, 'firstname'),
        'middleInitial': cmp_part(no1, no2, 'middleInitial'),
        'lastname': cmp_part(no1, no2, 'lastname'),
    }


def byline(byline):
    # Given a byline, extract the name string
    ents = [x.text for x in nlp(byline).ents]
    return ents

# Generate a simple match score for name matches
def simpleMatchScore(name1, name2):
    if name1 == name2:
        # Exact match
        return 1.0
    if clean(name1) == clean(name2):
        # Almost exact match
        return 0.99

    pieces1 = set(clean(name1).split(" "))
    pieces2 = set(clean(name2).split(" "))

    # One name is a strict subset of another name
    # without considering order
    # Eg, "Walker, James" => "James A Walker"
    common = pieces1.intersection(pieces2)
    if len(common) == len(pieces1) and len(common) == len(pieces2):
        return 0.95

    # At this point we resort to some heuristics 
    pcresult = parseAndCompareNames(name1, name2)
    if pcresult:
        return pcresult['lastname'] * 0.5 + pcresult['firstname'] * 0.3 + pcresult['middleInitial'] * 0.1
    
    return len(common) / ((max(len(pieces1), len(pieces2))) + 0.1)
    