"""
helpers for proquest
"""
import os
import csv
import bs4


"""
script to handle the raw xml from the proquest database
"""
def parse_proquest_xml(filename):
    soup = bs4.BeautifulSoup(open(filename), features="xml")
    text_raw = soup.find("Text").text
    text_soup = bs4.BeautifulSoup(text_raw, features="xml")
    paras = text_soup.findAll("p")
    source = soup.find("PubFrosting").find("Title").text
    title = soup.find("TitleAtt").find("Title").text
    date = soup.find("NumericDate").text
    if len(paras) > 0:
        text = '\n'.join([p.text.strip() + '\n' for p in paras])
    else:
        text = text_raw

    return {"date": date, "source": source, "title": title, "text": text, "filename": os.path.basename(filename)}

def save_txtfiles(records, dir):
    os.makedirs(dir, exist_ok=True)
    for r in records:
        textfile = f"{dir}/{r['filename']}.txt"
        with open(textfile, 'wt') as f:
            f.write(r['text'])
        r['textfile'] = textfile
        del r['text']
    return records