#!/usr/bin/env python3
"""
Extract Google Place IDs from Google Takeout

Usage:   extract.py favorites.csv > out.kml
Author:  Devin Bayer <dev@doubly.so>
Repo:    https://github.com/akvadrako/json2kml
License: GPL 3.0
"""

import sys, csv, re

from mako.template import Template
from dataclasses import dataclass
from urllib.request import urlopen
from os.path import expanduser
from json import loads

def log(code, *args):
    sys.stderr.write('%8.8s | ' % code)
    sys.stderr.write(' '.join(str(a) for a in args) + '\n')

@dataclass
class place:
    name: str
    note: str
    url: str
    comment: str
    address = ''
    lat = 0.0
    long = 0.0

path = sys.argv[1]
places = []

apikey = open(expanduser('~/.private/google-api')).read().strip()

failed_fd = open('failed.csv', 'a')

reader = csv.reader(open(path), delimiter=',', quotechar='"')
for row in reader:
    log('row', *row[:2])
    if row == 'Title Note URL Comment'.split():
        continue

    p = place(*row)
    p.lat = 0.0
    p.long = 0.0
    p.address = None

    m = re.match(r'.*google.com/maps/place/.*/data=.*!1s(0x[0-9a-fx:]+)', p.url)
    m2 = re.match(r".*google.com/maps/search/([0-9.]+),([0-9.]+)",p.url)
    if not m and not m2:
        log('nomatch', p.url)
        csv.writer(failed_fd).writerow(row)
        continue
    
    if not m2:
        ftid = m.group(1)
        log('match', ftid)
        resp = urlopen(f'https://maps.googleapis.com/maps/api/place/details/json?key={apikey}&ftid={ftid}')
        data = loads(resp.read())
        
        if data['status'] != 'OK':
            log('error', data)
            csv.writer(failed_fd).writerow(row + ['error: ' + data['status']])
            continue
        
        try:
            r = data['result']
            p.address = r['formatted_address']
            p.lat = r['geometry']['location']['lat']
            p.long = r['geometry']['location']['lng']
            log('addr', p.address, p.lat, p.long)
        except Exception as e:
            log('error', e, data)
            raise


        places.append(p)
    
    if not m:
        p.lat = float(m2.group(1))
        p.long = float(m2.group(2))
        places.append(p)
        
        

temp = Template(filename='template.kml.mako')
print(temp.render(
    path=path,
    places=places,
))

failed_fd.close()

