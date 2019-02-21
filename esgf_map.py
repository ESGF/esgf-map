import pyessv
from lxml import etree
import json
import os
from pykml.factory import KML_ElementMaker as KML

TEXT_ELEMENTS = ['description', 'text', 'linkDescription', 'displayName']

def getXmlWithCDATA(obj, cdata_elements):
  """
  Convert Objectify document to lxml.etree

  """
  root = etree.fromstring(etree.tostring(etree.ElementTree(obj)))
  # Create an xpath expression to search for all desired cdata elements
  xpath = '|'.join(map(lambda tag: '//kml:' + tag, cdata_elements))
  results = root.xpath(xpath, namespaces = {'kml': 'http://www.opengis.net/kml/2.2'})
  for element in results:
    element.text = etree.CDATA(element.text)
  return root

def _get_location_country(address):
    """
    Split postal address to get country name only

    """
    return address.split(',')[-1].lower().strip().replace('_', '-').replace(' ', '-')

# Load flag icon links
with open('flags.txt', 'r') as f:
    flags = f.read().splitlines()

# Start
print 'Create KML document'
doc = KML.kml(
    KML.Document(
        KML.Name('ESGF Map'),
    )
)

###################
# ESGF Placemarks #
###################

# Get node infos
with open(os.path.join(os.path.dirname(__file__), 'esgf_partners.json')) as f:
    NODES_DATA = json.loads(f.read())
    NODES_DATA = {i['code']: i for i in NODES_DATA}

# Get placemarks
print "Get ESGF placemarks"
placemarks = {}
for institution in NODES_DATA:
    node = NODES_DATA[institution]
    placemarks[node['code']] = {}
    placemarks[node['code']]['coordinates'] = node['coordinates']
    placemarks[node['code']]['index'] = node['tier1']
    placemarks[node['code']]['country'] = _get_location_country(node['postalAddress'])
    placemarks[node['code']]['description'] = '<a href="{}">{}</a>'.format(
        node['homepage'],
        node['name'])

# Get ESGF countries
countries = [placemarks[placemark]['country'] for placemark in placemarks]

# Create ESGF KML Folders for different layers
index = KML.Folder(KML.name('ESGF Full Nodes'))
data = KML.Folder(KML.name('ESGF Data-only Nodes'))

print 'Add ESGF KML Placemarks for each institution or consortia partner'
for placemark in sorted(placemarks.keys()):
    if placemarks[placemark]['index']:
        index.append(
            KML.Placemark(
                KML.name(placemark),
                KML.description(placemarks[placemark]['description']),
                KML.styleUrl('#icon_{}'.format(placemarks[placemark]['country'])),
                KML.Point(
                    KML.coordinates(
                        placemarks[placemark]['coordinates']
                    )
                )
            )
        )
    else:
        data.append(
            KML.Placemark(
                KML.name(placemark),
                KML.description(placemarks[placemark]['description']),
                KML.styleUrl('#icon_{}'.format(placemarks[placemark]['country'])),
                KML.Point(
                    KML.coordinates(
                        placemarks[placemark]['coordinates']
                    )
                )
            )
        )


####################
# CMIP6 Placemarks #
####################

# Get WCRP CMIP6 CV
cmip6 = pyessv.load('wcrp:cmip6')

# Get placemarks
print "Get CMIP6 placemarks"
placemarks = {}
for institution in cmip6.institution_id.terms:
    if 'consortia' in institution.data.keys() and institution.data['consortia']:
        for consortia in institution.data['consortia']:
            if 'postalAddress' in consortia.keys() and consortia['postalAddress']:
                placemarks[consortia['code']] = {}
                placemarks[consortia['code']]['coordinates'] = consortia['coordinates']
                placemarks[consortia['code']]['country'] = _get_location_country(consortia['postalAddress'])
                placemarks[consortia['code']]['description'] = '<a href="{}">{}</a>'.format(
                    consortia['homepage'],
                    consortia['name'])
    else:
        if 'postalAddress' in institution.data.keys() and institution.data['postalAddress']:
            placemarks[institution.label] = {}
            placemarks[institution.label]['coordinates'] = institution.data['coordinates']
            placemarks[institution.label]['country'] = _get_location_country(institution.data['postalAddress'])
            placemarks[institution.label]['description'] = '<a href="{}">{}</a>'.format(
                    institution.data['homepage'],
                    institution.data['name'])

# Extend countries with CMIP6
countries.extend([placemarks[placemark]['country'] for placemark in placemarks])

# Create CMIP6 KML Folder for new layer
cmip6 = KML.Folder(KML.name('CMIP6 contributors'))

print 'Add CMIP6 KML Placemarks for each institution or consortia partner'
for placemark in sorted(placemarks.keys()):
    print "{} :: {} :: {}".format(placemark, placemarks[placemark]['country'], placemarks[placemark]['description'])
    cmip6.append(
        KML.Placemark(
            KML.name(placemark),
            KML.description(placemarks[placemark]['description']),
            KML.styleUrl('#icon_{}'.format(placemarks[placemark]['country'])),
            KML.Point(
                KML.coordinates(
                    placemarks[placemark]['coordinates']
                )
            )
        )
    )

###############
# Icon Styles #
###############

print 'Add icon styles for institution countries'
for country in set(countries):
    res = [link for link in flags if '/{}.png'.format(country) in link]
    if not res:
        print 'No flag found for {}'.format(country)
    else:
        doc.Document.append(
            KML.Style(
                KML.IconStyle(
                    KML.Icon(
                        KML.href([link for link in flags if '/{}.png'.format(country) in link][0]),
                    )
                ),
                id='icon_{}'.format(country)
            )
        )

#############
# Final KML #
#############

print 'Append placemarks into KML document'
doc.Document.append(index)
doc.Document.append(data)
doc.Document.append(cmip6)

doc = getXmlWithCDATA(doc, TEXT_ELEMENTS)
print 'Write KML file'
with open('ESGF_Map.kml', 'w') as f:
    f.write(etree.tostring(doc, pretty_print=True))
