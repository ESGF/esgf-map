from lxml import etree
from geopy.geocoders import Nominatim, GoogleV3
from pykml.factory import KML_ElementMaker as KML
import pyessv


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
    return address.split(',')[-1].lower().strip().replace('_','-').replace(' ', '-')


# Get WCRP CMIP6 CV
cmip6 = pyessv.load('wcrp:cmip6')

# Get lon/lat coordinates for each institution or consortia partner
# Get country for each institution or consortia partner
coordinates = {}
countries = {}
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


# Create KML documentation
print "Create KML document"
doc = KML.kml(
        KML.Document(
            KML.Name("CMIP6 contribution"),
            KML.Folder(),
        )
    )

print "Add icon styles for institution countries"
for country in countries.values():
    doc.Document(
        KML.Style(
            KML.IconStyle(
                KML.Icon(
                    KML.href("http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png")
               ),
            ),
        )
    )


# Add a KML Placemark for each institution or consortia partner
for institution in cmip6.institution_id.terms:
    if 'postalAddress' in institution.data.keys() and institution.data['postalAddress']:
        doc.Document.Folder.append(
            KML.Placemark(
                KML.name(institution.label),
                KML.Point(
                    KML.coordinates(
                        _get_location_coordinates(institution.label, institution.data['postalAddress'])
                    )
                )
            )
        )

    if 'consortia' in institution.data.keys() and institution.data['consortia']:
        for consortia in institution.data['consortia']:
            if 'postalAddress' in consortia.keys() and consortia['postalAddress']:
                doc.Document.Folder.append(
                    KML.Placemark(
                        KML.name(consortia['code']),
                        KML.Point(
                            KML.coordinates(
                                _get_location_coordinates(consortia['code'], consortia['postalAddress'])
                            )

                        )
                    )
                )

# Write KML file
with open('CMIP6_contribution.kml', 'w') as f:
    f.write(etree.tostring(doc, pretty_print=True))

