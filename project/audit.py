"""
Your task in this exercise has two steps:

- audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix 
    the unexpected street types to the appropriate ones in the expected list.
    You have to add mappings only for the actual problems you find in this OSMFILE,
    not a generalized solution, since that may and will depend on the particular area you are auditing.
- write the update_name function, to actually fix the street name.
    The function takes a string with street name as an argument and should return the fixed name
    We have provided a simple test so that you see what exactly is expected
"""
import xml.etree.ElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "los-angeles_california.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected = ["Street", "Avenue", "Boulevard", "Drive", "Circle", "Corner", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Freeway", "Terrace", "Trail", "Interchange",
            "Center", "Highway", "Intersection", "Place", "View", "Way"]

# UPDATE THIS VARIABLE
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


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name.strip())

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def is_name(elem):
    return (elem.attrib['k'] == "name")

def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
                if is_name(tag) and elem.tag == "way":
                    audit_street_type(street_types, tag.attrib['v'])
        elem.clear()
    return street_types


def update_name(name, mapping):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type in mapping:
            name = name[0:len(name)-len(street_type)] + mapping[street_type]
            
    return name


def test():
    st_types = audit(OSMFILE)
#    assert len(st_types) == 3
    pprint.pprint(dict(st_types))

    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name, mapping)
            print name.encode('utf-8'), "=>", better_name.encode('utf-8')


if __name__ == '__main__':
    test()
