"""
helpers for proquest
"""
import pdb
import os
import csv
import bs4

from . import util

def findText(soup, nodename):
    node = soup.find(nodename)
    if node:
        return node.text
    else:
        return None

def findNestedText(root, nodenames):
    node = root
    for noden in nodenames:
        node = node.find(noden)
        if node is None:
            return None
        
    return node.text
        


def processOriginalAuthor(author):
    if author is None:
        return None
    print(author)
    if author.startswith('By'):
        author.removeprefix('By')
    return author.strip()


"""
script to handle the raw xml from the proquest database
"""
def parse_proquest_xml(filename):
    soup = bs4.BeautifulSoup(open(filename), features="xml")
    text_raw = soup.find("Text") or ''
    paras = []
    text = ''
    if text_raw:
        text_soup = bs4.BeautifulSoup(text_raw.text, features="xml")
        paras = text_soup.findAll("p")
        if len(paras) > 0:
            text = '\n'.join([p.text.strip() + '\n' for p in paras])
        else:
            text = text_raw.text
    try:
        source = findNestedText(soup, ["PubFrosting", "Title"])
        title = findNestedText(soup, ["TitleAtt", "Title"])
        date = findText(soup, "NumericDate")
        normalized = None
        original = None
        authornode = soup.find("Author")
        if authornode:
            normalized = findText(authornode, "NormalizedDisplayForm")
            original = processOriginalAuthor(findText(authornode, "OriginalForm"))
            components = original.split(',')
            if len(components) > 1 and ' ' not in components[0]:
                normalized = original
            if normalized is None and original is None:
                pdb.set_trace()


    except:
        print(filename)
        pdb.set_trace()

    return {"date": date, "source": source, "title": title, "text": text, "filename": os.path.basename(filename), 
            "author_normalized": normalized,
            "author": original}

def save_txtfiles(records, dir):
    os.makedirs(dir, exist_ok=True)
    for r in records:
        textfile = f"{dir}/{r['filename']}.txt"
        with open(textfile, 'wt') as f:
            f.write(r['text'])
        r['textfile'] = textfile
        del r['text']
    return records

def convert_all(dirname, tsvname, txtdir='txt'):
    records = []
    for f in os.listdir(dirname):
        records.append(parse_proquest_xml(dirname + '/'+f))
    save_txtfiles(records, txtdir)
    util.write_csv(records, tsvname, delimiter='\t')