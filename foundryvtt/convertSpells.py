#!/usr/bin/python3
# -*- coding: utf-8 -*-

import yaml
import json
import typing
import sys
import re

from libData import *

data = None
with open("../data/spells.yml", 'r') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)


def getLevel(level):
    m = re.search('([0-9])', level)
    if m:
        return int(m.group(1))
    else:
        return 0

#
# nettoie la valeur de certaines particularités
#
def cleanValue(value):
  value = value.strip()
  if value.endswith(',') or value.endswith(';') or value.endswith('.'):
    value = value[:-1].strip()
  return value

def getActivation(time):
    if not time:
        return None
    
    m = re.search('^([0-9]+) (.*)$', time)
    if m:
        value = int(m.group(1))
        type = m.group(2)
        if type.startswith("minute"):
            return { "cost": value, "type": "minute" }
        elif type.startswith("heure"):
            return { "cost": value, "type": "hour" }
        elif type.startswith("round"):
            return { "cost": value, "type": "round" }
        elif "complexe" in type: 
            return { "cost": value, "type": "full" }
        elif "immédiate" in type: 
            return { "cost": value, "type": "immediate" }
        elif "simple" in type:
            return { "cost": value, "type": "standard" }
        elif "rapide" in type:
            return { "cost": value, "type": "swift" }
        
        print(time)
    
    return { "cost": 0, "type": "special" }
  
def getRange(range):
    if not range:
        return None
    range = range.lower()
    
    if "contact" in range:
        return { "units": "touch" }
    elif "courte" in range:
        return { "units": "close" }
    elif "moyenne" in range:
        return { "units": "medium" }
    elif "longue" in range:
        return { "units": "long" }
    elif "personelle" in range:
        return { "units": "personal" }
    else:
        return { "units": "seeText" }    


def getSchool(school):
    if not school:
        return None
    school = school.lower()
    
    m = re.search('^(\w+)', school)
    if m:
        return m.group(1)
    else:
        print(school)

def getSubSchool(school):
    m = re.search('\((.+?)\)', school)
    if m:
      return m.group(1).lower()
    else:
      return ""

def getTypes(school):
    m = re.search('\[(.+?)\]', school)
    if m:
      return m.group(1).lower()
    else:
      return ""

def getComponents(comp):
    idx = comp.find('(')
    if idx > 0:
      comp = comp[0:idx].strip()
    
    # ugly fixes
    idx = comp.find('une goutte de sang du lanceur')
    if idx > 0:
      comp = comp[0:idx].strip()
    comp = comp.replace('ou', ',').replace('/',',')
    
    # parse elements
    comps = []
    for el in comp.split(','):
      comps.append(el.strip())
    return comps

def getComponentsFD(comps):
    fd = "FD" in comps
    m = "M" in comps
    f = "F" in comps
    if fd and m:
      return 2 # M/FD
    elif fd and f:
      return 3 # F/FD
    elif fd:
      return 1 # FD
    else:
      return 0

def getComponentsValue(comp):
    idx = comp.find('(')
    if idx > 0:
      comp = comp[idx+1:].strip()
    else:
      return ""
    
    if comp.endswith(')'):
      comp = comp[:-1]
    # ugly fixes
    idx = comp.find('une goutte de sang du lanceur')
    if idx > 0:
      return comp[idx].strip()
    else:
      return comp

def getCasterFullName(abbr):
  return abbr

  if abbr == 'Alc':
    return "Alchimiste"
  elif abbr == 'Ant':
    return "Antipaladin"
  elif abbr == 'Bar':
    return "Barde"
  elif abbr == 'Chm':
    return "Chaman"
  elif abbr == 'Con':
    return "Conjurateur"
  elif abbr == 'Dru':
    return "Druide"
  elif abbr == 'Ens':
    return "Ensorceleur"
  elif abbr == 'Mag':
    return "Magicien"
  elif abbr == 'Mgs':
    return "Magus"
  elif abbr == 'Méd':
    return "Médium"
  elif abbr == 'Hyp':
    return "Hypnotiseur"
  elif abbr == 'Inq':
    return "Inquisiteur"
  elif abbr == 'Occ':
    return "Occultiste"
  elif abbr == 'Pal':
    return "Paladin"
  elif abbr == 'Prê':
    return "Prêtre"
  elif abbr == 'Ora':
    return "Oracle"
  elif abbr == 'Psy':
    return "Psychiste"
  elif abbr == 'Rôd':
    return "Rôdeur"
  elif abbr == 'San':
    return "Sanguin"
  elif abbr == 'Sor':
    return "Sorcière"
  elif abbr == 'Spi':
    return "Spirite"
  
  print("Abbrevation not known: %s" % abbr)
  exit(1)
  

def generateLearnAt(niveau):
    classes = []
    regex = re.compile('[\w/]+ \d')
    for match in regex.findall(niveau):
      el = re.search('([\w/]+) (\d)', match)
      casters = el.group(1)
      level = int(el.group(2))
      el = re.search('(\w+)/(\w+)', casters)
      if el:
        classes.append([getCasterFullName(el.group(1)), level])
        classes.append([getCasterFullName(el.group(2)), level])
      else:
        classes.append([getCasterFullName(casters), level])
      
    learnAt = {
      "class": classes,
      #"domain": [],
      #"subDomain": [],
      #"elementalSchool": [],
      #"bloodline": []
    }
    return learnAt;

SCHOOLS = { 'abjuration': 'abj', 'divination': 'div', 'enchantement': 'enc', 'évocation': 'evo', 'illusion': 'ill', 
           'invocation': 'con', 'nécromancie': 'nec', 'transmutation': 'trs', 'universel': 'uni', 'ultimate': 'trs' }

list = []
duplicates = []
for s in data:
    if s['Nom'] in duplicates:
        print("Ignoring duplicate: " + s['Nom'])
        continue
    duplicates.append(s['Nom'])
        
    comps = getComponents(s['Composantes']) if 'Composantes' in s else []
    divineFocus = getComponentsFD(comps)
    
    name = cleanTitle(s['Nom'])
    description = s['DescriptionHTML'] if 'DescriptionHTML' in s else s['Description'].replace("\n", "<br/>")
    description = generateDescriptionHTML(name, description, s['Référence'])
    
    el = {
        "name": name,
        "permission": {
            "default": 0
        },
        "type": "spell",
        "data": {
            "description": {  ## based on PF1 spell template
               "value": ("<div class=\"spell-description\">" +
                         "<p>" +
                            "<strong>École</strong>&nbsp;{}; " +
                            "<strong>Niveau</strong>&nbsp;{}; " +
                         "</p>" +
                         "<p>" +
                            "<strong>Temps d'incantation</strong>&nbsp;{}<br> " +
                            "<strong>Composants</strong>&nbsp;{}<br/> " +
                         "</p>" +
                         "<p>" +
                            "<strong>Portée</strong>&nbsp;{}<br> " +
                            "<strong>Cibles</strong>&nbsp;{}<br> " +
                            "<strong>Durée</strong>&nbsp;{}<br> " +
                            "<strong>Jet de sauvegarde</strong>&nbsp;{}; " +
                            "<strong>Résistance à la magie</strong>&nbsp;{}<br>" +
                         "</p>" +
                         "<h2>Description</h2>{}" +
                         "</div>").format(
                    cleanValue(s['École']) if 'École' in s else '-',
                    s['Niveau'],
                    cleanValue(s['Temps d\'incantation']) if 'Temps d\'incantation' in s else '-',
                    cleanValue(s['Composantes']) if 'Composantes' in s else '-',
                    cleanValue(s['Portée']) if 'Portée' in s else '-',
                    cleanValue(s['Cible ou zone d\'effet']) if 'Cible ou zone d\'effet' in s else '-',
                    cleanValue(s['Durée']) if 'Durée' in s else '-',
                    cleanValue(s['Jet de sauvegarde']) if 'Jet de sauvegarde' in s else '-',
                    cleanValue(s['Résistance à la magie']) if 'Résistance à la magie' in s else '-',
                    description),
                "chat": "",
                "unidentified": ""                    
            },
            "source": s['Source'],
            "activation": getActivation(s['Temps d\'incantation']) if 'Temps d\'incantation' in s else None,
            "duration": {
                "value": None,
                "units": ""
            },
            "target": {
                "value": s['Cible ou zone d\'effet'] if 'Cible ou zone d\'effet' in s else '-'
            },
            "range": getRange(s['Portée']) if 'Portée' in s else None,
            "uses": {
                "value": 0,
                "max": 0,
                "per": None
            },
            "actionType": None,
            "attackBonus": "",
            "critConfirmBonus": "",
            "damage": {
                "parts": []
            },
            "attackParts": [],
            "formula": "",
            "ability": {
            "attack": None,
            "damage": "",
            "damageMult": 1,
            "critRange": 20,
            "critMult": 2
            },
            "save": {
                "dc": "0",
                "description": cleanValue(s['Jet de sauvegarde']) if 'Jet de sauvegarde' in s else '-',
                "type": None
            },
            "effectNotes": "",
            "attackNotes": "",
            "learnedAt": generateLearnAt(s['Niveau']),
            "level": getLevel(s['Niveau']),
            "clOffset": 0,
            "slOffset": 0,
            "school": SCHOOLS[getSchool(s['École'])] if 'École' in s else "",
            "subschool": getSubSchool(s['École']) if 'École' in s else "",
            "types": getTypes(s['École']) if 'École' in s else "",
            "components": {
                "value": "",
                "verbal": 'V' in comps,
                "somatic": 'G' in comps or 'S' in comps,
                "material": 'M' in comps,
                "focus": 'F' in comps or 'FD' in comps,
                "divineFocus": divineFocus
            },
            "castTime": s['Temps d\'incantation'] if 'Temps d\'incantation' in s else '-',
            "materials": {
                "value": "",
                "consumed": False,
                "focus": "",
                "cost": 0,
                "supply": 0
            },
            "spellbook": "primary",
            "preparation": {
                "mode": "prepared",
                "preparedAmount": 0,
                "maxAmount": 0
            },
            "sr": True if 'Résistance à la magie' in s and "oui" in s['Résistance à la magie'].lower() else False,
            "shortDescription": description,
            "spellDuration": s['Durée'] if 'Durée' in s else '-',
            "spellEffect": "",
            "spellArea": "",
            "attack": {
            "parts": []
            },
            "weaponData": {
            "critRange": 20,
            "critMult": 2
            }
        },
        "sort": 100001,
        "flags": {}
    }
    
    school = SCHOOLS[getSchool(s['École'])] if 'École' in s else ""
    if school == "abj":
      el["img"] = "systems/pf1/icons/spells/protect-sky-2.jpg"
    elif school == "con":
      el["img"] = "systems/pf1/icons/spells/wild-orange-2.jpg"
    elif school == "div":
      el["img"] = "systems/pf1/icons/spells/evil-eye-eerie-1.jpg"
    elif school == "enc":
      el["img"] = "systems/pf1/icons/spells/wind-grasp-air-2.jpg"
    elif school == "evo":
      el["img"] = "systems/pf1/icons/spells/fire-arrows-2.jpg"
    elif school == "ill":
      el["img"] = "systems/pf1/icons/spells/fog-blue-3.jpg"
    elif school == "nec":
      el["img"] = "systems/pf1/icons/spells/horror-eerie-2.jpg"
    elif school == "trs":
      el["img"] = "systems/pf1/icons/spells/vines-eerie-1.jpg"
    else:
      el["img"] = "systems/pf1/icons/spells/air-burst-air-2.jpg"
    
    list.append(el)

list = mergeWithLetContribute(list, "letscontribute/spellsfr.json")

# écrire le résultat dans le fichier d'origine
outFile = open("data/spells.json", "w")
outFile.write(json.dumps(list, indent=3))
