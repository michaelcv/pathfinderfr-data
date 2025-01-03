#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import json
import os

from jsonmerge import merge

SERVER = "https://boisdechet.org/fvtt"
#SERVER = "http://127.0.0.1:5000"

if not "LC_LOGIN" in os.environ:
  print("LC_LOGIN environment variable must be set!")
  exit(1)
if not "LC_SECRET" in os.environ:
  print("LC_SECRET environment variable must be set!")
  exit(1)


def checkReturnCode(response, expectedCode, context):
  if response.status_code != expectedCode:
    print("[%s] Unexpected response %s" % (context, response.status_code))
    try:
      print(r.json())
    except:
      print("No detail")
    exit(1)

##
## LOGIN to get access token
##
login = os.environ['LC_LOGIN']
secret = os.environ['LC_SECRET']
#login = "Global admin"
#secret = "test"

r = requests.post("%s/login" % SERVER, json={"login": login, "secret": secret})
checkReturnCode(r, 201, "Login")

token = r.json()['access_token']
headers = { "Authorization": "Bearer %s" % token }

##
## LIST of accepted entries
##
r = requests.get("%s/items/accepted" % SERVER, headers=headers)
checkReturnCode(r, 200, "Accepted")


lists={}

list = r.json()
for el in list:
  
  # ignore contributions for other compendiums than pf1-fr
  if not el['compendium'].startswith("pf1-fr"):
    continue;

  # ignore contributions with initiative != 1
  initiative = el['initiativeId'] if 'initiativeId' in el else 0
  if not initiative in [0,1,2,4,5]:
    print("Ignoring initiative %d" % initiative)
    continue;

  compendium = el['compendium'].split('.')[1]
  if not compendium in lists:
    lists[compendium] = {}
  if not el['name'] in lists[compendium]:
    lists[compendium][el['name']] = { 'data': {} }
  
    
  r = requests.get("%s/item/%s" % (SERVER, el['id']), headers=headers)
  checkReturnCode(r, 200, "Details")
  object = r.json()
  data = object['data']['data']
  
  # extract contentNotes and changes only
  if initiative == 1:
    print(el['name'])
    if "contextNotes" in data and len(data["contextNotes"]) > 0:
      lists[compendium][el['name']]['data']["contextNotes"] = data["contextNotes"]
    if "changes" in data and len(data["changes"]) > 0:
      lists[compendium][el['name']]['data']["changes"] = data["changes"]
      
  # extract image only
  elif initiative == 2:
    if "img" in object['data']:
      lists[compendium][el['name']]["img"] = object['data']["img"]
  
  # extract spells elements or others
  elif initiative == 4 or initiative == 5:
    if "ability" in data:
      lists[compendium][el['name']]['data']["ability"] = data["ability"]
    if "abilityType" in data:
      lists[compendium][el['name']]['data']["abilityType"] = data["abilityType"]
    if "actionType" in data:
      lists[compendium][el['name']]['data']["actionType"] = data["actionType"]
    if "damage" in data:
      lists[compendium][el['name']]['data']["damage"] = data["damage"]
    if "measureTemplate" in data:
      lists[compendium][el['name']]['data']["measureTemplate"] = data["measureTemplate"]
    if "range" in data:
      lists[compendium][el['name']]['data']["range"] = data["range"]
    if "save" in data:
      lists[compendium][el['name']]['data']["save"] = data["save"]
    if "duration" in data:
      lists[compendium][el['name']]['data']["duration"] = data["duration"]
    if "uses" in data:
      lists[compendium][el['name']]['data']["uses"] = data["uses"]
    if "activation" in data:
      lists[compendium][el['name']]['data']["activation"] = data["activation"]
  
  elif initiative == 0:
    lists[compendium][el['name']]['data'] = data

for category in lists:
  categName = category
  # special case
  if category.startswith("equip"):
    categName = "equip_" + category[5:].lower()
  
  # merge new contributions with existing data
  filepath = "letscontribute/%s.json" % categName
  
  existing = {}
  if os.path.isfile(filepath) :
    existing = json.load(open(filepath, 'r'))
  
  lists[category] = merge(existing, lists[category])
  # write result into file
  outFile = open(filepath, "w")
  outFile.write(json.dumps(lists[category], indent=3, sort_keys=True))

  
