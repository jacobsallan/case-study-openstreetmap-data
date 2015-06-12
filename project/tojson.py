#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
from collections import defaultdict
import pprint
import re
import codecs
import json
"""
Your task is to wrangle the data, fix the street names, and transform the shape of the data
into the model we mentioned earlier. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB. 

Note that in this exercise we do not use the 'update street name' procedures
you worked on in the previous exercise. If you are using this code in your final
project, you are strongly encouraged to use the code from previous exercise to 
update the street names before you save them to JSON. 

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if second level tag "k" value contains problematic characters, it should be ignored
- if second level tag "k" name is 'address', it should be ignored
- if second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if second level tag "k" value does not start with "addr:", but contains ":", you can process it
  same as any other tag.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]
"""


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected = ["Street", "Avenue", "Boulevard", "Drive", "Circle", "Corner", "Court", "Place",
            "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Freeway", "Terrace", "Trail", "Interchange",
            "Center", "Highway", "Intersection", "Place", "View", "Way"]

mapping = { "St": "Street",
            "St.": "Street",
            "Str": "Street",
            "str": "Street",
            "street": "Street",
            "Ci" : "Circle",
            "Cir" : "Circle",
            "Cnr" : "Corner",
            "Cr" : "Circle",
            "ct." : "Court",
            "Ct" : "Court",
            "Alicia Pkwy @ Via Linda" : "Alicia Parkway @ Via Linda",
            "Blvd & Citrus Ave" : "Boulevard & Citrus Avenue",
            "Orangethorpe Av @ Magnolia Av" : "Orangethorpe Avenue @ Magnolia Avenue",
            "Gothard  St @ Center Ave Ne" : "Gothard Street @ Center Avenue NE",
            "9004 Lakewood Blvd: Nw Quad I-5 / Lakewood (Sr 19) Ic Off Vista Del Rosa St" : "9004 Lakewood Boulevard: NW Quad I-5 / Lakewood (Sr 19) Ic Off Vista Del Rosa Street",
            "4980 Sweetgrass Ln Riverview Evangelical Church" : "4980 Sweetgrass Lane Riverview Evangelical Church",
            "Western Ave # O" : "Western Avenue # O",
            "RAVENSWOOD PL" : "Ravenswood Place",
            "SOUTH BREEZY WAY" : "South Breezy Way",
            "Pine grove road" : "Pine Grove Road",
            "Se Cnr Sr 55 & Lincoln Av" : "SE Corner Sr 55 & Lincoln Avenue",
            "W 6TH ST" : "W 6th Street",
            "Aven": "Avenue",
            "Ave": "Avenue",
            "ave": "Avenue",
            "Av": "Avenue",
            "Rd. at Telephone Rd." : "Road at Telephone Road",
            "Rd" : "Road",
            "Rd." : "Road",
            "Pky" : "Parkway",
            "Pkwy" : "Parkway",
            "Pkwy." : "Parkway",
            "Dr"  : "Drive",
            "Dr."  : "Drive",
            "Bl" : "Boulevard",
            "blvd" : "Boulevard",
            "Blv" : "Boulevard",
            "Bl." : "Boulevard",
            "Bd." : "Boulevard",
            "Bvd" : "Boulevard",
            "Blvd" : "Boulevard",
            "Blvd." : "Boulevard",
            "Ln." : "Lane",
            "Ln" : "Lane",
            "Ave Ne" : "Avenue NE",
            "Ave #0" : "Avenue #0",
            "Te" : "Terrace",
            "Tl" : "Trail",
            "Tr" : "Trail",
            "Ave Ic" : "Avenue Interchange",
            "Dr Ic" : "Drive Interchange",
            "Rd Ic" : "Road Interchange",
            "Ic" : "Interchange",
            "Str Int" : "Street Intersection",
            "Int" : "Intersection",
            "Ctr" : "Center",
            "Hwy" : "Highway",
            "Pl" : "Place",
            "Vw" : "View",
            "way" : "Way",
            "Wa" : "Way",
            "Wy" : "Way"
            }

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def is_name(elem):
    return (elem.attrib['k'] == "name")

def update_name(name, mapping):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type in mapping:
            name = name[0:len(name)-len(street_type)] + mapping[street_type]
#    if name.find('N') == 0 and name.find('N Street') == -1:
#        name = 'North ' + name[2:]
#    elif name.find('N. ') == 0:
#        name = 'North ' + name[3:]
#    elif name.find('S') == 0 and name.find('S Street') == -1:
#        name = 'South ' + name[2:]
#    elif name.find('S. ') == 0:
#        name = 'South ' + name[3:]
#    elif name.find('E') == 0 and name.find('E Street') == -1:
#        name = 'East ' + name[2:]
#    elif name.find('E. ') == 0:
#        name = 'East ' + name[3:]
#    elif name.find('W') == 0 and name.find('W Street') == -1:
#        name = 'West ' + name[2:]
#    elif name.find('W. ') == 0:
#        name = 'West ' + name[3:]
    return name

def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        node['type'] = element.tag
        for a in element.attrib:
            if a == "lat":
                if 'pos' not in node:
                    node['pos'] = [0.0, 0.0]
                node['pos'][0] = float(element.attrib['lat'])
            elif a == 'lon':
                if 'pos' not in node:
                    node['pos'] = [0.0, 0.0]
                node['pos'][1] = float(element.attrib['lon'])
            elif a in CREATED:
                if 'created' not in node:
                    node['created'] = {}
                node['created'][a] = element.attrib[a]
        for c in element.iter('tag'):
            direction = ""
            if 'k' in c.attrib:
                kvalue = c.attrib['k'].strip()
                if not problemchars.search(kvalue):
                    if kvalue[0:5] == 'addr:':
                        if kvalue.find(':', 5) == -1:
                            if 'address' not in node:
                                node['address'] = {}
                            if kvalue[5:] == 'street':
                                v = update_name(c.attrib['v'], mapping)
                                if direction == "":
                                    node['address']['street'] = unicode(v)
                                else:
                                    node['address']['street'] = direction + ' ' + unicode(v)
                            elif kvalue[5:] == 'street_direction_prefix':
                                direction = c.attrib['v'].strip()
                                if 'street' in node['address']:
                                    node['address']['street'] = direction + ' ' + node['address']['street']
                            elif kvalue[5:] == 'postcode':
                                v = c.attrib['v']
                                if v != '722A':
                                    if v[0:3] == 'CA ':
                                        v = v[4:]
                                    elif v[0] != '9':
                                        v = '9' + v[1:]
                                    node['address']['postcode'] = unicode(v)
                            elif kvalue[5:] == 'housenumber':
                                v = c.attrib['v']
                                if v == '2475 Adriatic Ave.':
                                    node['address']['street'] = 'Adriatic Avenue'
                                    node['address']['housenumber'] = '2475'
                                elif v == '18744 Via Princessa':
                                    node['address']['street'] = 'Via Princessa'
                                    node['address']['housenumber'] = '18744'
                                elif v == '1850 Sawtelle Boulevard, Suite 300, Los Angeles, CA 90025':
                                    node['address']['street'] = 'Sawtelle Boulevard'
                                    node['address']['housenumber'] = '1850 (Suite 300)'
                                    node['address']['city'] = 'Los Angeles'
                                    node['address']['postcode'] = '90025'
                                elif v == '2660 Park Center Drive':
                                    node['address']['housenumber'] = unicode(v)
                                elif v == '39252 Winchester Rd Murrieta, CA 92563':
                                    node['address']['housenumber'] = '39252'
                                    node['address']['street'] = 'Winchester Road'
                                    node['address']['city'] = 'Murrieta'
                                    node['address']['postcode'] = '92563'
                                else:
                                    node['address']['housenumber'] = unicode(v)
                            else:
                                v = c.attrib['v']
                                node['address'][kvalue[5:]] = unicode(v)
                    elif kvalue == 'name' and element.tag == 'way':
                        v = update_name(c.attrib['v'], mapping)
                        node[kvalue] = v
                    elif kvalue[0:6] == 'tiger:':
                        if 'tiger' not in node:
                            node['tiger'] = {}
                        v = c.attrib['v']
                        node['tiger'][kvalue[6:]] = unicode(v)
                    elif kvalue != 'address':
                        node[kvalue] = c.attrib['v']
                    else:
                        node[a] = element.attrib[a]
        for c in element.iter('nd'):
            if 'ref' in c.attrib:
                rvalue = c.attrib['ref']
                if 'node_refs' not in node:
                    node['node_refs'] = []
                node['node_refs'].append(rvalue)
        element.clear()
        return node
    else:
        return None


def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def test():
    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.
    data = process_map('los-angeles_california.osm', False)
#   pprint.pprint(data)
    
#    assert data[0] == {
#                        "id": "261114295", 
#                        "visible": "true", 
#                        "type": "node", 
#                        "pos": [
#                          41.9730791, 
#                          -87.6866303
#                        ], 
#                        "created": {
##                          "changeset": "11129782", 
#                          "user": "bbmiller", 
#                          "version": "7", 
#                          "uid": "451048", 
#                          "timestamp": "2012-03-28T18:31:23Z"
#                        }
#                      }
#    assert data[-1]["address"] == {
#                                    "street": "West Lexington St.", 
#                                    "housenumber": "1412"
#                                      }
#    assert data[-1]["node_refs"] == [ "2199822281", "2199822390",  "2199822392", "2199822369", 
#                                    "2199822370", "2199822284", "2199822281"]

if __name__ == "__main__":
    test()
