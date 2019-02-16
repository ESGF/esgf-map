import os
import pickle

import pyessv
from geopy.geocoders import Nominatim
from lxml import etree
from pykml.factory import KML_ElementMaker as KML


def _get_location_coordinates(address):
    """
    Geocoding postal address to get lon/lat coordinates

    """
    geolocator = Nominatim()
    location = geolocator.geocode(address)
    while location is None:
        address = ','.join(address.split(',')[1:]).strip()
        location = geolocator.geocode(address)
    return "{},{}".format(location.longitude, location.latitude)


def _get_location_country(address):
    """
    Split postal address to get country name only

    """
    return address.split(',')[-1].lower().strip().replace('_', '-').replace(' ', '-')


# Get WCRP CMIP6 CV
cmip6 = pyessv.load('wcrp:cmip6')

# Get placemarks
if os.path.exists('placemarks.pydata'):
    with open('placemarks.pydata', 'r') as f:
        placemarks = pickle.load(f)
else:
    print "Get lon/lat coordinates for each institution or consortia partner"
    placemarks = {}
    for institution in cmip6.institution_id.terms:
        if 'postalAddress' in institution.data.keys() and institution.data['postalAddress']:
            placemarks[institution.label] = {}
            placemarks[institution.label]['address'] = institution.data['postalAddress']
            placemarks[institution.label]['country'] = _get_location_country(institution.data['postalAddress'])
            placemarks[institution.label]['coordinates'] = _get_location_coordinates(institution.data['postalAddress'])
            placemarks[institution.label]['description'] = institution.data['name']

        if 'consortia' in institution.data.keys() and institution.data['consortia']:
            for consortia in institution.data['consortia']:
                if 'postalAddress' in consortia.keys() and consortia['postalAddress']:
                    placemarks[consortia['code']] = {}
                    placemarks[consortia['code']]['address'] = consortia['postalAddress']
                    placemarks[consortia['code']]['country'] = _get_location_country(consortia['postalAddress'])
                    placemarks[consortia['code']]['coordinates'] = _get_location_coordinates(consortia['postalAddress'])
                    placemarks[consortia['code']]['description'] = consortia['name']
    print 'Save placemarks'
    with open('placemarks.pydata', 'w') as f:
        pickle.dump(placemarks, f)

print 'Create KML document'
doc = KML.kml(
    KML.Document(
        KML.Name('CMIP6 contribution'),
    )
)

print 'Add icon styles for institution countries'
with open('flags.txt', 'r') as f:
    flags = f.read().splitlines()
for country in [placemarks[placemark]['country'] for placemark in placemarks]:
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

print 'Add a KML Placemark for each institution or consortia partner'
for placemark in sorted(placemarks.keys()):
    doc.Document.append(
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

print 'Write KML file'
with open('CMIP6_contribution.kml', 'w') as f:
    f.write(etree.tostring(doc, pretty_print=True))
