#!/usr/bin/python3
# -*- coding: utf-8 -*-

import urllib.request
import yaml
import sys
import html
import re
from bs4 import BeautifulSoup
from lxml import html

from libhtml import jumpTo, html2text, cleanInlineDescription, cleanSectionName, extractSource, mergeYAML

## Configurations pour le lancement
MOCK_SCHOOL = None
MOCK_TYPE = None
#MOCK_TALENT = "mocks/roublard-talents.html"       # décommenter pour tester avec les talents pré-téléchargées

URL = "https://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.%C3%89coles%20de%20magie.ashx"
FIELDS = ['Nom', 'École', 'Source', 'Description', 'DescriptionHTML', 'Référence' ]
MATCH = ['Nom', 'École']

HDR = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 OPR/114.0.0.0'}

def extractText(list):
    text = ""
    html = ""
    for el in list:
        if el.name == 'b' or el.name == 'br':
            break
        text += html2text(el)
        html += html2text(el, True, 2)
    return { 'text': text, 'html': html }

liste = []
typesList = []
visited = []
features = []

print("Extraction des aptitude (talents)...")


if MOCK_SCHOOL:
    content = BeautifulSoup(open(MOCK_SCHOOL),features="lxml").body
else:
    req = urllib.request.Request(URL, headers=HDR)
    content = BeautifulSoup(urllib.request.urlopen(req).read(),features="lxml").body

section = jumpTo(content, 'h2',{'class':'separator'}, u"Liste des écoles de magie élémentaires")

for s in section:
    if s.name == "ul":
        typesList += s.find_all('li')

for t in typesList:
    element = t.find_next('a')
    type = element.text
    link = element.get('href')

    if "pagelink" not in element.attrs['class']:
        print("Skipping unkown link: %s" % link)
        continue

    pageURL = "https://www.pathfinder-fr.org/Wiki/" + link

    if type in visited:
        continue

    print("Ecole %s" % type)
    visited.append(type)

    if MOCK_TYPE:
        typeContent = BeautifulSoup(open(MOCK_TYPE), features="lxml").body.find(id='PageContentDiv')
    else:
        req = urllib.request.Request(url=pageURL, headers=HDR)
        typeContent = BeautifulSoup(urllib.request.urlopen(req).read(), features="lxml").body.find(id='PageContentDiv')

    for feat in typeContent.find_all('b'):
        text = ""
        if type.lower() in feat.text.lower() or "source" in feat.text.lower():
            continue
        siblings = []
        #for s in feat.next_siblings:
            # print "%s %s" % (key,s.name)
        #    if s.name == 'b' or s.name == 'br':
        #        break
            #elif s.string:
                #text += s.string
        #    else:
        #        siblings += s
        extracts = extractText(feat.next_siblings)
        feature = {}
        feature[u'Nom'] = feat.text.rstrip('.')
        feature[u'École'] = type
        feature[u'Référence'] = pageURL.lower()

        plain = extracts['text']
        html = extracts['html']
        if html.startswith('<br/>'):
            html = html[5:]

        feature['Description'] = plain.strip()
        feature['DescriptionHTML'] = html
        print(feat.text.rstrip('.'))
        print(extracts['text'])

        features.append(feature)
    
            
print("Fusion avec fichier YAML existant...")

HEADER = ""

mergeYAML("../data/magic-type-features.yml", MATCH, FIELDS, HEADER, features)
