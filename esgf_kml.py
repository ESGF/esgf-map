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

# Get lon/lat coordinates for each institution or consortia partner
# Get country for each institution or consortia partner
coordinates = {}
countries = {}
try:
    for institution in cmip6.institution_id.terms:
        if 'postalAddress' in institution.data.keys() and institution.data['postalAddress']:
            coordinates[institution.label] = _get_location_coordinates(institution.data['postalAddress'])
            countries[institution.label] = _get_location_country(institution.data['postalAddress'])
            print 'Get coordinates for {} :: {} :: {}'.format(institution.label,
                                                              countries[institution.label],
                                                              coordinates[institution.label])
        if 'consortia' in institution.data.keys() and institution.data['consortia']:
            for consortia in institution.data['consortia']:
                if 'postalAddress' in consortia.keys() and consortia['postalAddress']:
                    coordinates[consortia['code']] = _get_location_coordinates(consortia['postalAddress'])
                    countries[consortia['code']] = _get_location_country(consortia['postalAddress'])
                    print 'Get coordinates for {} :: {} :: {}'.format(consortia['code'],
                                                                      countries[consortia['code']],
                                                                      coordinates[consortia['code']])
except:
    # 'Time out' error could occur depending on the geolocator API used
    if os.path.exists('coordinates.pydata'):
        with open('coordinates.pydata', 'r') as f:
            coordinates = pickle.load(f)
            countries = pickle.load(f)
    else:
        print 'No coordinates data found.'
        exit(1)

print 'Save countries and coordinates'
with open('coordinates.pydata', 'w') as f:
    pickle.dump(coordinates, f)
    pickle.dump(countries, f)

#with open('coordinates.pydata', 'r') as f:
#   coordinates = pickle.load(f)
#   countries = pickle.load(f)

# Create KML documentation
print 'Create KML document'
doc = KML.kml(
    KML.Document(
        KML.Name('CMIP6 contribution'),
    )
)

print 'Add icon styles for institution countries'
with open('flags.txt', 'r') as f:
    flags = f.read().splitlines()
for country in countries.values():
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
# Add icon styles for institution countries
for institution in cmip6.institution_id.terms:
    if 'postalAddress' in institution.data.keys() and institution.data['postalAddress']:
        doc.Document.append(
            KML.Placemark(
                KML.name(institution.label),
                KML.description(institution.data['name']),
                KML.styleUrl('#icon_{}'.format(countries[institution.label])),
                KML.Point(
                    KML.coordinates(coordinates[institution.label])
                )
            )
        )

    if 'consortia' in institution.data.keys() and institution.data['consortia']:
        for consortia in institution.data['consortia']:
            if 'postalAddress' in consortia.keys() and consortia['postalAddress']:
                doc.Document.append(
                    KML.Placemark(
                        KML.name(consortia['code']),
                        KML.description(consortia['name']),
                        KML.styleUrl('#icon_{}'.format(countries[consortia['code']])),
                        KML.Point(
                            KML.coordinates(coordinates[consortia['code']])
                        )
                    )
                )

print 'Write KML file'
with open('CMIP6_contribution.kml', 'w') as f:
    f.write(etree.tostring(doc, pretty_print=True))
