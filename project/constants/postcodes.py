"""
Constants for 'unknown' postcodes
These are Office for National Statistics (ONS) codes for where a postcode is not known
ZZ99 3VZ No fixed abode 
ZZ99 3CZ England/U.K  not otherwise specified 
ZZ99 3GZ Wales not otherwise specified 
ZZ99 1WZ Scotland not otherwise specified
ZZ99 2WZ Northern Ireland not otherwise specified

https://www.datadictionary.wales.nhs.uk/index.html#!worddocuments/postcode.htm
"""

UNKNOWN_POSTCODES_NO_SPACES = [
    "ZZ993VZ",
    "ZZ993CZ",
    "ZZ993GZ",
    "ZZ991WZ",
    "ZZ992WZ"
]


"""
Special NHS postcodes for countries that have reciprocal healthcare agreements with the UK
https://www.datadictionary.wales.nhs.uk/index.html#!worddocuments/administrativecategory.htm
"""
RECIPROCAL_POSTCODES_NO_SPACES = [
    "ZZ994MZ",  # Austria
    "ZZ992DZ",  # Belgium
    "ZZ994UZ",  # Bulgaria
    "ZZ996AZ",  # Cyprus
    "ZZ994FZ",  # Denmark
    "ZZ997LZ",  # Estonia
    "ZZ994BZ",  # Finland
    "ZZ994GZ",  # France
    "ZZ994QZ",  # Germany
    "ZZ994RZ",  # Greece
    "ZZ994CZ",  # Iceland
    "ZZ993AZ",  # Ireland
    "ZZ994LZ",  # Italy
    "ZZ997RZ",  # Latvia
    "ZZ992PZ",  # Liechtenstein
    "ZZ997SZ",  # Lithuania
    "ZZ992EZ",  # Luxembourg
    "ZZ994EZ",  # Netherlands
    "ZZ992AZ",  # Norway
    "ZZ994JZ",  # Portugal
    "ZZ994ZZ",  # Romania
    "ZZ994HZ",  # Spain
    "ZZ992CZ",  # Sweden
    "ZZ994PZ",  # Switzerland
    "ZZ996RZ",  # Anguilla
    "ZZ997JZ",  # Armenia
    "ZZ996GZ",  # Australia
    "ZZ997KZ",  # Azerbaijan
    "ZZ996MZ",  # Barbados
    "ZZ997MZ",  # Belarus
    "ZZ995NZ",  # Bosnia and Herzegovina
    "ZZ996RZ",  # British Virgin Islands
    "ZZ993HZ",  # Channel Islands
    "ZZ995VZ",  # Croatia
    "ZZ995XZ",  # Czech Republic
    "ZZ996UZ",  # Falkland Islands
    "ZZ997NZ",  # Georgia
    "ZZ995AZ",  # Gibraltar
    "ZZ994XZ",  # Hungary
    "ZZ994CZ",  # Iceland
    "ZZ993BZ",  # Isle of Man
    "ZZ997PZ",  # Kazakhstan
    "ZZ997QZ",  # Kyrgyzstan
    "ZZ995QZ",  # Macedonia
    "ZZ995BZ",  # Malta
    "ZZ999TZ",  # Moldova
    "ZZ996RZ",  # Montserrat
    "ZZ996HZ",  # New Zealand
    "ZZ994YZ",  # Poland
    "ZZ997UZ",  # Russia
    "ZZ995UZ",  # Slovenia
    "ZZ996UZ",  # St. Helena
    "ZZ999SZ",  # Serbia and Montenegro
    "ZZ997VZ",  # Tajikistan
    "ZZ997XZ",  # Turkmenistan
    "ZZ996RZ",  # Turks and Caicos Islands
    "ZZ997YZ",  # Ukraine
    "ZZ997ZZ",  # Uzbekistan
]

def skip_api_validation_for_postcode(postcode):
    to_check = postcode.replace(" ", "").upper()
    return to_check in UNKNOWN_POSTCODES_NO_SPACES or to_check in RECIPROCAL_POSTCODES_NO_SPACES