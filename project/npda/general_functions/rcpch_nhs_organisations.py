"""
This module contains functions that are used to extract NHS organisations from the RCPCH dataset.
"""

# python imports
import requests

# django imports
from django.conf import settings
from requests.exceptions import HTTPError

# RCPCH imports


def get_nhs_organisation(ods_code: str):
    """
    This function returns details of an NHS organisation against an ODS code from the RCPCH dataset.
    """

    url = (
        f"{settings.RCPCH_NHS_ORGANISATIONS_API_URL}/organisations/?ods_code={ods_code}"
    )

    try:
        response = requests.get(
            url=url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)
        raise Exception(f"{ods_code} not found")

    return response.json()[0]


def get_all_nhs_organisations():
    """
    This function returns all NHS organisations from the RCPCH dataset and returns them to the caller as a list of tuples.
    These are typically used in Django forms as choices.
    """

    url = f"{settings.RCPCH_NHS_ORGANISATIONS_API_URL}/organisations/limited"

    try:
        response = requests.get(
            url=url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)
        raise Exception("No NHS organisations found")

    # convert the response to choices list
    organisation_list = []
    for organisation in response.json():
        organisation_list.append(
            (organisation.get("ods_code"), organisation.get("name"))
        )
    return organisation_list


# [
#   {
#     "ods_code": "RGT01",
#     "name": "ADDENBROOKE'S HOSPITAL",
#     "website": "https://www.cuh.nhs.uk/",
#     "address1": "HILLS ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "01223 245151",
#     "city": "CAMBRIDGE",
#     "county": "CAMBRIDGESHIRE",
#     "latitude": 52.17513275,
#     "longitude": 0.140753239,
#     "postcode": "CB2 0QQ",
#     "geocode_coordinates": "SRID=27700;POINT (0.140753239 52.17513275)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ041"
#     },
#     "trust": {
#       "ods_code": "RGT",
#       "name": "CAMBRIDGE UNIVERSITY HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "CAMBRIDGE BIOMEDICAL CAMPUS",
#       "address_line_2": "HILLS ROAD",
#       "town": "CAMBRIDGE",
#       "postcode": "CB2 0QQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000056",
#       "name": "NHS Cambridgeshire and Peterborough Integrated Care Board",
#       "ods_code": "QUE"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RCF22",
#     "name": "AIREDALE GENERAL HOSPITAL",
#     "website": "https://www.airedaletrust.nhs.uk/",
#     "address1": "SKIPTON ROAD",
#     "address2": "STEETON",
#     "address3": "",
#     "telephone": "",
#     "city": "KEIGHLEY",
#     "county": "WEST YORKSHIRE",
#     "latitude": 53.8979454,
#     "longitude": -1.962710142,
#     "postcode": "BD20 6TD",
#     "geocode_coordinates": "SRID=27700;POINT (-1.962710142 53.8979454)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ047"
#     },
#     "trust": {
#       "ods_code": "RCF",
#       "name": "AIREDALE NHS FOUNDATION TRUST",
#       "address_line_1": "AIREDALE GENERAL HOSPITAL",
#       "address_line_2": "SKIPTON ROAD",
#       "town": "KEIGHLEY",
#       "postcode": "BD20 6TD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000054",
#       "name": "NHS West Yorkshire Integrated Care Board",
#       "ods_code": "QWO"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBS25",
#     "name": "ALDER HEY CHILDREN'S HOSPITAL",
#     "website": "http://www.alderhey.nhs.uk",
#     "address1": "ALDER HEY HOSPITAL",
#     "address2": "EATON ROAD",
#     "address3": "WEST DERBY",
#     "telephone": "",
#     "city": "LIVERPOOL",
#     "county": "MERSEYSIDE",
#     "latitude": 53.41930389,
#     "longitude": -2.897731543,
#     "postcode": "L12 2AP",
#     "geocode_coordinates": "SRID=27700;POINT (-2.897731543 53.41930389)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ074"
#     },
#     "trust": {
#       "ods_code": "RBS",
#       "name": "ALDER HEY CHILDREN'S NHS FOUNDATION TRUST",
#       "address_line_1": "ALDER HEY HOSPITAL",
#       "address_line_2": "EATON ROAD",
#       "town": "LIVERPOOL",
#       "postcode": "L12 2AP",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWP01",
#     "name": "ALEXANDRA HOSPITAL",
#     "website": null,
#     "address1": "WOODROW DRIVE",
#     "address2": null,
#     "address3": null,
#     "telephone": null,
#     "city": "REDDITCH",
#     "county": null,
#     "latitude": 52.279774,
#     "longitude": -1.912127,
#     "postcode": "B98 7UB",
#     "geocode_coordinates": "SRID=27700;POINT (-1.912127 52.279774)",
#     "active": true,
#     "published_at": "2000-04-01",
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ073"
#     },
#     "trust": {
#       "ods_code": "RWP",
#       "name": "WORCESTERSHIRE ACUTE HOSPITALS NHS TRUST",
#       "address_line_1": "WORCESTERSHIRE ROYAL HOSPITAL",
#       "address_line_2": "CHARLES HASTINGS WAY",
#       "town": "WORCESTER",
#       "postcode": "WR5 1DD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000019",
#       "name": "NHS Herefordshire and Worcestershire Integrated Care Board",
#       "ods_code": "QGH"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTFDJ",
#     "name": "ALNWICK INFIRMARY",
#     "website": "https://www.northumbria.nhs.uk/our-locations/alnwick-infirmary",
#     "address1": "INFIRMARY DRIVE",
#     "address2": "SOUTH ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "ALNWICK",
#     "county": "NORTHUMBERLAND",
#     "latitude": 55.41094208,
#     "longitude": -1.697199821,
#     "postcode": "NE66 2NS",
#     "geocode_coordinates": "SRID=27700;POINT (-1.697199821 55.41094208)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTF",
#       "name": "NORTHUMBRIA HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "NORTH TYNESIDE GENERAL HOSPITAL",
#       "address_line_2": "RAKE LANE",
#       "town": "NORTH SHIELDS",
#       "postcode": "NE29 8NH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXQ51",
#     "name": "AMERSHAM HOSPITAL",
#     "website": "http://www.buckshealthcare.nhs.uk/For%20patients%20and%20visitors/amersham-hospital.htm",
#     "address1": "WHIELDEN STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "AMERSHAM",
#     "county": "BUCKINGHAMSHIRE",
#     "latitude": 51.66300201,
#     "longitude": -0.621415079,
#     "postcode": "HP7 0JD",
#     "geocode_coordinates": "SRID=27700;POINT (-0.621415079 51.66300201)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RXQ",
#       "name": "BUCKINGHAMSHIRE HEALTHCARE NHS TRUST",
#       "address_line_1": "AMERSHAM HOSPITAL",
#       "address_line_2": "WHIELDEN STREET",
#       "town": "AMERSHAM",
#       "postcode": "HP7 0JD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000044",
#       "name": "NHS Buckinghamshire, Oxfordshire and Berkshire West Integrated Care Board",
#       "ods_code": "QU9"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBL14",
#     "name": "ARROWE PARK HOSPITAL",
#     "website": "http://www.wuth.nhs.uk",
#     "address1": "ARROWE PARK ROAD",
#     "address2": "",
#     "address3": "UPTON",
#     "telephone": "",
#     "city": "WIRRAL",
#     "county": "MERSEYSIDE",
#     "latitude": 53.36962891,
#     "longitude": -3.096800804,
#     "postcode": "CH49 5PE",
#     "geocode_coordinates": "SRID=27700;POINT (-3.096800804 53.36962891)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ170"
#     },
#     "trust": {
#       "ods_code": "RBL",
#       "name": "WIRRAL UNIVERSITY TEACHING HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "ARROWE PARK HOSPITAL",
#       "address_line_2": "ARROWE PARK ROAD",
#       "town": "WIRRAL",
#       "postcode": "CH49 5PE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTK02",
#     "name": "ASHFORD HOSPITAL",
#     "website": "http://www.ashfordstpeters.nhs.uk",
#     "address1": "LONDON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ASHFORD",
#     "county": "MIDDLESEX",
#     "latitude": 51.44402313,
#     "longitude": -0.472798347,
#     "postcode": "TW15 3AA",
#     "geocode_coordinates": "SRID=27700;POINT (-0.472798347 51.44402313)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTK",
#       "name": "ASHFORD AND ST PETER'S HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "ST PETERS HOSPITAL",
#       "address_line_2": "GUILDFORD ROAD",
#       "town": "CHERTSEY",
#       "postcode": "KT16 0PZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000063",
#       "name": "NHS Surrey Heartlands Integrated Care Board",
#       "ods_code": "QXU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RAL26",
#     "name": "BARNET HOSPITAL",
#     "website": "https://www.royalfree.nhs.uk/",
#     "address1": "WELLHOUSE LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BARNET",
#     "county": "HERTFORDSHIRE",
#     "latitude": 51.65072632,
#     "longitude": -0.214137778,
#     "postcode": "EN5 3DJ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.214137778 51.65072632)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ012"
#     },
#     "trust": {
#       "ods_code": "RAL",
#       "name": "ROYAL FREE LONDON NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL FREE HOSPITAL",
#       "address_line_2": "POND STREET",
#       "town": "LONDON",
#       "postcode": "NW3 2QG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RFFAA",
#     "name": "BARNSLEY HOSPITAL AND COMMUNITY PAEDIATRICS",
#     "website": "http://www.barnsleyhospital.nhs.uk",
#     "address1": "GAWBER ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BARNSLEY",
#     "county": "SOUTH YORKSHIRE",
#     "latitude": 53.55913544,
#     "longitude": -1.499477983,
#     "postcode": "S75 2EP",
#     "geocode_coordinates": "SRID=27700;POINT (-1.499477983 53.55913544)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ149"
#     },
#     "trust": {
#       "ods_code": "RFF",
#       "name": "BARNSLEY HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "GAWBER ROAD",
#       "address_line_2": "",
#       "town": "BARNSLEY",
#       "postcode": "S75 2EP",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000061",
#       "name": "NHS South Yorkshire Integrated Care Board",
#       "ods_code": "QF7"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Trent Epilepsy Network",
#       "boundary_identifier": "TEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVN38",
#     "name": "BARTON HILL SETTLEMENT",
#     "website": "",
#     "address1": "BARTON HILL SETTLEMENT",
#     "address2": "43 DUCIE ROAD",
#     "address3": "LAWRENCE HILL",
#     "telephone": "",
#     "city": "BRISTOL",
#     "county": "AVON",
#     "latitude": 51.45640792575672,
#     "longitude": -2.563680201763284,
#     "postcode": "BS5 0AX",
#     "geocode_coordinates": "SRID=27700;POINT (-2.563680201763284 51.45640792575672)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RVN",
#       "name": "AVON AND WILTSHIRE MENTAL HEALTH PARTNERSHIP NHS TRUST",
#       "address_line_1": "BATH NHS HOUSE",
#       "address_line_2": "NEWBRIDGE HILL",
#       "town": "BATH",
#       "postcode": "BA1 3QE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000040",
#       "name": "NHS Bath and North East Somerset, Swindon and Wiltshire Integrated Care Board",
#       "ods_code": "QOX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RAJ12",
#     "name": "BASILDON HOSPITAL",
#     "website": "",
#     "address1": "NETHERMAYNE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BASILDON",
#     "county": "ESSEX",
#     "latitude": 51.558185871010345,
#     "longitude": 0.45187032374537445,
#     "postcode": "SS16 5NL",
#     "geocode_coordinates": "SRID=27700;POINT (0.4518703237453744 51.55818587101034)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ019"
#     },
#     "trust": {
#       "ods_code": "RAJ",
#       "name": "MID AND SOUTH ESSEX NHS FOUNDATION TRUST",
#       "address_line_1": "PRITTLEWELL CHASE",
#       "address_line_2": "",
#       "town": "WESTCLIFF-ON-SEA",
#       "postcode": "SS0 0RY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000026",
#       "name": "NHS Mid and South Essex Integrated Care Board",
#       "ods_code": "QH8"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RN506",
#     "name": "BASINGSTOKE AND NORTH HAMPSHIRE HOSPITAL",
#     "website": "http://www.hampshirehospitals.nhs.uk",
#     "address1": "ALDERMASTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BASINGSTOKE",
#     "county": "HAMPSHIRE",
#     "latitude": 51.28063583,
#     "longitude": -1.109903693,
#     "postcode": "RG24 9NA",
#     "geocode_coordinates": "SRID=27700;POINT (-1.109903693 51.28063583)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ159"
#     },
#     "trust": {
#       "ods_code": "RN5",
#       "name": "HAMPSHIRE HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "BASINGSTOKE AND NORTH HAMPSHIRE HOS",
#       "address_line_2": "ALDERMASTON ROAD",
#       "town": "BASINGSTOKE",
#       "postcode": "RG24 9NA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RP5BA",
#     "name": "BASSETLAW HOSPITAL",
#     "website": "http://www.dbth.nhs.uk",
#     "address1": "KILTON HILL",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WORKSOP",
#     "county": "NOTTINGHAMSHIRE",
#     "latitude": 53.31655502,
#     "longitude": -1.110268831,
#     "postcode": "S81 0BD",
#     "geocode_coordinates": "SRID=27700;POINT (-1.110268831 53.31655502)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ016"
#     },
#     "trust": {
#       "ods_code": "RP5",
#       "name": "DONCASTER AND BASSETLAW TEACHING HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "DONCASTER ROYAL INFIRMARY",
#       "address_line_2": "ARMTHORPE ROAD",
#       "town": "DONCASTER",
#       "postcode": "DN2 5LT",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000060",
#       "name": "NHS Nottingham and Nottinghamshire Integrated Care Board",
#       "ods_code": "QT1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Trent Epilepsy Network",
#       "boundary_identifier": "TEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1CE4",
#     "name": "BATTENBURG AVENUE CLINIC",
#     "website": "",
#     "address1": "BATTENBURG AVENUE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "PORTSMOUTH",
#     "county": "HAMPSHIRE",
#     "latitude": 50.822634957956915,
#     "longitude": -1.0703087165064853,
#     "postcode": "PO2 0TA",
#     "geocode_coordinates": "SRID=27700;POINT (-1.070308716506485 50.82263495795691)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "R1C",
#       "name": "SOLENT NHS TRUST",
#       "address_line_1": "SOLENT NHS TRUST HEADQUARTERS",
#       "address_line_2": "HIGHPOINT VENUE",
#       "town": "SOUTHAMPTON",
#       "postcode": "SO19 8BR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RC979",
#     "name": "BEDFORD HOSPITAL SOUTH WING",
#     "website": "",
#     "address1": "SOUTH WING",
#     "address2": "KEMPSTON ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "BEDFORD",
#     "county": "",
#     "latitude": 52.128773757410244,
#     "longitude": -0.471222131766747,
#     "postcode": "MK42 9DJ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.471222131766747 52.12877375741024)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ220"
#     },
#     "trust": {
#       "ods_code": "RC9",
#       "name": "BEDFORDSHIRE HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "LEWSEY ROAD",
#       "address_line_2": "",
#       "town": "LUTON",
#       "postcode": "LU4 0DZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000024",
#       "name": "NHS Bedfordshire, Luton and Milton Keynes Integrated Care Board",
#       "ods_code": "QHG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RQ301",
#     "name": "BIRMINGHAM CHILDREN'S HOSPITAL",
#     "website": "http://www.bwc.nhs.uk",
#     "address1": "STEELHOUSE LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BIRMINGHAM",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.48477173,
#     "longitude": -1.893798947,
#     "postcode": "B4 6NH",
#     "geocode_coordinates": "SRID=27700;POINT (-1.893798947 52.48477173)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ108"
#     },
#     "trust": {
#       "ods_code": "RQ3",
#       "name": "BIRMINGHAM WOMEN'S AND CHILDREN'S NHS FOUNDATION TRUST",
#       "address_line_1": "STEELHOUSE LANE",
#       "address_line_2": "",
#       "town": "BIRMINGHAM",
#       "postcode": "B4 6NH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000055",
#       "name": "NHS Birmingham and Solihull Integrated Care Board",
#       "ods_code": "QHL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXPBA",
#     "name": "BISHOP AUCKLAND HOSPITAL",
#     "website": "http://www.cddft.nhs.uk/",
#     "address1": "COCKTON HILL ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BISHOP AUCKLAND",
#     "county": "COUNTY DURHAM",
#     "latitude": 54.65584946,
#     "longitude": -1.678531766,
#     "postcode": "DL14 6AD",
#     "geocode_coordinates": "SRID=27700;POINT (-1.678531766 54.65584946)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ160"
#     },
#     "trust": {
#       "ods_code": "RXP",
#       "name": "COUNTY DURHAM AND DARLINGTON NHS FOUNDATION TRUST",
#       "address_line_1": "DARLINGTON MEMORIAL HOSPITAL",
#       "address_line_2": "HOLLYHURST ROAD",
#       "town": "DARLINGTON",
#       "postcode": "DL3 6HX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXL01",
#     "name": "BLACKPOOL VICTORIA HOSPITAL",
#     "website": "https://www.bfwh.nhs.uk/",
#     "address1": "WHINNEY HEYS ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BLACKPOOL",
#     "county": "LANCASHIRE",
#     "latitude": 53.82066727,
#     "longitude": -3.016264915,
#     "postcode": "FY3 8NR",
#     "geocode_coordinates": "SRID=27700;POINT (-3.016264915 53.82066727)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ106"
#     },
#     "trust": {
#       "ods_code": "RXL",
#       "name": "BLACKPOOL TEACHING HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "VICTORIA HOSPITAL",
#       "address_line_2": "WHINNEY HEYS ROAD",
#       "town": "BLACKPOOL",
#       "postcode": "FY3 8NR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000048",
#       "name": "NHS Lancashire and South Cumbria Integrated Care Board",
#       "ods_code": "QE1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RYK14",
#     "name": "BLAKENALL VILLAGE CENTRE",
#     "website": "",
#     "address1": "79 THAMES ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WALSALL",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.61485987017649,
#     "longitude": -1.986635562256734,
#     "postcode": "WS3 1LZ",
#     "geocode_coordinates": "SRID=27700;POINT (-1.986635562256734 52.61485987017649)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RYK",
#       "name": "DUDLEY INTEGRATED HEALTH AND CARE NHS TRUST",
#       "address_line_1": "VENTURE WAY",
#       "address_line_2": "",
#       "town": "BRIERLEY HILL",
#       "postcode": "DY5 1RU",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000062",
#       "name": "NHS Black Country Integrated Care Board",
#       "ods_code": "QUA"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTFDX",
#     "name": "BLYTH COMMUNITY HOSPITAL",
#     "website": "https://www.northumbria.nhs.uk/blyth",
#     "address1": "THOROTON STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BLYTH",
#     "county": "NORTHUMBERLAND",
#     "latitude": 55.12787628,
#     "longitude": -1.514920115,
#     "postcode": "NE24 1DX",
#     "geocode_coordinates": "SRID=27700;POINT (-1.514920115 55.12787628)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTF",
#       "name": "NORTHUMBRIA HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "NORTH TYNESIDE GENERAL HOSPITAL",
#       "address_line_2": "RAKE LANE",
#       "town": "NORTH SHIELDS",
#       "postcode": "NE29 8NH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RAE01",
#     "name": "BRADFORD ROYAL INFIRMARY",
#     "website": "",
#     "address1": "DUCKWORTH LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BRADFORD",
#     "county": "WEST YORKSHIRE",
#     "latitude": 53.80683265969457,
#     "longitude": -1.7966404739876927,
#     "postcode": "BD9 6RH",
#     "geocode_coordinates": "SRID=27700;POINT (-1.796640473987693 53.80683265969457)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RAE",
#       "name": "BRADFORD TEACHING HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "BRADFORD ROYAL INFIRMARY",
#       "address_line_2": "DUCKWORTH LANE",
#       "town": "BRADFORD",
#       "postcode": "BD9 6RJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000054",
#       "name": "NHS West Yorkshire Integrated Care Board",
#       "ods_code": "QWO"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RMC79",
#     "name": "BREIGHTMET HEALTH CENTRE",
#     "website": "",
#     "address1": "BREIGHTMET FOLD LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BOLTON",
#     "county": "LANCASHIRE",
#     "latitude": 53.58260174509509,
#     "longitude": -2.3841852348486086,
#     "postcode": "BL2 6NT",
#     "geocode_coordinates": "SRID=27700;POINT (-2.384185234848609 53.58260174509509)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RMC",
#       "name": "BOLTON NHS FOUNDATION TRUST",
#       "address_line_1": "THE ROYAL BOLTON HOSPITAL",
#       "address_line_2": "MINERVA ROAD",
#       "town": "BOLTON",
#       "postcode": "BL4 0JR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RA723",
#     "name": "BRISTOL ROYAL HOSPITAL FOR CHILDREN",
#     "website": "http://www.uhbristol.nhs.uk/your-hospitals/bristol-royal-hospital-for-children.html",
#     "address1": "UPPER MAUDLIN STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BRISTOL",
#     "county": "",
#     "latitude": 51.45775223,
#     "longitude": -2.597314835,
#     "postcode": "BS2 8BJ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.597314835 51.45775223)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ139"
#     },
#     "trust": {
#       "ods_code": "RA7",
#       "name": "UNIVERSITY HOSPITALS BRISTOL AND WESTON NHS FOUNDATION TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "MARLBOROUGH STREET",
#       "town": "BRISTOL",
#       "postcode": "BS1 3NU",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000039",
#       "name": "NHS Bristol, North Somerset and South Gloucestershire Integrated Care Board",
#       "ods_code": "QUY"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A2AJ",
#     "name": "BRONGLAIS GENERAL HOSPITAL",
#     "website": "",
#     "address1": "CARADOC ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ABERYSTWYTH",
#     "county": "DYFED",
#     "latitude": 52.41629608119735,
#     "longitude": -4.071755772843108,
#     "postcode": "SY23 1ER",
#     "geocode_coordinates": "SRID=27700;POINT (-4.071755772843108 52.41629608119735)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A2",
#       "boundary_identifier": "W11000025",
#       "name": "Hywel Dda University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "R1LCT",
#     "name": "BROOMFIELD HOSPITAL",
#     "website": "https://www.mse.nhs.uk/",
#     "address1": "COURT ROAD",
#     "address2": "BROOMFIELD",
#     "address3": "",
#     "telephone": "",
#     "city": "CHELMSFORD",
#     "county": "ESSEX",
#     "latitude": 51.77465439,
#     "longitude": 0.466007918,
#     "postcode": "CM1 7ET",
#     "geocode_coordinates": "SRID=27700;POINT (0.466007918 51.77465439)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ171"
#     },
#     "trust": {
#       "ods_code": "R1L",
#       "name": "ESSEX PARTNERSHIP UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "THE LODGE",
#       "address_line_2": "LODGE APPROACH",
#       "town": "WICKFORD",
#       "postcode": "SS11 7XX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000026",
#       "name": "NHS Mid and South Essex Integrated Care Board",
#       "ods_code": "QH8"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXQ61",
#     "name": "BUCKINGHAM HOSPITAL",
#     "website": "http://www.buckshealthcare.nhs.uk",
#     "address1": "HIGH STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BUCKINGHAM",
#     "county": "BUCKINGHAMSHIRE",
#     "latitude": 52.0015831,
#     "longitude": -0.985668004,
#     "postcode": "MK18 1NU",
#     "geocode_coordinates": "SRID=27700;POINT (-0.985668004 52.0015831)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RXQ",
#       "name": "BUCKINGHAMSHIRE HEALTHCARE NHS TRUST",
#       "address_line_1": "AMERSHAM HOSPITAL",
#       "address_line_2": "WHIELDEN STREET",
#       "town": "AMERSHAM",
#       "postcode": "HP7 0JD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000044",
#       "name": "NHS Buckinghamshire, Oxfordshire and Berkshire West Integrated Care Board",
#       "ods_code": "QU9"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVV02",
#     "name": "BUCKLAND HOSPITAL",
#     "website": "http://www.ekhuft.nhs.uk/buckland",
#     "address1": "COOMBE VALLEY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "DOVER",
#     "county": "KENT",
#     "latitude": 51.13205338,
#     "longitude": 1.292394757,
#     "postcode": "CT17 0HD",
#     "geocode_coordinates": "SRID=27700;POINT (1.292394757 51.13205338)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ024"
#     },
#     "trust": {
#       "ods_code": "RVV",
#       "name": "EAST KENT HOSPITALS UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "KENT & CANTERBURY HOSPITAL",
#       "address_line_2": "ETHELBERT ROAD",
#       "town": "CANTERBURY",
#       "postcode": "CT1 3NG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000032",
#       "name": "NHS Kent and Medway Integrated Care Board",
#       "ods_code": "QKS"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXR10",
#     "name": "BURNLEY GENERAL HOSPITAL",
#     "website": "http://www.elht.nhs.uk",
#     "address1": "CASTERTON AVENUE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BURNLEY",
#     "county": "LANCASHIRE",
#     "latitude": 53.81042862,
#     "longitude": -2.227864027,
#     "postcode": "BB10 2PQ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.227864027 53.81042862)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RXR",
#       "name": "EAST LANCASHIRE HOSPITALS NHS TRUST",
#       "address_line_1": "ROYAL BLACKBURN HOSPITAL",
#       "address_line_2": "HASLINGDEN ROAD",
#       "town": "BLACKBURN",
#       "postcode": "BB2 3HH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000048",
#       "name": "NHS Lancashire and South Cumbria Integrated Care Board",
#       "ods_code": "QE1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RHM08",
#     "name": "BURSLEDON HOUSE",
#     "website": "",
#     "address1": "SOUTHAMPTON GENERAL HOSPITAL CAMPUS",
#     "address2": "TREMONA ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "SOUTHAMPTON",
#     "county": "HAMPSHIRE",
#     "latitude": 50.93125793154169,
#     "longitude": -1.433717192863688,
#     "postcode": "SO16 6YD",
#     "geocode_coordinates": "SRID=27700;POINT (-1.433717192863688 50.93125793154169)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RHM",
#       "name": "UNIVERSITY HOSPITAL SOUTHAMPTON NHS FOUNDATION TRUST",
#       "address_line_1": "SOUTHAMPTON GENERAL HOSPITAL",
#       "address_line_2": "TREMONA ROAD",
#       "town": "SOUTHAMPTON",
#       "postcode": "SO16 6YD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTG02",
#     "name": "BURTON HOSPITAL",
#     "website": "https://www.uhdb.nhs.uk/",
#     "address1": "QUEENS HOSPITAL",
#     "address2": "BELVEDERE ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "BURTON-ON-TRENT",
#     "county": "STAFFORDSHIRE",
#     "latitude": 52.81777954,
#     "longitude": -1.65636909,
#     "postcode": "DE13 0RB",
#     "geocode_coordinates": "SRID=27700;POINT (-1.65636909 52.81777954)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ033"
#     },
#     "trust": {
#       "ods_code": "RTG",
#       "name": "UNIVERSITY HOSPITALS OF DERBY AND BURTON NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL DERBY HOSPITAL",
#       "address_line_2": "UTTOXETER ROAD",
#       "town": "DERBY",
#       "postcode": "DE22 3NE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000058",
#       "name": "NHS Derby and Derbyshire Integrated Care Board",
#       "ods_code": "QJ2"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWY02",
#     "name": "CALDERDALE ROYAL HOSPITAL",
#     "website": "http://www.cht.nhs.uk",
#     "address1": "SALTERHEBBLE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HALIFAX",
#     "county": "WEST YORKSHIRE",
#     "latitude": 53.70482254,
#     "longitude": -1.857493639,
#     "postcode": "HX3 0PW",
#     "geocode_coordinates": "SRID=27700;POINT (-1.857493639 53.70482254)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ186"
#     },
#     "trust": {
#       "ods_code": "RWY",
#       "name": "CALDERDALE AND HUDDERSFIELD NHS FOUNDATION TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "ACRE STREET",
#       "town": "HUDDERSFIELD",
#       "postcode": "HD3 3EA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000054",
#       "name": "NHS West Yorkshire Integrated Care Board",
#       "ods_code": "QWO"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "C1G7Z",
#     "name": "CDC POOLE @ DORSET HEALTH VILLAGE",
#     "website": "",
#     "address1": "2ND FLOOR",
#     "address2": "DOLPHIN CENTRE",
#     "address3": "",
#     "telephone": "",
#     "city": "POOLE",
#     "county": "DORSET",
#     "latitude": 50.719050056794515,
#     "longitude": -1.9807258428334855,
#     "postcode": "BH15 1SZ",
#     "geocode_coordinates": "SRID=27700;POINT (-1.980725842833486 50.71905005679452)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RDY",
#       "name": "DORSET HEALTHCARE UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "SENTINEL HOUSE",
#       "address_line_2": "4-6 NUFFIELD ROAD",
#       "town": "POOLE",
#       "postcode": "BH17 0RB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000041",
#       "name": "NHS Dorset Integrated Care Board",
#       "ods_code": "QVV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1K02",
#     "name": "CENTRAL MIDDLESEX HOSPITAL",
#     "website": "http://www.lnwh.nhs.uk",
#     "address1": "ACTON LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.53093719,
#     "longitude": -0.269146293,
#     "postcode": "NW10 7NS",
#     "geocode_coordinates": "SRID=27700;POINT (-0.269146293 51.53093719)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "R1K",
#       "name": "LONDON NORTH WEST UNIVERSITY HEALTHCARE NHS TRUST",
#       "address_line_1": "NORTHWICK PARK HOSPITAL",
#       "address_line_2": "WATFORD ROAD",
#       "town": "HARROW",
#       "postcode": "HA1 3UJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000027",
#       "name": "NHS North West London Integrated Care Board",
#       "ods_code": "QRV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Brent",
#       "gss_code": "E09000005"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RYVD9",
#     "name": "CENTRE FOR CHILD DEVELOPMENT",
#     "website": "",
#     "address1": "HILL RISE",
#     "address2": "KEMPSTON",
#     "address3": "",
#     "telephone": "",
#     "city": "BEDFORD",
#     "county": "BEDFORDSHIRE",
#     "latitude": 52.1095632794134,
#     "longitude": -0.511761474096703,
#     "postcode": "MK42 7EB",
#     "geocode_coordinates": "SRID=27700;POINT (-0.511761474096703 52.1095632794134)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RYV",
#       "name": "CAMBRIDGESHIRE COMMUNITY SERVICES NHS TRUST",
#       "address_line_1": "UNIT 7-8",
#       "address_line_2": "MEADOW PARK",
#       "town": "ST. IVES",
#       "postcode": "PE27 4LG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000024",
#       "name": "NHS Bedfordshire, Luton and Milton Keynes Integrated Care Board",
#       "ods_code": "QHG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RALC7",
#     "name": "CHASE FARM HOSPITAL",
#     "website": null,
#     "address1": "127 THE RIDGEWAY",
#     "address2": null,
#     "address3": null,
#     "telephone": null,
#     "city": "ENFIELD",
#     "county": null,
#     "latitude": 51.666528,
#     "longitude": -0.104009,
#     "postcode": "EN2 8JL",
#     "geocode_coordinates": "SRID=27700;POINT (-0.104009 51.666528)",
#     "active": true,
#     "published_at": "2014-04-01",
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ014"
#     },
#     "trust": {
#       "ods_code": "RAL",
#       "name": "ROYAL FREE LONDON NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL FREE HOSPITAL",
#       "address_line_2": "POND STREET",
#       "town": "LONDON",
#       "postcode": "NW3 2QG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RQM01",
#     "name": "CHELSEA & WESTMINSTER HOSPITAL",
#     "website": "http://www.chelwest.nhs.uk",
#     "address1": "369 FULHAM ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.48431015,
#     "longitude": -0.181629702,
#     "postcode": "SW10 9NH",
#     "geocode_coordinates": "SRID=27700;POINT (-0.181629702 51.48431015)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ130"
#     },
#     "trust": {
#       "ods_code": "RQM",
#       "name": "CHELSEA AND WESTMINSTER HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "CHELSEA & WESTMINSTER HOSPITAL",
#       "address_line_2": "369 FULHAM ROAD",
#       "town": "LONDON",
#       "postcode": "SW10 9NH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000027",
#       "name": "NHS North West London Integrated Care Board",
#       "ods_code": "QRV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Kensington and Chelsea",
#       "gss_code": "E09000020"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTE01",
#     "name": "CHELTENHAM GENERAL HOSPITAL",
#     "website": "http://www.gloshospitals.nhs.uk",
#     "address1": "SANDFORD ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CHELTENHAM",
#     "county": "GLOUCESTERSHIRE",
#     "latitude": 51.89212418,
#     "longitude": -2.07186842,
#     "postcode": "GL53 7AN",
#     "geocode_coordinates": "SRID=27700;POINT (-2.07186842 51.89212418)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ242"
#     },
#     "trust": {
#       "ods_code": "RTE",
#       "name": "GLOUCESTERSHIRE HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "CHELTENHAM GENERAL HOSPITAL",
#       "address_line_2": "SANDFORD ROAD",
#       "town": "CHELTENHAM",
#       "postcode": "GL53 7AN",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000043",
#       "name": "NHS Gloucestershire Integrated Care Board",
#       "ods_code": "QR1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A6BJ",
#     "name": "CHEPSTOW COMMUNITY HOSPITAL",
#     "website": "",
#     "address1": "TEMPEST WAY",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CHEPSTOW",
#     "county": "GWENT",
#     "latitude": 51.63943343225332,
#     "longitude": -2.686661402962116,
#     "postcode": "NP16 5YX",
#     "geocode_coordinates": "SRID=27700;POINT (-2.686661402962116 51.63943343225332)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A6",
#       "boundary_identifier": "W11000028",
#       "name": "Aneurin Bevan University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RFSDA",
#     "name": "CHESTERFIELD ROYAL HOSPITAL",
#     "website": "http://www.chesterfieldroyal.nhs.uk",
#     "address1": "CALOW",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CHESTERFIELD",
#     "county": "DERBYSHIRE",
#     "latitude": 53.2362175,
#     "longitude": -1.400036573,
#     "postcode": "S44 5BL",
#     "geocode_coordinates": "SRID=27700;POINT (-1.400036573 53.2362175)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ064"
#     },
#     "trust": {
#       "ods_code": "RFS",
#       "name": "CHESTERFIELD ROYAL HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "CHESTERFIELD ROAD",
#       "address_line_2": "CALOW",
#       "town": "CHESTERFIELD",
#       "postcode": "S44 5BL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000058",
#       "name": "NHS Derby and Derbyshire Integrated Care Board",
#       "ods_code": "QJ2"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Trent Epilepsy Network",
#       "boundary_identifier": "TEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXP48",
#     "name": "CHESTER-LE-STREET HEALTH CENTRE",
#     "website": "",
#     "address1": "NEWCASTLE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CHESTER LE STREET",
#     "county": "COUNTY DURHAM",
#     "latitude": 54.861359849136804,
#     "longitude": -1.572211745083105,
#     "postcode": "DH3 3UR",
#     "geocode_coordinates": "SRID=27700;POINT (-1.572211745083105 54.8613598491368)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RXP",
#       "name": "COUNTY DURHAM AND DARLINGTON NHS FOUNDATION TRUST",
#       "address_line_1": "DARLINGTON MEMORIAL HOSPITAL",
#       "address_line_2": "HOLLYHURST ROAD",
#       "town": "DARLINGTON",
#       "postcode": "DL3 6HX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "K8C1E",
#     "name": "CHEYNE CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "DOUGHTY HOUSE",
#     "address2": "369 FULHAM ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "",
#     "latitude": 51.48464571866343,
#     "longitude": -0.18172355879372384,
#     "postcode": "SW10 9NH",
#     "geocode_coordinates": "SRID=27700;POINT (-0.1817235587937238 51.48464571866343)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RQM",
#       "name": "CHELSEA AND WESTMINSTER HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "CHELSEA & WESTMINSTER HOSPITAL",
#       "address_line_2": "369 FULHAM ROAD",
#       "town": "LONDON",
#       "postcode": "SW10 9NH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000027",
#       "name": "NHS North West London Integrated Care Board",
#       "ods_code": "QRV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Kensington and Chelsea",
#       "gss_code": "E09000020"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RGR69",
#     "name": "CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "HOSPITAL ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BURY ST. EDMUNDS",
#     "county": "SUFFOLK",
#     "latitude": 52.24063085442167,
#     "longitude": 0.7084705271013394,
#     "postcode": "IP33 3ND",
#     "geocode_coordinates": "SRID=27700;POINT (0.7084705271013394 52.24063085442167)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RGR",
#       "name": "WEST SUFFOLK NHS FOUNDATION TRUST",
#       "address_line_1": "WEST SUFFOLK HOSPITAL",
#       "address_line_2": "HARDWICK LANE",
#       "town": "BURY ST. EDMUNDS",
#       "postcode": "IP33 2QZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000023",
#       "name": "NHS Suffolk and North East Essex Integrated Care Board",
#       "ods_code": "QJG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1LVD",
#     "name": "CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "MINTON WAY",
#     "address2": "CHURCH LANGLEY",
#     "address3": "",
#     "telephone": "",
#     "city": "HARLOW",
#     "county": "ESSEX",
#     "latitude": 51.767976263497225,
#     "longitude": 0.13251425290988306,
#     "postcode": "CM17 9TG",
#     "geocode_coordinates": "SRID=27700;POINT (0.1325142529098831 51.76797626349722)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "R1L",
#       "name": "ESSEX PARTNERSHIP UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "THE LODGE",
#       "address_line_2": "LODGE APPROACH",
#       "town": "WICKFORD",
#       "postcode": "SS11 7XX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000026",
#       "name": "NHS Mid and South Essex Integrated Care Board",
#       "ods_code": "QH8"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RYW91",
#     "name": "CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "HEARTLANDS HOSPITAL",
#     "address2": "45 BORDESLEY GREEN EAST,",
#     "address3": "",
#     "telephone": "",
#     "city": "BIRMINGHAM",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.47799116365538,
#     "longitude": -1.8275362317445312,
#     "postcode": "SW10 9NH",
#     "geocode_coordinates": "SRID=27700;POINT (-1.827536231744531 52.47799116365538)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RYW",
#       "name": "BIRMINGHAM COMMUNITY HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "3 PRIESTLEY WHARF",
#       "address_line_2": "HOLT STREET",
#       "town": "BIRMINGHAM",
#       "postcode": "B7 4BN",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000055",
#       "name": "NHS Birmingham and Solihull Integrated Care Board",
#       "ods_code": "QHL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RATE2",
#     "name": "CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "BRENTWOOD COMMUNITY HOSPITAL",
#     "address2": "11 CRESCENT DRIVE",
#     "address3": "",
#     "telephone": "",
#     "city": "BRENTWOOD",
#     "county": "ESSEX",
#     "latitude": 51.62369359002008,
#     "longitude": 0.31635099703690556,
#     "postcode": "CM15 8DR",
#     "geocode_coordinates": "SRID=27700;POINT (0.3163509970369056 51.62369359002008)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RAT",
#       "name": "NORTH EAST LONDON NHS FOUNDATION TRUST",
#       "address_line_1": "WEST WING",
#       "address_line_2": "C E M E CENTRE",
#       "town": "RAINHAM",
#       "postcode": "RM13 8GQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000029",
#       "name": "NHS North East London Integrated Care Board",
#       "ods_code": "QMF"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RYR41",
#     "name": "CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "28-29 WESTHAMPNETT ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CHICHESTER",
#     "county": "WEST SUSSEX",
#     "latitude": 50.84253071425149,
#     "longitude": -0.7601499913684482,
#     "postcode": "PO19 7HH",
#     "geocode_coordinates": "SRID=27700;POINT (-0.7601499913684482 50.84253071425149)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RYR",
#       "name": "UNIVERSITY HOSPITALS SUSSEX NHS FOUNDATION TRUST",
#       "address_line_1": "WORTHING HOSPITAL",
#       "address_line_2": "LYNDHURST ROAD",
#       "town": "WORTHING",
#       "postcode": "BN11 2DH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000064",
#       "name": "NHS Sussex Integrated Care Board",
#       "ods_code": "QNX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RK98A",
#     "name": "CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "SCOTT HOSPITAL",
#     "address2": "BEACON PARK ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "PLYMOUTH",
#     "county": "DEVON",
#     "latitude": 50.39051691746257,
#     "longitude": -4.163071330781396,
#     "postcode": "PL2 2PQ",
#     "geocode_coordinates": "SRID=27700;POINT (-4.163071330781396 50.39051691746257)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RK9",
#       "name": "UNIVERSITY HOSPITALS PLYMOUTH NHS TRUST",
#       "address_line_1": "DERRIFORD HOSPITAL",
#       "address_line_2": "DERRIFORD ROAD",
#       "town": "PLYMOUTH",
#       "postcode": "PL6 8DH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000037",
#       "name": "NHS Devon Integrated Care Board",
#       "ods_code": "QJK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A1NU",
#     "name": "CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "NANT Y GAMAR",
#     "address2": "CRAIG Y DON",
#     "address3": "",
#     "telephone": "",
#     "city": "LLANDUDNO",
#     "county": "GWYNEDD",
#     "latitude": 52.24065712570418,
#     "longitude": 0.7084597970760184,
#     "postcode": "LL30 1YE",
#     "geocode_coordinates": "SRID=27700;POINT (0.7084597970760184 52.24065712570418)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A1",
#       "boundary_identifier": "W11000023",
#       "name": "Betsi Cadwaladr University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "7A1LW",
#     "name": "CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "HOLYHEAD ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BANGOR",
#     "county": "GWYNEDD",
#     "latitude": 53.22551496089767,
#     "longitude": -4.134974832357014,
#     "postcode": "LL57 2EE",
#     "geocode_coordinates": "SRID=27700;POINT (-4.134974832357014 53.22551496089767)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A1",
#       "boundary_identifier": "W11000023",
#       "name": "Betsi Cadwaladr University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RYVF7",
#     "name": "CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "ADDENBROOKES HOSPITAL",
#     "address2": "HILLS ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "CAMBRIDGE",
#     "county": "CAMBRIDGESHIRE",
#     "latitude": 52.17487593919441,
#     "longitude": 0.14141622590743344,
#     "postcode": "CB2 0QQ",
#     "geocode_coordinates": "SRID=27700;POINT (0.1414162259074334 52.17487593919441)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RYV",
#       "name": "CAMBRIDGESHIRE COMMUNITY SERVICES NHS TRUST",
#       "address_line_1": "UNIT 7-8",
#       "address_line_2": "MEADOW PARK",
#       "town": "ST. IVES",
#       "postcode": "PE27 4LG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000024",
#       "name": "NHS Bedfordshire, Luton and Milton Keynes Integrated Care Board",
#       "ods_code": "QHG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXPCD",
#     "name": "CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "PRIORY COURT",
#     "address2": "ANNFIELD PLAIN",
#     "address3": "",
#     "telephone": "",
#     "city": "STANLEY",
#     "county": "COUNTY DURHAM",
#     "latitude": 54.857744,
#     "longitude": -1.736403,
#     "postcode": "DH9 7TG",
#     "geocode_coordinates": "SRID=27700;POINT (-1.736403 54.857744)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RXP",
#       "name": "COUNTY DURHAM AND DARLINGTON NHS FOUNDATION TRUST",
#       "address_line_1": "DARLINGTON MEMORIAL HOSPITAL",
#       "address_line_2": "HOLLYHURST ROAD",
#       "town": "DARLINGTON",
#       "postcode": "DL3 6HX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJC07",
#     "name": "CHILD DEVELOPMENT CENTRE (WARWICK HOSPITAL)",
#     "website": "",
#     "address1": "WARWICK HOSPITAL",
#     "address2": "LAKIN ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "WARWICK",
#     "county": "WARWICKSHIRE",
#     "latitude": 52.2899606215984,
#     "longitude": -1.584414018263402,
#     "postcode": "CV34 5BW",
#     "geocode_coordinates": "SRID=27700;POINT (-1.584414018263402 52.2899606215984)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RJC",
#       "name": "SOUTH WARWICKSHIRE UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "WARWICK HOSPITAL",
#       "address_line_2": "LAKIN ROAD",
#       "town": "WARWICK",
#       "postcode": "CV34 5BW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000018",
#       "name": "NHS Coventry and Warwickshire Integrated Care Board",
#       "ods_code": "QWU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RP416",
#     "name": "CHILD DEVELOPMENT CENTRE - WEST HAM LANE",
#     "website": "",
#     "address1": "WEST HAM LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.536834588132855,
#     "longitude": 0.006225110524521736,
#     "postcode": "E15 4PT",
#     "geocode_coordinates": "SRID=27700;POINT (0.006225110524521736 51.53683458813286)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RP4",
#       "name": "GREAT ORMOND STREET HOSPITAL FOR CHILDREN NHS FOUNDATION TRUST",
#       "address_line_1": "GREAT ORMOND STREET",
#       "address_line_2": "",
#       "town": "LONDON",
#       "postcode": "WC1N 3JH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Newham",
#       "gss_code": "E09000025"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RP427",
#     "name": "CHILD DEVELOPMENT CENTRE (WOOD ST HEALTH CENTRE)",
#     "website": "",
#     "address1": "WOOD STREET HEALTH CENTRE",
#     "address2": "6 LINFORD ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.588111852487415,
#     "longitude": -0.003012560636604331,
#     "postcode": "E17 3LA",
#     "geocode_coordinates": "SRID=27700;POINT (-0.003012560636604331 51.58811185248742)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RP4",
#       "name": "GREAT ORMOND STREET HOSPITAL FOR CHILDREN NHS FOUNDATION TRUST",
#       "address_line_1": "GREAT ORMOND STREET",
#       "address_line_2": "",
#       "town": "LONDON",
#       "postcode": "WC1N 3JH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Waltham Forest",
#       "gss_code": "E09000031"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RV3J5",
#     "name": "CHILD DEVELOPMENT CTR",
#     "website": "",
#     "address1": "WOODLANDS CENTRE",
#     "address2": "HILLINGDON HOSPITAL",
#     "address3": "",
#     "telephone": "",
#     "city": "UXBRIDGE",
#     "county": "MIDDLESEX",
#     "latitude": 51.534177763702324,
#     "longitude": -0.4578701302698584,
#     "postcode": "UB8 3NN",
#     "geocode_coordinates": "SRID=27700;POINT (-0.4578701302698584 51.53417776370232)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RV3",
#       "name": "CENTRAL AND NORTH WEST LONDON NHS FOUNDATION TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "350 EUSTON ROAD",
#       "town": "LONDON",
#       "postcode": "NW1 3AX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A3LW",
#     "name": "CHILD DEVELOPMENT UNIT",
#     "website": "",
#     "address1": "BAGLAN WAY",
#     "address2": "BAGLAN INDUSTRIAL PARK",
#     "address3": "",
#     "telephone": "",
#     "city": "PORT TALBOT",
#     "county": "WEST GLAMORGAN",
#     "latitude": 51.59865037448691,
#     "longitude": -3.802852293530534,
#     "postcode": "SA12 7BY",
#     "geocode_coordinates": "SRID=27700;POINT (-3.802852293530534 51.59865037448691)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A3",
#       "boundary_identifier": "W11000031",
#       "name": "Swansea Bay University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RV3J1",
#     "name": "CHILD HEALTH",
#     "website": "",
#     "address1": "HOSPITAL CAMPUS",
#     "address2": "EAGLESTONE",
#     "address3": "",
#     "telephone": "",
#     "city": "MILTON KEYNES",
#     "county": "BUCKINGHAMSHIRE",
#     "latitude": 52.024944716501295,
#     "longitude": -0.736349618753685,
#     "postcode": "MK6 5NG",
#     "geocode_coordinates": "SRID=27700;POINT (-0.736349618753685 52.0249447165013)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RV3",
#       "name": "CENTRAL AND NORTH WEST LONDON NHS FOUNDATION TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "350 EUSTON ROAD",
#       "town": "LONDON",
#       "postcode": "NW1 3AX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "REFCH",
#     "name": "CHILD HEALTH",
#     "website": "",
#     "address1": "PENDRAGON HOUSE",
#     "address2": "GLOWETH",
#     "address3": "",
#     "telephone": "",
#     "city": "TRURO",
#     "county": "CORNWALL",
#     "latitude": 50.2662166792816,
#     "longitude": -5.095523529924103,
#     "postcode": "TR1 3XQ",
#     "geocode_coordinates": "SRID=27700;POINT (-5.095523529924103 50.2662166792816)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "REF",
#       "name": "ROYAL CORNWALL HOSPITALS NHS TRUST",
#       "address_line_1": "ROYAL CORNWALL HOSPITAL",
#       "address_line_2": "TRELISKE",
#       "town": "TRURO",
#       "postcode": "TR1 3LJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000036",
#       "name": "NHS Cornwall and the Isles of Scilly Integrated Care Board",
#       "ods_code": "QT6"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A7BM",
#     "name": "CHILDREN'S CENTRE ANNEX",
#     "website": "",
#     "address1": "BRECON WAR MEMORIAL HOSPITAL",
#     "address2": "CERRIGCOCHION ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "BRECON",
#     "county": "",
#     "latitude": 51.94899731632159,
#     "longitude": -3.3848060452712567,
#     "postcode": "LD3 7NS",
#     "geocode_coordinates": "SRID=27700;POINT (-3.384806045271257 51.94899731632159)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A7",
#       "boundary_identifier": "W11000024",
#       "name": "Powys Teaching Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": null,
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RX1LK",
#     "name": "CHILDRENS DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "NOTTINGHAM CITY HOSPITAL",
#     "address2": "HUCKNALL ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "NOTTINGHAM",
#     "county": "NOTTINGHAMSHIRE",
#     "latitude": 52.9905804091911,
#     "longitude": -1.1640642028760453,
#     "postcode": "NG5 1PB",
#     "geocode_coordinates": "SRID=27700;POINT (-1.164064202876045 52.9905804091911)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RX1",
#       "name": "NOTTINGHAM UNIVERSITY HOSPITALS NHS TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "QUEENS MEDICAL CENTRE",
#       "town": "NOTTINGHAM",
#       "postcode": "NG7 2UH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000060",
#       "name": "NHS Nottingham and Nottinghamshire Integrated Care Board",
#       "ods_code": "QT1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXN01",
#     "name": "CHORLEY & SOUTH RIBBLE HOSPITAL",
#     "website": "https://www.lancsteachinghospitals.nhs.uk",
#     "address1": "PRESTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CHORLEY",
#     "county": "LANCASHIRE",
#     "latitude": 53.66609192,
#     "longitude": -2.636446476,
#     "postcode": "PR7 1PP",
#     "geocode_coordinates": "SRID=27700;POINT (-2.636446476 53.66609192)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RXN",
#       "name": "LANCASHIRE TEACHING HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL PRESTON HOSPITAL",
#       "address_line_2": "SHAROE GREEN LANE",
#       "town": "PRESTON",
#       "postcode": "PR2 9HT",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000048",
#       "name": "NHS Lancashire and South Cumbria Integrated Care Board",
#       "ods_code": "QE1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RT5CF",
#     "name": "CITY COMMUNITY PAEDS (EPMA)",
#     "website": "",
#     "address1": "RIVERSIDE HOUSE",
#     "address2": "BRIDGE PARK PLAZA",
#     "address3": "BRIDGE PARK ROAD",
#     "telephone": "",
#     "city": "LEICESTER",
#     "county": "LEICESTERSHIRE",
#     "latitude": 52.6765,
#     "longitude": -1.10302,
#     "postcode": "LE4 8PQ",
#     "geocode_coordinates": "SRID=27700;POINT (-1.10302 52.6765)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RT5",
#       "name": "LEICESTERSHIRE PARTNERSHIP NHS TRUST",
#       "address_line_1": "RIVERSIDE HOUSE",
#       "address_line_2": "BRIDGE PARK PLAZA",
#       "town": "LEICESTER",
#       "postcode": "LE4 8PQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000015",
#       "name": "NHS Leicester, Leicestershire and Rutland Integrated Care Board",
#       "ods_code": "QK1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXK02",
#     "name": "CITY HOSPITAL",
#     "website": "http://www.swbh.nhs.uk",
#     "address1": "DUDLEY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BIRMINGHAM",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.4886322,
#     "longitude": -1.932492137,
#     "postcode": "B18 7QH",
#     "geocode_coordinates": "SRID=27700;POINT (-1.932492137 52.4886322)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ097"
#     },
#     "trust": {
#       "ods_code": "RXK",
#       "name": "SANDWELL AND WEST BIRMINGHAM HOSPITALS NHS TRUST",
#       "address_line_1": "CITY HOSPITAL",
#       "address_line_2": "DUDLEY ROAD",
#       "town": "BIRMINGHAM",
#       "postcode": "B18 7QH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000055",
#       "name": "NHS Birmingham and Solihull Integrated Care Board",
#       "ods_code": "QHL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RDEE4",
#     "name": "COLCHESTER GENERAL HOSPITAL",
#     "website": "https://www.esneft.nhs.uk",
#     "address1": "TURNER ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "COLCHESTER",
#     "county": "ESSEX",
#     "latitude": 51.91016388,
#     "longitude": 0.899196804,
#     "postcode": "CO4 5JL",
#     "geocode_coordinates": "SRID=27700;POINT (0.899196804 51.91016388)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ076"
#     },
#     "trust": {
#       "ods_code": "RDE",
#       "name": "EAST SUFFOLK AND NORTH ESSEX NHS FOUNDATION TRUST",
#       "address_line_1": "COLCHESTER DIST GENERAL HOSPITAL",
#       "address_line_2": "TURNER ROAD",
#       "town": "COLCHESTER",
#       "postcode": "CO4 5JL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000023",
#       "name": "NHS Suffolk and North East Essex Integrated Care Board",
#       "ods_code": "QJG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTG11",
#     "name": "COLEMAN HEALTH CENTRE",
#     "website": "",
#     "address1": "COLEMAN STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "DERBY",
#     "county": "DERBYSHIRE",
#     "latitude": 52.89510370116093,
#     "longitude": -1.4452974605534492,
#     "postcode": "DE24 8NH",
#     "geocode_coordinates": "SRID=27700;POINT (-1.445297460553449 52.89510370116093)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTG",
#       "name": "UNIVERSITY HOSPITALS OF DERBY AND BURTON NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL DERBY HOSPITAL",
#       "address_line_2": "UTTOXETER ROAD",
#       "town": "DERBY",
#       "postcode": "DE22 3NE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000058",
#       "name": "NHS Derby and Derbyshire Integrated Care Board",
#       "ods_code": "QJ2"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RKEAA",
#     "name": "COMM. PAED. MEDICAL TEAM",
#     "website": "",
#     "address1": "ST. ANN'S ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "",
#     "latitude": 51.580052959564135,
#     "longitude": -0.08932988262221664,
#     "postcode": "N15 3TH",
#     "geocode_coordinates": "SRID=27700;POINT (-0.08932988262221664 51.58005295956414)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RKE",
#       "name": "WHITTINGTON HEALTH NHS TRUST",
#       "address_line_1": "THE WHITTINGTON HOSPITAL",
#       "address_line_2": "MAGDALA AVENUE",
#       "town": "LONDON",
#       "postcode": "N19 5NF",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Haringey",
#       "gss_code": "E09000014"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RYV42",
#     "name": "COMMUNITY CHILD HEALTH",
#     "website": "",
#     "address1": "1 OAK DRIVE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HUNTINGDON",
#     "county": "CAMBRIDGESHIRE",
#     "latitude": 52.34562706391435,
#     "longitude": -0.17570404808129073,
#     "postcode": "PE29 7HN",
#     "geocode_coordinates": "SRID=27700;POINT (-0.1757040480812907 52.34562706391435)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RYV",
#       "name": "CAMBRIDGESHIRE COMMUNITY SERVICES NHS TRUST",
#       "address_line_1": "UNIT 7-8",
#       "address_line_2": "MEADOW PARK",
#       "town": "ST. IVES",
#       "postcode": "PE27 4LG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000024",
#       "name": "NHS Bedfordshire, Luton and Milton Keynes Integrated Care Board",
#       "ods_code": "QHG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RY327",
#     "name": "COMMUNITY CHILDRENS SERVICES",
#     "website": "",
#     "address1": "UPTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NORWICH",
#     "county": "NORFOLK",
#     "latitude": 52.6167141242066,
#     "longitude": 1.2671810673633923,
#     "postcode": "NR4 7PA",
#     "geocode_coordinates": "SRID=27700;POINT (1.267181067363392 52.6167141242066)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RY3",
#       "name": "NORFOLK COMMUNITY HEALTH AND CARE NHS TRUST",
#       "address_line_1": "NORWICH COMMUNITY HOSPITAL",
#       "address_line_2": "BOWTHORPE ROAD",
#       "town": "NORWICH",
#       "postcode": "NR2 3TU",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000022",
#       "name": "NHS Norfolk and Waveney Integrated Care Board",
#       "ods_code": "QMM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBKCP",
#     "name": "COMMUNITY PAEDIATRICS",
#     "website": "",
#     "address1": "MANOR HOSPITAL",
#     "address2": "MOAT ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "WALSALL",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.58303487554701,
#     "longitude": -1.9976477770103798,
#     "postcode": "WS2 9PS",
#     "geocode_coordinates": "SRID=27700;POINT (-1.99764777701038 52.58303487554701)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RBK",
#       "name": "WALSALL HEALTHCARE NHS TRUST",
#       "address_line_1": "MANOR HOSPITAL",
#       "address_line_2": "MOAT ROAD",
#       "town": "WALSALL",
#       "postcode": "WS2 9PS",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000062",
#       "name": "NHS Black Country Integrated Care Board",
#       "ods_code": "QUA"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "E1H0U",
#     "name": "COMMUNITY PAEDIATRICS",
#     "website": "",
#     "address1": "KINGS DRIVE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "EASTBOURNE",
#     "county": "",
#     "latitude": 50.78645763637544,
#     "longitude": 0.26970748986035503,
#     "postcode": "BN21 2UD",
#     "geocode_coordinates": "SRID=27700;POINT (0.269707489860355 50.78645763637544)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ230"
#     },
#     "trust": {
#       "ods_code": "RXC",
#       "name": "EAST SUSSEX HEALTHCARE NHS TRUST",
#       "address_line_1": "ST ANNES HOUSE",
#       "address_line_2": "729 THE RIDGE",
#       "town": "ST. LEONARDS-ON-SEA",
#       "postcode": "TN37 7PT",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000064",
#       "name": "NHS Sussex Integrated Care Board",
#       "ods_code": "QNX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBL69",
#     "name": "COMMUNITY PAEDIATRICS",
#     "website": "",
#     "address1": "ARROWE PARK HOSPITAL",
#     "address2": "ARROWE PARK ROAD",
#     "address3": "UPTON",
#     "telephone": "",
#     "city": "WIRRAL",
#     "county": "MERSEYSIDE",
#     "latitude": 53.37066114086599,
#     "longitude": -3.095204921241858,
#     "postcode": "CH49 5PE",
#     "geocode_coordinates": "SRID=27700;POINT (-3.095204921241858 53.37066114086599)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RBL",
#       "name": "WIRRAL UNIVERSITY TEACHING HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "ARROWE PARK HOSPITAL",
#       "address_line_2": "ARROWE PARK ROAD",
#       "town": "WIRRAL",
#       "postcode": "CH49 5PE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBTCP",
#     "name": "COMMUNITY PAEDIATRICS",
#     "website": "",
#     "address1": "LEIGHTON HOSPITAL",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CREWE",
#     "county": "CHESHIRE",
#     "latitude": 53.119010495755255,
#     "longitude": -2.475808230401211,
#     "postcode": "CW1 4QJ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.475808230401211 53.11901049575525)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RBT",
#       "name": "MID CHESHIRE HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "LEIGHTON HOSPITAL",
#       "address_line_2": "LEIGHTON",
#       "town": "CREWE",
#       "postcode": "CW1 4QJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXGDG",
#     "name": "COMMUNITY PAEDIATRICS",
#     "website": "",
#     "address1": "NEW STREET HEALTH CENTRE",
#     "address2": "UPPER NEW STREET",
#     "address3": "",
#     "telephone": "",
#     "city": "BARNSLEY",
#     "county": "SOUTH YORKSHIRE",
#     "latitude": 53.54885593728199,
#     "longitude": -1.4800215002356396,
#     "postcode": "S70 1LP",
#     "geocode_coordinates": "SRID=27700;POINT (-1.48002150023564 53.54885593728199)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RXG",
#       "name": "SOUTH WEST YORKSHIRE PARTNERSHIP NHS FOUNDATION TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "FIELDHEAD HOSPITAL",
#       "town": "WAKEFIELD",
#       "postcode": "WF1 3SP",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000061",
#       "name": "NHS South Yorkshire Integrated Care Board",
#       "ods_code": "QF7"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Trent Epilepsy Network",
#       "boundary_identifier": "TEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJC39",
#     "name": "COMMUNITY PAEDIATRICS",
#     "website": "",
#     "address1": "STRATFORD HOSPITAL",
#     "address2": "ARDEN STREET",
#     "address3": "",
#     "telephone": "",
#     "city": "STRATFORD-UPON-AVON",
#     "county": "WARWICKSHIRE",
#     "latitude": 52.195127472619795,
#     "longitude": -1.7122910053235376,
#     "postcode": "CV37 6NX",
#     "geocode_coordinates": "SRID=27700;POINT (-1.712291005323538 52.1951274726198)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RJC",
#       "name": "SOUTH WARWICKSHIRE UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "WARWICK HOSPITAL",
#       "address_line_2": "LAKIN ROAD",
#       "town": "WARWICK",
#       "postcode": "CV34 5BW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000018",
#       "name": "NHS Coventry and Warwickshire Integrated Care Board",
#       "ods_code": "QWU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTG70",
#     "name": "COMMUNITY PAEDIATRICS",
#     "website": "",
#     "address1": "ROYAL DERBY HOSPITAL",
#     "address2": "UTTOXETER ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "DERBY",
#     "county": "",
#     "latitude": 52.91110179327077,
#     "longitude": -1.512306403428385,
#     "postcode": "DE22 3NE",
#     "geocode_coordinates": "SRID=27700;POINT (-1.512306403428385 52.91110179327077)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTG",
#       "name": "UNIVERSITY HOSPITALS OF DERBY AND BURTON NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL DERBY HOSPITAL",
#       "address_line_2": "UTTOXETER ROAD",
#       "town": "DERBY",
#       "postcode": "DE22 3NE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000058",
#       "name": "NHS Derby and Derbyshire Integrated Care Board",
#       "ods_code": "QJ2"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RNNHT",
#     "name": "COMMUNITY PAEDIATRICS",
#     "website": "",
#     "address1": "FURNESS GENERAL HOSPITAL",
#     "address2": "DALTON LANE",
#     "address3": "",
#     "telephone": "",
#     "city": "BARROW-IN-FURNESS",
#     "county": "CUMBRIA",
#     "latitude": 54.13673411203507,
#     "longitude": -3.2083506112939224,
#     "postcode": "LA14 4LF",
#     "geocode_coordinates": "SRID=27700;POINT (-3.208350611293922 54.13673411203507)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RNN",
#       "name": "NORTH CUMBRIA INTEGRATED CARE NHS FOUNDATION TRUST",
#       "address_line_1": "PILLARS BUILDING",
#       "address_line_2": "CUMBERLAND INFIRMARY",
#       "town": "CARLISLE",
#       "postcode": "CA2 7HY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RATE3",
#     "name": "COMMUNITY PAEDIATRICS - CDC (EPACT)",
#     "website": "",
#     "address1": "GREAT OAKS CLINIC",
#     "address2": "GREAT OAKS",
#     "address3": "",
#     "telephone": "",
#     "city": "BASILDON",
#     "county": "ESSEX",
#     "latitude": 51.61275615547437,
#     "longitude": 0.6648505953412928,
#     "postcode": "SS14 1EH",
#     "geocode_coordinates": "SRID=27700;POINT (0.6648505953412928 51.61275615547437)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RAT",
#       "name": "NORTH EAST LONDON NHS FOUNDATION TRUST",
#       "address_line_1": "WEST WING",
#       "address_line_2": "C E M E CENTRE",
#       "town": "RAINHAM",
#       "postcode": "RM13 8GQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000029",
#       "name": "NHS North East London Integrated Care Board",
#       "ods_code": "QMF"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RATE1",
#     "name": "COMMUNITY PAEDIATRICS - CDC GIFFORD HOUSE (EPACT)",
#     "website": "",
#     "address1": "THURROCK COMMUNITY HOSPITAL",
#     "address2": "LONG LANE",
#     "address3": "",
#     "telephone": "",
#     "city": "GRAYS",
#     "county": "ESSEX",
#     "latitude": 51.49616178096384,
#     "longitude": 0.33659109093339895,
#     "postcode": "RM16 2PX",
#     "geocode_coordinates": "SRID=27700;POINT (0.336591090933399 51.49616178096384)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RAT",
#       "name": "NORTH EAST LONDON NHS FOUNDATION TRUST",
#       "address_line_1": "WEST WING",
#       "address_line_2": "C E M E CENTRE",
#       "town": "RAINHAM",
#       "postcode": "RM13 8GQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000029",
#       "name": "NHS North East London Integrated Care Board",
#       "ods_code": "QMF"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1C22",
#     "name": "COMMUNITY PAEDIATRICS - EAST",
#     "website": "",
#     "address1": "ST. JAMES HOSPITAL",
#     "address2": "LOCKSWAY ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "SOUTHSEA",
#     "county": "HAMPSHIRE",
#     "latitude": 50.796657008704145,
#     "longitude": -1.0493687455907676,
#     "postcode": "PO4 8LD",
#     "geocode_coordinates": "SRID=27700;POINT (-1.049368745590768 50.79665700870414)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "R1C",
#       "name": "SOLENT NHS TRUST",
#       "address_line_1": "SOLENT NHS TRUST HEADQUARTERS",
#       "address_line_2": "HIGHPOINT VENUE",
#       "town": "SOUTHAMPTON",
#       "postcode": "SO19 8BR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXR2M",
#     "name": "COMMUNITY PAEDIATRICS - RBH",
#     "website": "",
#     "address1": "ROYAL BLACKBURN HOSPITAL",
#     "address2": "HASLINGDEN ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "BLACKBURN",
#     "county": "LANCASHIRE",
#     "latitude": 53.736147580420365,
#     "longitude": -2.461713564745193,
#     "postcode": "BB2 3HH",
#     "geocode_coordinates": "SRID=27700;POINT (-2.461713564745193 53.73614758042036)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RXR",
#       "name": "EAST LANCASHIRE HOSPITALS NHS TRUST",
#       "address_line_1": "ROYAL BLACKBURN HOSPITAL",
#       "address_line_2": "HASLINGDEN ROAD",
#       "town": "BLACKBURN",
#       "postcode": "BB2 3HH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000048",
#       "name": "NHS Lancashire and South Cumbria Integrated Care Board",
#       "ods_code": "QE1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1C55",
#     "name": "COMMUNITY PAEDIATRICS - WEST",
#     "website": "",
#     "address1": "121-123 TREMONA ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SOUTHAMPTON",
#     "county": "HAMPSHIRE",
#     "latitude": 50.93151657046671,
#     "longitude": -1.4333675030065531,
#     "postcode": "SO16 6HU",
#     "geocode_coordinates": "SRID=27700;POINT (-1.433367503006553 50.93151657046671)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "R1C",
#       "name": "SOLENT NHS TRUST",
#       "address_line_1": "SOLENT NHS TRUST HEADQUARTERS",
#       "address_line_2": "HIGHPOINT VENUE",
#       "town": "SOUTHAMPTON",
#       "postcode": "SO19 8BR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1CA6",
#     "name": "COMMUNITY PAEDS N.FOREST",
#     "website": "",
#     "address1": "ASHURST C&FAMILY CENTRE",
#     "address2": "LYNDHURST ROAD",
#     "address3": "ASHURST",
#     "telephone": "",
#     "city": "SOUTHAMPTON",
#     "county": "HAMPSHIRE",
#     "latitude": 50.89113624486605,
#     "longitude": -1.5229741072550669,
#     "postcode": "SO40 7AR",
#     "geocode_coordinates": "SRID=27700;POINT (-1.522974107255067 50.89113624486605)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "R1C",
#       "name": "SOLENT NHS TRUST",
#       "address_line_1": "SOLENT NHS TRUST HEADQUARTERS",
#       "address_line_2": "HIGHPOINT VENUE",
#       "town": "SOUTHAMPTON",
#       "postcode": "SO19 8BR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXC01",
#     "name": "CONQUEST HOSPITAL",
#     "website": "http://www.esht.nhs.uk/conquest",
#     "address1": "THE RIDGE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ST. LEONARDS-ON-SEA",
#     "county": "EAST SUSSEX",
#     "latitude": 50.88516617,
#     "longitude": 0.567284167,
#     "postcode": "TN37 7RD",
#     "geocode_coordinates": "SRID=27700;POINT (0.567284167 50.88516617)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ230"
#     },
#     "trust": {
#       "ods_code": "RXC",
#       "name": "EAST SUSSEX HEALTHCARE NHS TRUST",
#       "address_line_1": "ST ANNES HOUSE",
#       "address_line_2": "729 THE RIDGE",
#       "town": "ST. LEONARDS-ON-SEA",
#       "postcode": "TN37 7PT",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000064",
#       "name": "NHS Sussex Integrated Care Board",
#       "ods_code": "QNX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJR05",
#     "name": "COUNTESS OF CHESTER HOSPITAL",
#     "website": "http://www.coch.nhs.uk",
#     "address1": "THE COUNTESS OF CHESTER HEALTH PARK",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CHESTER",
#     "county": "CHESHIRE",
#     "latitude": 53.21153259,
#     "longitude": -2.902284384,
#     "postcode": "CH2 1UL",
#     "geocode_coordinates": "SRID=27700;POINT (-2.902284384 53.21153259)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ179"
#     },
#     "trust": {
#       "ods_code": "RJR",
#       "name": "COUNTESS OF CHESTER HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "COUNTESS OF CHESTER HEALTH PARK",
#       "address_line_2": "LIVERPOOL ROAD",
#       "town": "CHESTER",
#       "postcode": "CH2 1UL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJE09",
#     "name": "COUNTY HOSPITAL",
#     "website": null,
#     "address1": "STAFFORDSHIRE GENERAL HOSPITAL",
#     "address2": null,
#     "address3": null,
#     "telephone": null,
#     "city": "STAFFORD",
#     "county": null,
#     "latitude": 52.811291,
#     "longitude": -2.097785,
#     "postcode": "ST16 3SA",
#     "geocode_coordinates": "SRID=27700;POINT (-2.097785 52.811291)",
#     "active": true,
#     "published_at": "2005-04-01",
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ065"
#     },
#     "trust": {
#       "ods_code": "RJE",
#       "name": "UNIVERSITY HOSPITALS OF NORTH MIDLANDS NHS TRUST",
#       "address_line_1": "NEWCASTLE ROAD",
#       "address_line_2": "",
#       "town": "STOKE-ON-TRENT",
#       "postcode": "ST4 6QG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000010",
#       "name": "NHS Staffordshire and Stoke-on-Trent Integrated Care Board",
#       "ods_code": "QNC"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1APF",
#     "name": "COVERCROFT",
#     "website": "",
#     "address1": "COLMAN ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "DROITWICH",
#     "county": "WORCESTERSHIRE",
#     "latitude": 52.26794984957385,
#     "longitude": -2.1533879740866677,
#     "postcode": "WR9 8QU",
#     "geocode_coordinates": "SRID=27700;POINT (-2.153387974086668 52.26794984957385)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "R1A",
#       "name": "HEREFORDSHIRE AND WORCESTERSHIRE HEALTH AND CARE NHS TRUST",
#       "address_line_1": "UNIT 2 KINGS COURT",
#       "address_line_2": "CHARLES HASTINGS WAY",
#       "town": "WORCESTER",
#       "postcode": "WR5 1JR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000019",
#       "name": "NHS Herefordshire and Worcestershire Integrated Care Board",
#       "ods_code": "QGH"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJ6CC",
#     "name": "CROYDON COMMUNITY SERVICES",
#     "website": "",
#     "address1": "MALLING CLOSE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CROYDON",
#     "county": "SURREY",
#     "latitude": 51.38943236801409,
#     "longitude": -0.05949026304572937,
#     "postcode": "CR0 7YD",
#     "geocode_coordinates": "SRID=27700;POINT (-0.05949026304572937 51.38943236801409)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RJ6",
#       "name": "CROYDON HEALTH SERVICES NHS TRUST",
#       "address_line_1": "CROYDON UNIVERSITY HOSPITAL",
#       "address_line_2": "530 LONDON ROAD",
#       "town": "THORNTON HEATH",
#       "postcode": "CR7 7YE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000031",
#       "name": "NHS South West London Integrated Care Board",
#       "ods_code": "QWE"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJ611",
#     "name": "CROYDON UNIVERSITY HOSPITAL",
#     "website": "http://www.croydonhealthservices.nhs.uk/",
#     "address1": "LONDON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CROYDON",
#     "county": "SURREY",
#     "latitude": 51.38912964,
#     "longitude": -0.108768813,
#     "postcode": "CR7 7YE",
#     "geocode_coordinates": "SRID=27700;POINT (-0.108768813 51.38912964)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ062"
#     },
#     "trust": {
#       "ods_code": "RJ6",
#       "name": "CROYDON HEALTH SERVICES NHS TRUST",
#       "address_line_1": "CROYDON UNIVERSITY HOSPITAL",
#       "address_line_2": "530 LONDON ROAD",
#       "town": "THORNTON HEATH",
#       "postcode": "CR7 7YE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000031",
#       "name": "NHS South West London Integrated Care Board",
#       "ods_code": "QWE"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RNN62",
#     "name": "CUMBERLAND INFIRMARY",
#     "website": "",
#     "address1": "NEWTOWN ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CARLISLE",
#     "county": "CUMBRIA",
#     "latitude": 54.89650345,
#     "longitude": -2.957777023,
#     "postcode": "CA2 7HY",
#     "geocode_coordinates": "SRID=27700;POINT (-2.957777023 54.89650345)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ150"
#     },
#     "trust": {
#       "ods_code": "RNN",
#       "name": "NORTH CUMBRIA INTEGRATED CARE NHS FOUNDATION TRUST",
#       "address_line_1": "PILLARS BUILDING",
#       "address_line_2": "CUMBERLAND INFIRMARY",
#       "town": "CARLISLE",
#       "postcode": "CA2 7HY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RN707",
#     "name": "DARENT VALLEY HOSPITAL",
#     "website": "http://www.dgt.nhs.uk",
#     "address1": "DARENTH WOOD ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "DARTFORD",
#     "county": "KENT",
#     "latitude": 51.43495178,
#     "longitude": 0.258659244,
#     "postcode": "DA2 8DA",
#     "geocode_coordinates": "SRID=27700;POINT (0.258659244 51.43495178)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ119"
#     },
#     "trust": {
#       "ods_code": "RN7",
#       "name": "DARTFORD AND GRAVESHAM NHS TRUST",
#       "address_line_1": "DARENT VALLEY HOSPITAL",
#       "address_line_2": "DARENTH WOOD ROAD",
#       "town": "DARTFORD",
#       "postcode": "DA2 8DA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000032",
#       "name": "NHS Kent and Medway Integrated Care Board",
#       "ods_code": "QKS"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXPDA",
#     "name": "DARLINGTON MEMORIAL HOSPITAL",
#     "website": "http://www.cddft.nhs.uk",
#     "address1": "HOLLYHURST ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "DARLINGTON",
#     "county": "COUNTY DURHAM",
#     "latitude": 54.53037643,
#     "longitude": -1.563717365,
#     "postcode": "DL3 6HX",
#     "geocode_coordinates": "SRID=27700;POINT (-1.563717365 54.53037643)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ161"
#     },
#     "trust": {
#       "ods_code": "RXP",
#       "name": "COUNTY DURHAM AND DARLINGTON NHS FOUNDATION TRUST",
#       "address_line_1": "DARLINGTON MEMORIAL HOSPITAL",
#       "address_line_2": "HOLLYHURST ROAD",
#       "town": "DARLINGTON",
#       "postcode": "DL3 6HX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RK950",
#     "name": "DERRIFORD HOSPITAL",
#     "website": "http://www.plymouthhospitals.nhs.uk",
#     "address1": "DERRIFORD ROAD",
#     "address2": "CROWNHILL",
#     "address3": "",
#     "telephone": "",
#     "city": "PLYMOUTH",
#     "county": "DEVON",
#     "latitude": 50.41672897,
#     "longitude": -4.113671303,
#     "postcode": "PL6 8DH",
#     "geocode_coordinates": "SRID=27700;POINT (-4.113671303 50.41672897)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ096"
#     },
#     "trust": {
#       "ods_code": "RK9",
#       "name": "UNIVERSITY HOSPITALS PLYMOUTH NHS TRUST",
#       "address_line_1": "DERRIFORD HOSPITAL",
#       "address_line_2": "DERRIFORD ROAD",
#       "town": "PLYMOUTH",
#       "postcode": "PL6 8DH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000037",
#       "name": "NHS Devon Integrated Care Board",
#       "ods_code": "QJK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXF10",
#     "name": "DEWSBURY & DISTRICT HOSPITAL",
#     "website": null,
#     "address1": "HALIFAX ROAD",
#     "address2": null,
#     "address3": null,
#     "telephone": null,
#     "city": "DEWSBURY",
#     "county": null,
#     "latitude": 53.702252,
#     "longitude": -1.651877,
#     "postcode": "WF13 4HS",
#     "geocode_coordinates": "SRID=27700;POINT (-1.651877 53.702252)",
#     "active": true,
#     "published_at": "2002-04-01",
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ226"
#     },
#     "trust": {
#       "ods_code": "RXF",
#       "name": "MID YORKSHIRE HOSPITALS NHS TRUST",
#       "address_line_1": "PINDERFIELDS HOSPITAL",
#       "address_line_2": "ABERFORD ROAD",
#       "town": "WAKEFIELD",
#       "postcode": "WF1 4DG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000054",
#       "name": "NHS West Yorkshire Integrated Care Board",
#       "ods_code": "QWO"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJL30",
#     "name": "DIANA, PRINCESS OF WALES HOSPITAL",
#     "website": "http://www.nlg.nhs.uk/hospitals/grimsby",
#     "address1": "SCARTHO ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "GRIMSBY",
#     "county": "SOUTH HUMBERSIDE",
#     "latitude": 53.54485703,
#     "longitude": -0.096213497,
#     "postcode": "DN33 2BA",
#     "geocode_coordinates": "SRID=27700;POINT (-0.096213497 53.54485703)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ020"
#     },
#     "trust": {
#       "ods_code": "RJL",
#       "name": "NORTHERN LINCOLNSHIRE AND GOOLE NHS FOUNDATION TRUST",
#       "address_line_1": "DIANA PRINCESS OF WALES HOSPITAL",
#       "address_line_2": "SCARTHO ROAD",
#       "town": "GRIMSBY",
#       "postcode": "DN33 2BA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000051",
#       "name": "NHS Humber and North Yorkshire Integrated Care Board",
#       "ods_code": "QOQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Trent Epilepsy Network",
#       "boundary_identifier": "TEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RHW0C",
#     "name": "DINGLEY SPECIALIST CHILDREN'S CENTRE",
#     "website": "",
#     "address1": "ERLEGH HOUSE",
#     "address2": "UNIVERSITY OF READING",
#     "address3": "WHITEKNIGHTS ROAD",
#     "telephone": "",
#     "city": "READING",
#     "county": "",
#     "latitude": 51.442447786143,
#     "longitude": -0.9354541726665103,
#     "postcode": "RG6 6BZ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.9354541726665103 51.442447786143)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RHW",
#       "name": "ROYAL BERKSHIRE NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL BERKSHIRE HOSPITAL",
#       "address_line_2": "LONDON ROAD",
#       "town": "READING",
#       "postcode": "RG1 5AN",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000044",
#       "name": "NHS Buckinghamshire, Oxfordshire and Berkshire West Integrated Care Board",
#       "ods_code": "QU9"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RP5DR",
#     "name": "DONCASTER ROYAL INFIRMARY",
#     "website": "http://www.dbth.nhs.uk",
#     "address1": "ARMTHORPE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "DONCASTER",
#     "county": "SOUTH YORKSHIRE",
#     "latitude": 53.53078461,
#     "longitude": -1.108923912,
#     "postcode": "DN2 5LT",
#     "geocode_coordinates": "SRID=27700;POINT (-1.108923912 53.53078461)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ006"
#     },
#     "trust": {
#       "ods_code": "RP5",
#       "name": "DONCASTER AND BASSETLAW TEACHING HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "DONCASTER ROYAL INFIRMARY",
#       "address_line_2": "ARMTHORPE ROAD",
#       "town": "DONCASTER",
#       "postcode": "DN2 5LT",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000060",
#       "name": "NHS Nottingham and Nottinghamshire Integrated Care Board",
#       "ods_code": "QT1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Trent Epilepsy Network",
#       "boundary_identifier": "TEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBD01",
#     "name": "DORSET COUNTY HOSPITAL",
#     "website": "http://www.dchft.nhs.uk",
#     "address1": "WILLIAMS AVENUE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "DORCHESTER",
#     "county": "DORSET",
#     "latitude": 50.71294403,
#     "longitude": -2.446922541,
#     "postcode": "DT1 2JY",
#     "geocode_coordinates": "SRID=27700;POINT (-2.446922541 50.71294403)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ017"
#     },
#     "trust": {
#       "ods_code": "RBD",
#       "name": "DORSET COUNTY HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "DORSET COUNTY HOSPITAL",
#       "address_line_2": "WILLIAMS AVENUE",
#       "town": "DORCHESTER",
#       "postcode": "DT1 2JY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000041",
#       "name": "NHS Dorset Integrated Care Board",
#       "ods_code": "QVV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVN4T",
#     "name": "DROVE HOUSE",
#     "website": "",
#     "address1": "DROVE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WESTON-SUPER-MARE",
#     "county": "AVON",
#     "latitude": 51.33946376061602,
#     "longitude": -2.9688690485123415,
#     "postcode": "BS23 3NT",
#     "geocode_coordinates": "SRID=27700;POINT (-2.968869048512341 51.33946376061602)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RVN",
#       "name": "AVON AND WILTSHIRE MENTAL HEALTH PARTNERSHIP NHS TRUST",
#       "address_line_1": "BATH NHS HOUSE",
#       "address_line_2": "NEWBRIDGE HILL",
#       "town": "BATH",
#       "postcode": "BA1 3QE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000040",
#       "name": "NHS Bath and North East Somerset, Swindon and Wiltshire Integrated Care Board",
#       "ods_code": "QOX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1K04",
#     "name": "EALING HOSPITAL",
#     "website": "https://www.lnwh.nhs.uk/",
#     "address1": "UXBRIDGE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SOUTHALL",
#     "county": "MIDDLESEX",
#     "latitude": 51.50760651,
#     "longitude": -0.345481128,
#     "postcode": "UB1 3HW",
#     "geocode_coordinates": "SRID=27700;POINT (-0.345481128 51.50760651)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ191"
#     },
#     "trust": {
#       "ods_code": "R1K",
#       "name": "LONDON NORTH WEST UNIVERSITY HEALTHCARE NHS TRUST",
#       "address_line_1": "NORTHWICK PARK HOSPITAL",
#       "address_line_2": "WATFORD ROAD",
#       "town": "HARROW",
#       "postcode": "HA1 3UJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000027",
#       "name": "NHS North West London Integrated Care Board",
#       "ods_code": "QRV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXC02",
#     "name": "EASTBOURNE DISTRICT GENERAL HOSPITAL",
#     "website": "http://www.esht.nhs.uk/eastbournedgh",
#     "address1": "KINGS DRIVE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "EASTBOURNE",
#     "county": "EAST SUSSEX",
#     "latitude": 50.78696823,
#     "longitude": 0.271121651,
#     "postcode": "BN21 2UD",
#     "geocode_coordinates": "SRID=27700;POINT (0.271121651 50.78696823)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ230"
#     },
#     "trust": {
#       "ods_code": "RXC",
#       "name": "EAST SUSSEX HEALTHCARE NHS TRUST",
#       "address_line_1": "ST ANNES HOUSE",
#       "address_line_2": "729 THE RIDGE",
#       "town": "ST. LEONARDS-ON-SEA",
#       "postcode": "TN37 7PT",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000064",
#       "name": "NHS Sussex Integrated Care Board",
#       "ods_code": "QNX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVJT9",
#     "name": "EASTGATE HOUSE",
#     "website": "",
#     "address1": "UNIT 9",
#     "address2": "EASTGATE OFFICE CENTRE",
#     "address3": "EASTGATE ROAD",
#     "telephone": "",
#     "city": "BRISTOL",
#     "county": "AVON",
#     "latitude": 51.48515271161083,
#     "longitude": -3.1650109188615785,
#     "postcode": "BS5 6XX",
#     "geocode_coordinates": "SRID=27700;POINT (-3.165010918861578 51.48515271161083)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RVJ",
#       "name": "NORTH BRISTOL NHS TRUST",
#       "address_line_1": "SOUTHMEAD HOSPITAL",
#       "address_line_2": "SOUTHMEAD ROAD",
#       "town": "BRISTOL",
#       "postcode": "BS10 5NB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000039",
#       "name": "NHS Bristol, North Somerset and South Gloucestershire Integrated Care Board",
#       "ods_code": "QUY"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTP04",
#     "name": "EAST SURREY HOSPITAL",
#     "website": "",
#     "address1": "CANADA AVENUE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "REDHILL",
#     "county": "SURREY",
#     "latitude": 51.21919,
#     "longitude": -0.16201,
#     "postcode": "RH1 5RH",
#     "geocode_coordinates": "SRID=27700;POINT (-0.16201 51.21919)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ213"
#     },
#     "trust": {
#       "ods_code": "RTP",
#       "name": "SURREY AND SUSSEX HEALTHCARE NHS TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "EAST SURREY HOSPITAL",
#       "town": "REDHILL",
#       "postcode": "RH1 5RH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000063",
#       "name": "NHS Surrey Heartlands Integrated Care Board",
#       "ods_code": "QXU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RM332",
#     "name": "ECCLES GATEWAY",
#     "website": "",
#     "address1": "28 BARTON LANE",
#     "address2": "ECCLES",
#     "address3": "",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.482882456526816,
#     "longitude": -2.33845275607912,
#     "postcode": "M30 0TU",
#     "geocode_coordinates": "SRID=27700;POINT (-2.33845275607912 53.48288245652682)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RM3",
#       "name": "NORTHERN CARE ALLIANCE NHS FOUNDATION TRUST",
#       "address_line_1": "SALFORD ROYAL",
#       "address_line_2": "STOTT LANE",
#       "town": "SALFORD",
#       "postcode": "M6 8HD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A2P7",
#     "name": "ELIZABETH WILLIAMS CLINIC",
#     "website": "",
#     "address1": "MILL LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LLANELLI",
#     "county": "DYFED",
#     "latitude": 51.684363752680774,
#     "longitude": -4.156748736588136,
#     "postcode": "SA15 3SE",
#     "geocode_coordinates": "SRID=27700;POINT (-4.156748736588136 51.68436375268077)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A2",
#       "boundary_identifier": "W11000025",
#       "name": "Hywel Dda University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RVR50",
#     "name": "EPSOM HOSPITAL",
#     "website": "http://www.epsom-sthelier.nhs.uk",
#     "address1": "DORKING ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "EPSOM",
#     "county": "SURREY",
#     "latitude": 51.32551956,
#     "longitude": -0.273216724,
#     "postcode": "KT18 7EG",
#     "geocode_coordinates": "SRID=27700;POINT (-0.273216724 51.32551956)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ050"
#     },
#     "trust": {
#       "ods_code": "RVR",
#       "name": "EPSOM AND ST HELIER UNIVERSITY HOSPITALS NHS TRUST",
#       "address_line_1": "ST HELIER HOSPITAL",
#       "address_line_2": "WRYTHE LANE",
#       "town": "CARSHALTON",
#       "postcode": "SM5 1AA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000063",
#       "name": "NHS Surrey Heartlands Integrated Care Board",
#       "ods_code": "QXU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A1MF",
#     "name": "FLINTSHIRE CHILDREN'S CENTRE",
#     "website": "",
#     "address1": "CATHERINE GLADSTONE HOUSE",
#     "address2": "HAWARDEN WAY, MANCOT",
#     "address3": "",
#     "telephone": "",
#     "city": "DEESIDE",
#     "county": "CLWYD",
#     "latitude": 53.197806016801934,
#     "longitude": -3.013333702231281,
#     "postcode": "CH5 2EP",
#     "geocode_coordinates": "SRID=27700;POINT (-3.013333702231281 53.19780601680193)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A1",
#       "boundary_identifier": "W11000023",
#       "name": "Betsi Cadwaladr University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RTD01",
#     "name": "FREEMAN HOSPITAL",
#     "website": "http://www.newcastle-hospitals.nhs.uk/",
#     "address1": "FREEMAN ROAD",
#     "address2": "HIGH HEATON",
#     "address3": "",
#     "telephone": "",
#     "city": "NEWCASTLE UPON TYNE",
#     "county": "TYNE AND WEAR",
#     "latitude": 55.0027771,
#     "longitude": -1.593362212,
#     "postcode": "NE7 7DN",
#     "geocode_coordinates": "SRID=27700;POINT (-1.593362212 55.0027771)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTD",
#       "name": "THE NEWCASTLE UPON TYNE HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "FREEMAN HOSPITAL",
#       "address_line_2": "FREEMAN ROAD",
#       "town": "NEWCASTLE UPON TYNE",
#       "postcode": "NE7 7DN",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTR45",
#     "name": "FRIARAGE HOSPITAL SITE",
#     "website": "http://www.southtees.nhs.uk",
#     "address1": "FRIARAGE HOSPITAL",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NORTHALLERTON",
#     "county": "NORTH YORKSHIRE",
#     "latitude": 54.34233475,
#     "longitude": -1.430518746,
#     "postcode": "DL6 1JG",
#     "geocode_coordinates": "SRID=27700;POINT (-1.430518746 54.34233475)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ027"
#     },
#     "trust": {
#       "ods_code": "RTR",
#       "name": "SOUTH TEES HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "JAMES COOK UNIVERSITY HOSPITAL",
#       "address_line_2": "MARTON ROAD",
#       "town": "MIDDLESBROUGH",
#       "postcode": "TS4 3BW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000051",
#       "name": "NHS Humber and North Yorkshire Integrated Care Board",
#       "ods_code": "QOQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RDU01",
#     "name": "FRIMLEY PARK HOSPITAL",
#     "website": "https://www.fhft.nhs.uk/",
#     "address1": "PORTSMOUTH ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "FRIMLEY",
#     "county": "SURREY",
#     "latitude": 51.31966782,
#     "longitude": -0.742014408,
#     "postcode": "GU16 7UJ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.742014408 51.31966782)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ218"
#     },
#     "trust": {
#       "ods_code": "RDU",
#       "name": "FRIMLEY HEALTH NHS FOUNDATION TRUST",
#       "address_line_1": "PORTSMOUTH ROAD",
#       "address_line_2": "FRIMLEY",
#       "town": "CAMBERLEY",
#       "postcode": "GU16 7UJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000034",
#       "name": "NHS Frimley Integrated Care Board",
#       "ods_code": "QNQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTXBU",
#     "name": "FURNESS GENERAL HOSPITAL",
#     "website": "http://www.uhmb.nhs.uk",
#     "address1": "DALTON LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BARROW-IN-FURNESS",
#     "county": "CUMBRIA",
#     "latitude": 54.13640213,
#     "longitude": -3.20788455,
#     "postcode": "LA14 4LF",
#     "geocode_coordinates": "SRID=27700;POINT (-3.20788455 54.13640213)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ167"
#     },
#     "trust": {
#       "ods_code": "RTX",
#       "name": "UNIVERSITY HOSPITALS OF MORECAMBE BAY NHS FOUNDATION TRUST",
#       "address_line_1": "WESTMORLAND GENERAL HOSPITAL",
#       "address_line_2": "BURTON ROAD",
#       "town": "KENDAL",
#       "postcode": "LA9 7RG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000048",
#       "name": "NHS Lancashire and South Cumbria Integrated Care Board",
#       "ods_code": "QE1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R0B0G",
#     "name": "GALLERIES HEALTH CENTRE",
#     "website": "",
#     "address1": "HEALTH CENTRE",
#     "address2": "THE GALLERIES",
#     "address3": "WASHINGTON CENTRE",
#     "telephone": "",
#     "city": "WASHINGTON",
#     "county": "TYNE AND WEAR",
#     "latitude": 54.89882555930676,
#     "longitude": -1.5304436726140653,
#     "postcode": "NE38 7NQ",
#     "geocode_coordinates": "SRID=27700;POINT (-1.530443672614065 54.89882555930676)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "R0B",
#       "name": "SOUTH TYNESIDE AND SUNDERLAND NHS FOUNDATION TRUST",
#       "address_line_1": "SUNDERLAND ROYAL HOSPITAL",
#       "address_line_2": "KAYLL ROAD",
#       "town": "SUNDERLAND",
#       "postcode": "SR4 7TP",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RLT09",
#     "name": "GEORGE ELIOT PAEDIATRICS",
#     "website": "",
#     "address1": "COLLEGE STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NUNEATON",
#     "county": "WARWICKSHIRE",
#     "latitude": 52.51178977454635,
#     "longitude": -1.47510009235745,
#     "postcode": "CV10 7DJ",
#     "geocode_coordinates": "SRID=27700;POINT (-1.47510009235745 52.51178977454635)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ121"
#     },
#     "trust": {
#       "ods_code": "RLT",
#       "name": "GEORGE ELIOT HOSPITAL NHS TRUST",
#       "address_line_1": "LEWES HOUSE",
#       "address_line_2": "COLLEGE STREET",
#       "town": "NUNEATON",
#       "postcode": "CV10 7DJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000018",
#       "name": "NHS Coventry and Warwickshire Integrated Care Board",
#       "ods_code": "QWU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A2AA",
#     "name": "GLANGWILI HOSPITAL CHILD HEALTH SECTION",
#     "website": "",
#     "address1": "CHILD HEALTH SECTION",
#     "address2": "ADMINISTRATION BLOCK",
#     "address3": "WEST WALES GENERAL HOSPITAL",
#     "telephone": "",
#     "city": "CARMARTHEN",
#     "county": "DYFED",
#     "latitude": 51.86750511544308,
#     "longitude": -4.287558062189436,
#     "postcode": "SA31 2AF",
#     "geocode_coordinates": "SRID=27700;POINT (-4.287558062189436 51.86750511544308)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A2",
#       "boundary_identifier": "W11000025",
#       "name": "Hywel Dda University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RTE03",
#     "name": "GLOUCESTERSHIRE ROYAL HOSPITAL",
#     "website": "http://www.gloshospitals.nhs.uk",
#     "address1": "GREAT WESTERN ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "GLOUCESTER",
#     "county": "GLOUCESTERSHIRE",
#     "latitude": 51.8663826,
#     "longitude": -2.232058525,
#     "postcode": "GL1 3NN",
#     "geocode_coordinates": "SRID=27700;POINT (-2.232058525 51.8663826)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTE",
#       "name": "GLOUCESTERSHIRE HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "CHELTENHAM GENERAL HOSPITAL",
#       "address_line_2": "SANDFORD ROAD",
#       "town": "CHELTENHAM",
#       "postcode": "GL53 7AN",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000043",
#       "name": "NHS Gloucestershire Integrated Care Board",
#       "ods_code": "QR1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTK09",
#     "name": "GOLDSWORTH PARK MEDICAL CENTRE",
#     "website": "",
#     "address1": "DENTON WAY",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WOKING",
#     "county": "SURREY",
#     "latitude": 51.31890703272032,
#     "longitude": -0.5911015293992617,
#     "postcode": "GU21 3LQ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.5911015293992617 51.31890703272032)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTK",
#       "name": "ASHFORD AND ST PETER'S HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "ST PETERS HOSPITAL",
#       "address_line_2": "GUILDFORD ROAD",
#       "town": "CHERTSEY",
#       "postcode": "KT16 0PZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000063",
#       "name": "NHS Surrey Heartlands Integrated Care Board",
#       "ods_code": "QXU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RRK98",
#     "name": "GOOD HOPE HOSPITAL",
#     "website": "https://www.uhb.nhs.uk",
#     "address1": "RECTORY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SUTTON COLDFIELD",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.56736755,
#     "longitude": -1.812028766,
#     "postcode": "B75 7RR",
#     "geocode_coordinates": "SRID=27700;POINT (-1.812028766 52.56736755)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ144"
#     },
#     "trust": {
#       "ods_code": "RRK",
#       "name": "UNIVERSITY HOSPITALS BIRMINGHAM NHS FOUNDATION TRUST",
#       "address_line_1": "QUEEN ELIZABETH HOSPITAL",
#       "address_line_2": "MINDELSOHN WAY",
#       "town": "BIRMINGHAM",
#       "postcode": "B15 2GW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000055",
#       "name": "NHS Birmingham and Solihull Integrated Care Board",
#       "ods_code": "QHL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWDLP",
#     "name": "GRANTHAM & DISTRICT HOSPITAL AND COMMUNITY PAEDIATRICS",
#     "website": "",
#     "address1": "101 MANTHORPE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "GRANTHAM",
#     "county": "LINCOLNSHIRE",
#     "latitude": 52.92118212034121,
#     "longitude": -0.6399615735161382,
#     "postcode": "NG31 8DG",
#     "geocode_coordinates": "SRID=27700;POINT (-0.6399615735161382 52.92118212034121)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ168"
#     },
#     "trust": {
#       "ods_code": "RWD",
#       "name": "UNITED LINCOLNSHIRE HOSPITALS NHS TRUST",
#       "address_line_1": "LINCOLN COUNTY HOSPITAL",
#       "address_line_2": "GREETWELL ROAD",
#       "town": "LINCOLN",
#       "postcode": "LN2 5QY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000013",
#       "name": "NHS Lincolnshire Integrated Care Board",
#       "ods_code": "QJM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RP401",
#     "name": "GREAT ORMOND STREET HOSPITAL CENTRAL LONDON SITE",
#     "website": "http://www.gosh.nhs.uk",
#     "address1": "GREAT ORMOND STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.52220917,
#     "longitude": -0.119909525,
#     "postcode": "WC1N 3JH",
#     "geocode_coordinates": "SRID=27700;POINT (-0.119909525 51.52220917)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ196"
#     },
#     "trust": {
#       "ods_code": "RP4",
#       "name": "GREAT ORMOND STREET HOSPITAL FOR CHILDREN NHS FOUNDATION TRUST",
#       "address_line_1": "GREAT ORMOND STREET",
#       "address_line_2": "",
#       "town": "LONDON",
#       "postcode": "WC1N 3JH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Camden",
#       "gss_code": "E09000007"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJ1E7",
#     "name": "GSTT @ MARY SHERIDAN CHILD HEALTH CLINIC",
#     "website": "",
#     "address1": "WOODEN SPOON HOUSE",
#     "address2": "5 DUGARD WAY",
#     "address3": "KENNINGTON",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.49240809148386,
#     "longitude": -0.10466680536798287,
#     "postcode": "SE11 4TH",
#     "geocode_coordinates": "SRID=27700;POINT (-0.1046668053679829 51.49240809148386)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RJ1",
#       "name": "GUY'S AND ST THOMAS' NHS FOUNDATION TRUST",
#       "address_line_1": "ST THOMAS' HOSPITAL",
#       "address_line_2": "WESTMINSTER BRIDGE ROAD",
#       "town": "LONDON",
#       "postcode": "SE1 7EH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000030",
#       "name": "NHS South East London Integrated Care Board",
#       "ods_code": "QKK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Lambeth",
#       "gss_code": "E09000022"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RY905",
#     "name": "HAM CLINIC",
#     "website": "",
#     "address1": "ASHBURNHAM ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "RICHMOND",
#     "county": "SURREY",
#     "latitude": 51.43785081919746,
#     "longitude": -0.3146123188645736,
#     "postcode": "TW10 7NF",
#     "geocode_coordinates": "SRID=27700;POINT (-0.3146123188645736 51.43785081919746)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RY9",
#       "name": "HOUNSLOW AND RICHMOND COMMUNITY HEALTHCARE NHS TRUST",
#       "address_line_1": "THAMES HOUSE",
#       "address_line_2": "180-194 HIGH STREET",
#       "town": "TEDDINGTON",
#       "postcode": "TW11 8HU",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000031",
#       "name": "NHS South West London Integrated Care Board",
#       "ods_code": "QWE"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RYJ03",
#     "name": "HAMMERSMITH HOSPITAL",
#     "website": "https://www.imperial.nhs.uk/our-locations/hammersmith-hospital",
#     "address1": "DU CANE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.51742172,
#     "longitude": -0.234706819,
#     "postcode": "W12 0HS",
#     "geocode_coordinates": "SRID=27700;POINT (-0.234706819 51.51742172)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RYJ",
#       "name": "IMPERIAL COLLEGE HEALTHCARE NHS TRUST",
#       "address_line_1": "THE BAYS",
#       "address_line_2": "ST MARYS HOSPITAL",
#       "town": "LONDON",
#       "postcode": "W2 1BL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000027",
#       "name": "NHS North West London Integrated Care Board",
#       "ods_code": "QRV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Hammersmith and Fulham",
#       "gss_code": "E09000013"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RCD01",
#     "name": "HARROGATE DISTRICT HOSPITAL",
#     "website": "http://www.hdft.nhs.uk/",
#     "address1": "LANCASTER PARK ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HARROGATE",
#     "county": "NORTH YORKSHIRE",
#     "latitude": 53.99380875,
#     "longitude": -1.517558336,
#     "postcode": "HG2 7SX",
#     "geocode_coordinates": "SRID=27700;POINT (-1.517558336 53.99380875)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ129"
#     },
#     "trust": {
#       "ods_code": "RCD",
#       "name": "HARROGATE AND DISTRICT NHS FOUNDATION TRUST",
#       "address_line_1": "HARROGATE DISTRICT HOSPITAL",
#       "address_line_2": "LANCASTER PARK ROAD",
#       "town": "HARROGATE",
#       "postcode": "HG2 7SX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000051",
#       "name": "NHS Humber and North Yorkshire Integrated Care Board",
#       "ods_code": "QOQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RRK97",
#     "name": "HEARTLANDS HOSPITAL",
#     "website": "https://www.uhb.nhs.uk",
#     "address1": "BORDESLEY GREEN EAST",
#     "address2": "BORDESLEY GREEN",
#     "address3": "",
#     "telephone": "",
#     "city": "BIRMINGHAM",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.48022079,
#     "longitude": -1.829951048,
#     "postcode": "B9 5SS",
#     "geocode_coordinates": "SRID=27700;POINT (-1.829951048 52.48022079)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ040"
#     },
#     "trust": {
#       "ods_code": "RRK",
#       "name": "UNIVERSITY HOSPITALS BIRMINGHAM NHS FOUNDATION TRUST",
#       "address_line_1": "QUEEN ELIZABETH HOSPITAL",
#       "address_line_2": "MINDELSOHN WAY",
#       "town": "BIRMINGHAM",
#       "postcode": "B15 2GW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000055",
#       "name": "NHS Birmingham and Solihull Integrated Care Board",
#       "ods_code": "QHL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RY918",
#     "name": "HEART OF HOUNSLOW CENTRE FOR HEALTH",
#     "website": "",
#     "address1": "92 BATH ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HOUNSLOW",
#     "county": "MIDDLESEX",
#     "latitude": 51.46830184092232,
#     "longitude": -0.3709422403006183,
#     "postcode": "TW3 3EL",
#     "geocode_coordinates": "SRID=27700;POINT (-0.3709422403006183 51.46830184092232)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RY9",
#       "name": "HOUNSLOW AND RICHMOND COMMUNITY HEALTHCARE NHS TRUST",
#       "address_line_1": "THAMES HOUSE",
#       "address_line_2": "180-194 HIGH STREET",
#       "town": "TEDDINGTON",
#       "postcode": "TW11 8HU",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000031",
#       "name": "NHS South West London Integrated Care Board",
#       "ods_code": "QWE"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RDU52",
#     "name": "HEATHERWOOD HOSPITAL",
#     "website": "",
#     "address1": "BROOK AVENUE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ASCOT",
#     "county": "",
#     "latitude": 51.40828363735065,
#     "longitude": -0.685306078413111,
#     "postcode": "SL5 7GB",
#     "geocode_coordinates": "SRID=27700;POINT (-0.685306078413111 51.40828363735065)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RDU",
#       "name": "FRIMLEY HEALTH NHS FOUNDATION TRUST",
#       "address_line_1": "PORTSMOUTH ROAD",
#       "address_line_2": "FRIMLEY",
#       "town": "CAMBERLEY",
#       "postcode": "GU16 7UJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000034",
#       "name": "NHS Frimley Integrated Care Board",
#       "ods_code": "QNQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RLQ01",
#     "name": "HEREFORD COUNTY HOSPITAL",
#     "website": "http://www.wyevalley.nhs.uk",
#     "address1": "UNION WALK",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HEREFORD",
#     "county": "HEREFORDSHIRE",
#     "latitude": 52.05873489,
#     "longitude": -2.707180262,
#     "postcode": "HR1 2ER",
#     "geocode_coordinates": "SRID=27700;POINT (-2.707180262 52.05873489)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ111"
#     },
#     "trust": {
#       "ods_code": "RLQ",
#       "name": "WYE VALLEY NHS TRUST",
#       "address_line_1": "COUNTY HOSPITAL",
#       "address_line_2": "27 UNION WALK",
#       "town": "HEREFORD",
#       "postcode": "HR1 2ER",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000019",
#       "name": "NHS Herefordshire and Worcestershire Integrated Care Board",
#       "ods_code": "QGH"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWH23",
#     "name": "HERTFORD COUNTY HOSPITAL AND COMMUNITY PAEDIATRICS",
#     "website": "http://www.enherts-tr.nhs.uk/our-hospitals/hertford-county/",
#     "address1": "NORTH ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HERTFORD",
#     "county": "HERTFORDSHIRE",
#     "latitude": 51.79648972,
#     "longitude": -0.088494822,
#     "postcode": "SG14 1LP",
#     "geocode_coordinates": "SRID=27700;POINT (-0.088494822 51.79648972)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ099"
#     },
#     "trust": {
#       "ods_code": "RWH",
#       "name": "EAST AND NORTH HERTFORDSHIRE NHS TRUST",
#       "address_line_1": "LISTER HOSPITAL",
#       "address_line_2": "COREYS MILL LANE",
#       "town": "STEVENAGE",
#       "postcode": "SG1 4AB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000025",
#       "name": "NHS Hertfordshire and West Essex Integrated Care Board",
#       "ods_code": "QM7"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTFDR",
#     "name": "HEXHAM GENERAL HOSPITAL",
#     "website": "https://www.northumbria.nhs.uk/hexham",
#     "address1": "CORBRIDGE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HEXHAM",
#     "county": "NORTHUMBERLAND",
#     "latitude": 54.97036743,
#     "longitude": -2.095787287,
#     "postcode": "NE46 1QJ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.095787287 54.97036743)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTF",
#       "name": "NORTHUMBRIA HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "NORTH TYNESIDE GENERAL HOSPITAL",
#       "address_line_2": "RAKE LANE",
#       "town": "NORTH SHIELDS",
#       "postcode": "NE29 8NH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RAS01",
#     "name": "HILLINGDON HOSPITAL",
#     "website": "https://www.thh.nhs.uk",
#     "address1": "PIELD HEATH ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "UXBRIDGE",
#     "county": "MIDDLESEX",
#     "latitude": 51.52607727,
#     "longitude": -0.461160362,
#     "postcode": "UB8 3NN",
#     "geocode_coordinates": "SRID=27700;POINT (-0.461160362 51.52607727)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ102"
#     },
#     "trust": {
#       "ods_code": "RAS",
#       "name": "THE HILLINGDON HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "PIELD HEATH ROAD",
#       "address_line_2": "",
#       "town": "UXBRIDGE",
#       "postcode": "UB8 3NN",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000027",
#       "name": "NHS North West London Integrated Care Board",
#       "ods_code": "QRV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RGN90",
#     "name": "HINCHINGBROOKE HOSPITAL",
#     "website": "https://www.nwangliaft.nhs.uk/our-hospitals/hinchingbrooke-hospital/",
#     "address1": "HINCHINGBROOKE PARK",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HUNTINGDON",
#     "county": "CAMBRIDGESHIRE",
#     "latitude": 52.33335114,
#     "longitude": -0.202664033,
#     "postcode": "PE29 6NT",
#     "geocode_coordinates": "SRID=27700;POINT (-0.202664033 52.33335114)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ086"
#     },
#     "trust": {
#       "ods_code": "RGN",
#       "name": "NORTH WEST ANGLIA NHS FOUNDATION TRUST",
#       "address_line_1": "PETERBOROUGH CITY HOSPITAL",
#       "address_line_2": "BRETTON GATE",
#       "town": "PETERBOROUGH",
#       "postcode": "PE3 9GZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000056",
#       "name": "NHS Cambridgeshire and Peterborough Integrated Care Board",
#       "ods_code": "QUE"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RQXM1",
#     "name": "HOMERTON UNIVERSITY HOSPITAL",
#     "website": "http://www.homerton.nhs.uk",
#     "address1": "HOMERTON ROW",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.55063248,
#     "longitude": -0.046084356,
#     "postcode": "E9 6SR",
#     "geocode_coordinates": "SRID=27700;POINT (-0.046084356 51.55063248)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RQX",
#       "name": "HOMERTON HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "HOMERTON ROW",
#       "address_line_2": "",
#       "town": "LONDON",
#       "postcode": "E9 6SR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000029",
#       "name": "NHS North East London Integrated Care Board",
#       "ods_code": "QMF"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Hackney",
#       "gss_code": "E09000012"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTH05",
#     "name": "HORTON GENERAL HOSPITAL",
#     "website": "http://www.ouh.nhs.uk/hospitals/horton/default.aspx",
#     "address1": "OXFORD RD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BANBURY",
#     "county": "OXFORDSHIRE",
#     "latitude": 52.05348206,
#     "longitude": -1.336883426,
#     "postcode": "OX16 9AL",
#     "geocode_coordinates": "SRID=27700;POINT (-1.336883426 52.05348206)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTH",
#       "name": "OXFORD UNIVERSITY HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "JOHN RADCLIFFE HOSPITAL",
#       "address_line_2": "HEADLEY WAY",
#       "town": "OXFORD",
#       "postcode": "OX3 9DU",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000044",
#       "name": "NHS Buckinghamshire, Oxfordshire and Berkshire West Integrated Care Board",
#       "ods_code": "QU9"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RKB03",
#     "name": "HOSPITAL OF ST CROSS",
#     "website": "http://www.uhcw.nhs.uk/",
#     "address1": "BARBY RD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "RUGBY",
#     "county": "WARWICKSHIRE",
#     "latitude": 52.36527634,
#     "longitude": -1.259016037,
#     "postcode": "CV22 5PX",
#     "geocode_coordinates": "SRID=27700;POINT (-1.259016037 52.36527634)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RKB",
#       "name": "UNIVERSITY HOSPITALS COVENTRY AND WARWICKSHIRE NHS TRUST",
#       "address_line_1": "WALSGRAVE GENERAL HOSPITAL",
#       "address_line_2": "CLIFFORD BRIDGE ROAD",
#       "town": "COVENTRY",
#       "postcode": "CV2 2DX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000018",
#       "name": "NHS Coventry and Warwickshire Integrated Care Board",
#       "ods_code": "QWU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWA01",
#     "name": "HULL ROYAL INFIRMARY",
#     "website": "https://www.hey.nhs.uk/",
#     "address1": "ANLABY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HULL",
#     "county": "NORTH HUMBERSIDE",
#     "latitude": 53.74443436,
#     "longitude": -0.358168989,
#     "postcode": "HU3 2JZ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.358168989 53.74443436)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ026"
#     },
#     "trust": {
#       "ods_code": "RWA",
#       "name": "HULL UNIVERSITY TEACHING HOSPITALS NHS TRUST",
#       "address_line_1": "HULL ROYAL INFIRMARY",
#       "address_line_2": "ANLABY ROAD",
#       "town": "HULL",
#       "postcode": "HU3 2JZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000051",
#       "name": "NHS Humber and North Yorkshire Integrated Care Board",
#       "ods_code": "QOQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTG07",
#     "name": "ILKESTON COMMUNITY HOSPITAL",
#     "website": "",
#     "address1": "HEANOR ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ILKESTON",
#     "county": "DERBYSHIRE",
#     "latitude": 52.988319908650226,
#     "longitude": -1.3202010304096143,
#     "postcode": "DE7 8LN",
#     "geocode_coordinates": "SRID=27700;POINT (-1.320201030409614 52.98831990865023)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTG",
#       "name": "UNIVERSITY HOSPITALS OF DERBY AND BURTON NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL DERBY HOSPITAL",
#       "address_line_2": "UTTOXETER ROAD",
#       "town": "DERBY",
#       "postcode": "DE22 3NE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000058",
#       "name": "NHS Derby and Derbyshire Integrated Care Board",
#       "ods_code": "QJ2"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RDE03",
#     "name": "IPSWICH HOSPITAL",
#     "website": "https://www.esneft.nhs.uk",
#     "address1": "HEATH ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "IPSWICH",
#     "county": "SUFFOLK",
#     "latitude": 52.05684662,
#     "longitude": 1.197929144,
#     "postcode": "IP4 5PD",
#     "geocode_coordinates": "SRID=27700;POINT (1.197929144 52.05684662)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ181"
#     },
#     "trust": {
#       "ods_code": "RDE",
#       "name": "EAST SUFFOLK AND NORTH ESSEX NHS FOUNDATION TRUST",
#       "address_line_1": "COLCHESTER DIST GENERAL HOSPITAL",
#       "address_line_2": "TURNER ROAD",
#       "town": "COLCHESTER",
#       "postcode": "CO4 5JL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000023",
#       "name": "NHS Suffolk and North East Essex Integrated Care Board",
#       "ods_code": "QJG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RM335",
#     "name": "IRLAM MEDICAL CENTRE",
#     "website": "",
#     "address1": "MACDONALD ROAD",
#     "address2": "IRLAM",
#     "address3": "",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.437687672356965,
#     "longitude": -2.431705058942659,
#     "postcode": "M44 5LH",
#     "geocode_coordinates": "SRID=27700;POINT (-2.431705058942659 53.43768767235697)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RM3",
#       "name": "NORTHERN CARE ALLIANCE NHS FOUNDATION TRUST",
#       "address_line_1": "SALFORD ROYAL",
#       "address_line_2": "STOTT LANE",
#       "town": "SALFORD",
#       "postcode": "M6 8HD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RGP75",
#     "name": "JAMES PAGET UNIVERSITY HOSPITAL",
#     "website": "http://www.jpaget.nhs.uk/",
#     "address1": "LOWESTOFT ROAD",
#     "address2": "GORLESTON",
#     "address3": "",
#     "telephone": "",
#     "city": "GREAT YARMOUTH",
#     "county": "NORFOLK",
#     "latitude": 52.5616684,
#     "longitude": 1.717994452,
#     "postcode": "NR31 6LA",
#     "geocode_coordinates": "SRID=27700;POINT (1.717994452 52.5616684)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ127"
#     },
#     "trust": {
#       "ods_code": "RGP",
#       "name": "JAMES PAGET UNIVERSITY HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "LOWESTOFT ROAD",
#       "address_line_2": "GORLESTON",
#       "town": "GREAT YARMOUTH",
#       "postcode": "NR31 6LA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000022",
#       "name": "NHS Norfolk and Waveney Integrated Care Board",
#       "ods_code": "QMM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTH08",
#     "name": "JOHN RADCLIFFE HOSPITAL",
#     "website": "http://www.ouh.nhs.uk/hospitals/jr/default.aspx",
#     "address1": "HEADLEY WAY",
#     "address2": "HEADINGTON",
#     "address3": "",
#     "telephone": "",
#     "city": "OXFORD",
#     "county": "OXFORDSHIRE",
#     "latitude": 51.76386261,
#     "longitude": -1.219777584,
#     "postcode": "OX3 9DU",
#     "geocode_coordinates": "SRID=27700;POINT (-1.219777584 51.76386261)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ007"
#     },
#     "trust": {
#       "ods_code": "RTH",
#       "name": "OXFORD UNIVERSITY HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "JOHN RADCLIFFE HOSPITAL",
#       "address_line_2": "HEADLEY WAY",
#       "town": "OXFORD",
#       "postcode": "OX3 9DU",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000044",
#       "name": "NHS Buckinghamshire, Oxfordshire and Berkshire West Integrated Care Board",
#       "ods_code": "QU9"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVVKC",
#     "name": "KENT & CANTERBURY HOSPITAL",
#     "website": "http://www.ekhuft.nhs.uk/kentandcanterburyhospital",
#     "address1": "ETHELBERT ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CANTERBURY",
#     "county": "KENT",
#     "latitude": 51.2665863,
#     "longitude": 1.087097526,
#     "postcode": "CT1 3NG",
#     "geocode_coordinates": "SRID=27700;POINT (1.087097526 51.2665863)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ024"
#     },
#     "trust": {
#       "ods_code": "RVV",
#       "name": "EAST KENT HOSPITALS UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "KENT & CANTERBURY HOSPITAL",
#       "address_line_2": "ETHELBERT ROAD",
#       "town": "CANTERBURY",
#       "postcode": "CT1 3NG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000032",
#       "name": "NHS Kent and Medway Integrated Care Board",
#       "ods_code": "QKS"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RNQ51",
#     "name": "KETTERING GENERAL HOSPITAL",
#     "website": "http://www.kgh.nhs.uk",
#     "address1": "ROTHWELL RD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "KETTERING",
#     "county": "NORTHAMPTONSHIRE",
#     "latitude": 52.40114594,
#     "longitude": -0.741529107,
#     "postcode": "NN16 8UZ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.741529107 52.40114594)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ174"
#     },
#     "trust": {
#       "ods_code": "RNQ",
#       "name": "KETTERING GENERAL HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "ROTHWELL ROAD",
#       "address_line_2": "",
#       "town": "KETTERING",
#       "postcode": "NN16 8UZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000059",
#       "name": "NHS Northamptonshire Integrated Care Board",
#       "ods_code": "QPM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWP31",
#     "name": "KIDDERMINSTER HOSPITAL",
#     "website": null,
#     "address1": "BEWDLEY ROAD",
#     "address2": null,
#     "address3": null,
#     "telephone": null,
#     "city": "KIDDERMINSTER",
#     "county": null,
#     "latitude": 52.386056,
#     "longitude": -2.261161,
#     "postcode": "DY11 6RJ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.261161 52.386056)",
#     "active": true,
#     "published_at": "2000-04-01",
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ084"
#     },
#     "trust": {
#       "ods_code": "RWP",
#       "name": "WORCESTERSHIRE ACUTE HOSPITALS NHS TRUST",
#       "address_line_1": "WORCESTERSHIRE ROYAL HOSPITAL",
#       "address_line_2": "CHARLES HASTINGS WAY",
#       "town": "WORCESTER",
#       "postcode": "WR5 1DD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000019",
#       "name": "NHS Herefordshire and Worcestershire Integrated Care Board",
#       "ods_code": "QGH"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJZ01",
#     "name": "KING'S COLLEGE HOSPITAL (DENMARK HILL)",
#     "website": "http://www.kch.nhs.uk",
#     "address1": "DENMARK HILL",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.46807861,
#     "longitude": -0.093901388,
#     "postcode": "SE5 9RS",
#     "geocode_coordinates": "SRID=27700;POINT (-0.093901388 51.46807861)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ215"
#     },
#     "trust": {
#       "ods_code": "RJZ",
#       "name": "KING'S COLLEGE HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "DENMARK HILL",
#       "address_line_2": "",
#       "town": "LONDON",
#       "postcode": "SE5 9RS",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000030",
#       "name": "NHS South East London Integrated Care Board",
#       "ods_code": "QKK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Lambeth",
#       "gss_code": "E09000022"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RK5BC",
#     "name": "KING'S MILL HOSPITAL",
#     "website": "http://www.sfh-tr.nhs.uk",
#     "address1": "MANSFIELD ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SUTTON-IN-ASHFIELD",
#     "county": "NOTTINGHAMSHIRE",
#     "latitude": 53.13455582,
#     "longitude": -1.233566165,
#     "postcode": "NG17 4JL",
#     "geocode_coordinates": "SRID=27700;POINT (-1.233566165 53.13455582)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ180"
#     },
#     "trust": {
#       "ods_code": "RK5",
#       "name": "SHERWOOD FOREST HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "KINGS MILL HOSPITAL",
#       "address_line_2": "MANSFIELD ROAD",
#       "town": "SUTTON-IN-ASHFIELD",
#       "postcode": "NG17 4JL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000060",
#       "name": "NHS Nottingham and Nottinghamshire Integrated Care Board",
#       "ods_code": "QT1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RAX01",
#     "name": "KINGSTON HOSPITAL",
#     "website": "http://www.kingstonhospital.nhs.uk/",
#     "address1": "GALSWORTHY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "KINGSTON UPON THAMES",
#     "county": "SURREY",
#     "latitude": 51.41482544,
#     "longitude": -0.282609493,
#     "postcode": "KT2 7QB",
#     "geocode_coordinates": "SRID=27700;POINT (-0.282609493 51.41482544)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ057"
#     },
#     "trust": {
#       "ods_code": "RAX",
#       "name": "KINGSTON HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "GALSWORTHY ROAD",
#       "address_line_2": "",
#       "town": "KINGSTON UPON THAMES",
#       "postcode": "KT2 7QB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000063",
#       "name": "NHS Surrey Heartlands Integrated Care Board",
#       "ods_code": "QXU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVNE6",
#     "name": "KINGSWOOD HUB",
#     "website": "",
#     "address1": "ALMA ROAD",
#     "address2": "KINGSWOOD",
#     "address3": "",
#     "telephone": "",
#     "city": "BRISTOL",
#     "county": "AVON",
#     "latitude": 51.463190232745326,
#     "longitude": -2.499945216472451,
#     "postcode": "BS15 4DA",
#     "geocode_coordinates": "SRID=27700;POINT (-2.499945216472451 51.46319023274533)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RVN",
#       "name": "AVON AND WILTSHIRE MENTAL HEALTH PARTNERSHIP NHS TRUST",
#       "address_line_1": "BATH NHS HOUSE",
#       "address_line_2": "NEWBRIDGE HILL",
#       "town": "BATH",
#       "postcode": "BA1 3QE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000040",
#       "name": "NHS Bath and North East Somerset, Swindon and Wiltshire Integrated Care Board",
#       "ods_code": "QOX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RK5CP",
#     "name": "KMH COMMUNITY PAEDIATRICIANS",
#     "website": "http://www.sfh-tr.nhs.uk",
#     "address1": "KINGS MILL HOSPITAL",
#     "address2": "MANSFIELD ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "SUTTON-IN-ASHFIELD",
#     "county": "NOTTINGHAMSHIRE",
#     "latitude": 53.13455582,
#     "longitude": -1.233566165,
#     "postcode": "NG17 4JL",
#     "geocode_coordinates": "SRID=27700;POINT (-1.233566165 53.13455582)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RK5",
#       "name": "SHERWOOD FOREST HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "KINGS MILL HOSPITAL",
#       "address_line_2": "MANSFIELD ROAD",
#       "town": "SUTTON-IN-ASHFIELD",
#       "postcode": "NG17 4JL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000060",
#       "name": "NHS Nottingham and Nottinghamshire Integrated Care Board",
#       "ods_code": "QT1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RR801",
#     "name": "LEEDS GENERAL INFIRMARY",
#     "website": "http://www.leedsth.nhs.uk",
#     "address1": "GREAT GEORGE STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LEEDS",
#     "county": "WEST YORKSHIRE",
#     "latitude": 53.80146027,
#     "longitude": -1.552119255,
#     "postcode": "LS1 3EX",
#     "geocode_coordinates": "SRID=27700;POINT (-1.552119255 53.80146027)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ101"
#     },
#     "trust": {
#       "ods_code": "RR8",
#       "name": "LEEDS TEACHING HOSPITALS NHS TRUST",
#       "address_line_1": "ST. JAMES'S UNIVERSITY HOSPITAL",
#       "address_line_2": "BECKETT STREET",
#       "town": "LEEDS",
#       "postcode": "LS9 7TF",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000054",
#       "name": "NHS West Yorkshire Integrated Care Board",
#       "ods_code": "QWO"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWEAA",
#     "name": "LEICESTER ROYAL INFIRMARY",
#     "website": "http://www.leicestershospitals.nhs.uk",
#     "address1": "INFIRMARY SQUARE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LEICESTER",
#     "county": "LEICESTERSHIRE",
#     "latitude": 52.62678528,
#     "longitude": -1.135946155,
#     "postcode": "LE1 5WW",
#     "geocode_coordinates": "SRID=27700;POINT (-1.135946155 52.62678528)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ055"
#     },
#     "trust": {
#       "ods_code": "RWE",
#       "name": "UNIVERSITY HOSPITALS OF LEICESTER NHS TRUST",
#       "address_line_1": "LEICESTER ROYAL INFIRMARY",
#       "address_line_2": "INFIRMARY SQUARE",
#       "town": "LEICESTER",
#       "postcode": "LE1 5WW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000015",
#       "name": "NHS Leicester, Leicestershire and Rutland Integrated Care Board",
#       "ods_code": "QK1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBT20",
#     "name": "LEIGHTON HOSPITAL",
#     "website": "http://www.mchft.nhs.uk",
#     "address1": "LEIGHTON",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CREWE",
#     "county": "CHESHIRE",
#     "latitude": 53.11769104,
#     "longitude": -2.475848436,
#     "postcode": "CW1 4QJ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.475848436 53.11769104)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ030"
#     },
#     "trust": {
#       "ods_code": "RBT",
#       "name": "MID CHESHIRE HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "LEIGHTON HOSPITAL",
#       "address_line_2": "LEIGHTON",
#       "town": "CREWE",
#       "postcode": "CW1 4QJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJC79",
#     "name": "LILLINGTON CHILDRENS CENTRE",
#     "website": "",
#     "address1": "CROWN WAY CLINIC",
#     "address2": "CROWN WAY",
#     "address3": "LILLINGTON",
#     "telephone": "",
#     "city": "LEAMINGTON SPA",
#     "county": "WARWICKSHIRE",
#     "latitude": 52.303557274248234,
#     "longitude": -1.519704461685684,
#     "postcode": "CV32 7SF",
#     "geocode_coordinates": "SRID=27700;POINT (-1.519704461685684 52.30355727424823)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RJC",
#       "name": "SOUTH WARWICKSHIRE UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "WARWICK HOSPITAL",
#       "address_line_2": "LAKIN ROAD",
#       "town": "WARWICK",
#       "postcode": "CV34 5BW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000018",
#       "name": "NHS Coventry and Warwickshire Integrated Care Board",
#       "ods_code": "QWU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWDDA",
#     "name": "LINCOLN COUNTY HOSPITAL AND COMMUNITY PAEDIATRICS",
#     "website": "http://www.ulh.nhs.uk",
#     "address1": "GREETWELL ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LINCOLN",
#     "county": "LINCOLNSHIRE",
#     "latitude": 53.23357773,
#     "longitude": -0.51962018,
#     "postcode": "LN2 5QY",
#     "geocode_coordinates": "SRID=27700;POINT (-0.51962018 53.23357773)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ048"
#     },
#     "trust": {
#       "ods_code": "RWD",
#       "name": "UNITED LINCOLNSHIRE HOSPITALS NHS TRUST",
#       "address_line_1": "LINCOLN COUNTY HOSPITAL",
#       "address_line_2": "GREETWELL ROAD",
#       "town": "LINCOLN",
#       "postcode": "LN2 5QY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000013",
#       "name": "NHS Lincolnshire Integrated Care Board",
#       "ods_code": "QJM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWH01",
#     "name": "LISTER HOSPITAL AND COMMUNITY PAEDIATRICS",
#     "website": "http://www.enherts-tr.nhs.uk",
#     "address1": "COREYS MILL LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "STEVENAGE",
#     "county": "HERTFORDSHIRE",
#     "latitude": 51.92461014,
#     "longitude": -0.212711543,
#     "postcode": "SG1 4AB",
#     "geocode_coordinates": "SRID=27700;POINT (-0.212711543 51.92461014)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ099"
#     },
#     "trust": {
#       "ods_code": "RWH",
#       "name": "EAST AND NORTH HERTFORDSHIRE NHS TRUST",
#       "address_line_1": "LISTER HOSPITAL",
#       "address_line_2": "COREYS MILL LANE",
#       "town": "STEVENAGE",
#       "postcode": "SG1 4AB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000025",
#       "name": "NHS Hertfordshire and West Essex Integrated Care Board",
#       "ods_code": "QM7"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RGT2X",
#     "name": "LUTON AND DUNSTABLE UNIVERSITY HOSPITAL",
#     "website": null,
#     "address1": "LEWSEY ROAD",
#     "address2": null,
#     "address3": null,
#     "telephone": null,
#     "city": "LUTON",
#     "county": null,
#     "latitude": 51.894292,
#     "longitude": -0.474153,
#     "postcode": "LU4 0DZ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.474153 51.894292)",
#     "active": true,
#     "published_at": "2017-10-01",
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ220"
#     },
#     "trust": {
#       "ods_code": "RGT",
#       "name": "CAMBRIDGE UNIVERSITY HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "CAMBRIDGE BIOMEDICAL CAMPUS",
#       "address_line_2": "HILLS ROAD",
#       "town": "CAMBRIDGE",
#       "postcode": "CB2 0QQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000056",
#       "name": "NHS Cambridgeshire and Peterborough Integrated Care Board",
#       "ods_code": "QUE"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RC971",
#     "name": "LUTON & DUNSTABLE HOSPITAL",
#     "website": "https://www.ldh.nhs.uk/",
#     "address1": "LEWSEY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LUTON",
#     "county": "BEDFORDSHIRE",
#     "latitude": 51.89428329,
#     "longitude": -0.474163622,
#     "postcode": "LU4 0DZ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.474163622 51.89428329)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ010"
#     },
#     "trust": {
#       "ods_code": "RC9",
#       "name": "BEDFORDSHIRE HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "LEWSEY ROAD",
#       "address_line_2": "",
#       "town": "LUTON",
#       "postcode": "LU4 0DZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000024",
#       "name": "NHS Bedfordshire, Luton and Milton Keynes Integrated Care Board",
#       "ods_code": "QHG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RW1Y0",
#     "name": "LYMINGTON HOSPITAL",
#     "website": "",
#     "address1": "AMPRESS PARK",
#     "address2": "WELLWORTHY ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "LYMINGTON",
#     "county": "HAMPSHIRE",
#     "latitude": 50.76950814986551,
#     "longitude": -1.5442285268512799,
#     "postcode": "SO41 8QD",
#     "geocode_coordinates": "SRID=27700;POINT (-1.54422852685128 50.76950814986551)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RW1",
#       "name": "SOUTHERN HEALTH NHS FOUNDATION TRUST",
#       "address_line_1": "TATCHBURY MOUNT HOSPITAL",
#       "address_line_2": "CALMORE",
#       "town": "SOUTHAMPTON",
#       "postcode": "SO40 2RZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJN71",
#     "name": "MACCLESFIELD DISTRICT GENERAL HOSPITAL",
#     "website": "http://www.eastcheshire.nhs.uk",
#     "address1": "VICTORIA ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "MACCLESFIELD",
#     "county": "CHESHIRE",
#     "latitude": 53.26232529,
#     "longitude": -2.141059637,
#     "postcode": "SK10 3BL",
#     "geocode_coordinates": "SRID=27700;POINT (-2.141059637 53.26232529)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ009"
#     },
#     "trust": {
#       "ods_code": "RJN",
#       "name": "EAST CHESHIRE NHS TRUST",
#       "address_line_1": "MACCLESFIELD DISTRICT HOSPITAL",
#       "address_line_2": "VICTORIA ROAD",
#       "town": "MACCLESFIELD",
#       "postcode": "SK10 3BL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RCBL8",
#     "name": "MALTON COMMUNITY HOSPITAL",
#     "website": "http://www.york.nhs.uk",
#     "address1": "MIDDLECAVE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "MALTON",
#     "county": "NORTH YORKSHIRE",
#     "latitude": 54.13724518,
#     "longitude": -0.806531847,
#     "postcode": "YO17 7NG",
#     "geocode_coordinates": "SRID=27700;POINT (-0.806531847 54.13724518)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RCB",
#       "name": "YORK AND SCARBOROUGH TEACHING HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "YORK HOSPITAL",
#       "address_line_2": "WIGGINTON ROAD",
#       "town": "YORK",
#       "postcode": "YO31 8HE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000051",
#       "name": "NHS Humber and North Yorkshire Integrated Care Board",
#       "ods_code": "QOQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "COX3P",
#     "name": "MANCHESTER LOCAL CARE ORGANISATION",
#     "website": "",
#     "address1": "5TH FLOOR, BRIDGEWATER HOUSE",
#     "address2": "58-60 WHITWORTH STREET",
#     "address3": "",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.4752,
#     "longitude": -2.24016,
#     "postcode": "M1 6LT",
#     "geocode_coordinates": "SRID=27700;POINT (-2.24016 53.4752)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ136"
#     },
#     "trust": {
#       "ods_code": "R0A",
#       "name": "MANCHESTER UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "COBBETT HOUSE",
#       "address_line_2": "OXFORD ROAD",
#       "town": "MANCHESTER",
#       "postcode": "M13 9WL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBK02",
#     "name": "MANOR HOSPITAL",
#     "website": "http://www.walsallhealthcare.nhs.uk",
#     "address1": "MOAT ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WALSALL",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.58233261,
#     "longitude": -1.998909116,
#     "postcode": "WS2 9PS",
#     "geocode_coordinates": "SRID=27700;POINT (-1.998909116 52.58233261)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ178"
#     },
#     "trust": {
#       "ods_code": "RBK",
#       "name": "WALSALL HEALTHCARE NHS TRUST",
#       "address_line_1": "MANOR HOSPITAL",
#       "address_line_2": "MOAT ROAD",
#       "town": "WALSALL",
#       "postcode": "WS2 9PS",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000062",
#       "name": "NHS Black Country Integrated Care Board",
#       "ods_code": "QUA"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RPA02",
#     "name": "MEDWAY MARITIME HOSPITAL",
#     "website": "",
#     "address1": "WINDMILL ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "GILLINGHAM",
#     "county": "KENT",
#     "latitude": 51.37986,
#     "longitude": 0.54206,
#     "postcode": "ME7 5NY",
#     "geocode_coordinates": "SRID=27700;POINT (0.54206 51.37986)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ126"
#     },
#     "trust": {
#       "ods_code": "RPA",
#       "name": "MEDWAY NHS FOUNDATION TRUST",
#       "address_line_1": "MEDWAY MARITIME HOSPITAL",
#       "address_line_2": "WINDMILL ROAD",
#       "town": "GILLINGHAM",
#       "postcode": "ME7 5NY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000032",
#       "name": "NHS Kent and Medway Integrated Care Board",
#       "ods_code": "QKS"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "I3W1A",
#     "name": "MIDLAND METROPOLITAN UNIVERSITY HOSPITAL",
#     "website": "",
#     "address1": "GROVE LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SMETHWICK",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.491258,
#     "longitude": -1.949846,
#     "postcode": "B66 2QT",
#     "geocode_coordinates": "SRID=27700;POINT (-1.949846 52.491258)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RXK",
#       "name": "SANDWELL AND WEST BIRMINGHAM HOSPITALS NHS TRUST",
#       "address_line_1": "CITY HOSPITAL",
#       "address_line_2": "DUDLEY ROAD",
#       "town": "BIRMINGHAM",
#       "postcode": "B18 7QH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000055",
#       "name": "NHS Birmingham and Solihull Integrated Care Board",
#       "ods_code": "QHL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RD816",
#     "name": "MILTON KEYNES HOSPITAL",
#     "website": "http://www.mkuh.nhs.uk",
#     "address1": "STANDING WAY",
#     "address2": "EAGLESTONE",
#     "address3": "",
#     "telephone": "",
#     "city": "MILTON KEYNES",
#     "county": "BUCKINGHAMSHIRE",
#     "latitude": 52.02637482,
#     "longitude": -0.73576653,
#     "postcode": "MK6 5LD",
#     "geocode_coordinates": "SRID=27700;POINT (-0.73576653 52.02637482)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ145"
#     },
#     "trust": {
#       "ods_code": "RD8",
#       "name": "MILTON KEYNES UNIVERSITY HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "STANDING WAY",
#       "address_line_2": "EAGLESTONE",
#       "town": "MILTON KEYNES",
#       "postcode": "MK6 5LD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000024",
#       "name": "NHS Bedfordshire, Luton and Milton Keynes Integrated Care Board",
#       "ods_code": "QHG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RD825",
#     "name": "MKGH COMMUNITY PAEDIATRICS TEAM",
#     "website": "",
#     "address1": "MILTON KEYNES GENERAL HOSPITAL",
#     "address2": "STANDING WAY",
#     "address3": "EAGLESTONE",
#     "telephone": "",
#     "city": "MILTON KEYNES",
#     "county": "BUCKINGHAMSHIRE",
#     "latitude": 52.02494542953305,
#     "longitude": -0.7362993875660501,
#     "postcode": "MK6 5LD",
#     "geocode_coordinates": "SRID=27700;POINT (-0.7362993875660501 52.02494542953305)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RD8",
#       "name": "MILTON KEYNES UNIVERSITY HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "STANDING WAY",
#       "address_line_2": "EAGLESTONE",
#       "town": "MILTON KEYNES",
#       "postcode": "MK6 5LD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000024",
#       "name": "NHS Bedfordshire, Luton and Milton Keynes Integrated Care Board",
#       "ods_code": "QHG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RN351",
#     "name": "MOREDON MEDICAL CENTRE",
#     "website": "",
#     "address1": "MOREDON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SWINDON",
#     "county": "",
#     "latitude": 51.58372293121609,
#     "longitude": -1.8112139471060151,
#     "postcode": "SN2 2JG",
#     "geocode_coordinates": "SRID=27700;POINT (-1.811213947106015 51.58372293121609)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RN3",
#       "name": "GREAT WESTERN HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "GREAT WESTERN HOSPITAL",
#       "address_line_2": "MARLBOROUGH ROAD",
#       "town": "SWINDON",
#       "postcode": "SN3 6BB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000040",
#       "name": "NHS Bath and North East Somerset, Swindon and Wiltshire Integrated Care Board",
#       "ods_code": "QOX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A3C7",
#     "name": "MORRISTON HOSPITAL",
#     "website": "",
#     "address1": "HEOL MAES EGLWYS",
#     "address2": "CWMRHYDYCEIRW",
#     "address3": "",
#     "telephone": "",
#     "city": "SWANSEA",
#     "county": "WEST GLAMORGAN",
#     "latitude": 51.68358816236783,
#     "longitude": -3.9342430863145736,
#     "postcode": "SA6 6NL",
#     "geocode_coordinates": "SRID=27700;POINT (-3.934243086314574 51.68358816236783)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A3",
#       "boundary_identifier": "W11000031",
#       "name": "Swansea Bay University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RV3F3",
#     "name": "MOSAIC CHILDRENS CENTRE",
#     "website": "",
#     "address1": "KENTISH TOWN HEALTH CENTRE",
#     "address2": "2 BARTHOLOMEW ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.54647338497589,
#     "longitude": -0.13911479241869015,
#     "postcode": "NW5 2BX",
#     "geocode_coordinates": "SRID=27700;POINT (-0.1391147924186902 51.54647338497589)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RV3",
#       "name": "CENTRAL AND NORTH WEST LONDON NHS FOUNDATION TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "350 EUSTON ROAD",
#       "town": "LONDON",
#       "postcode": "NW1 3AX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Camden",
#       "gss_code": "E09000007"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RK901",
#     "name": "MOUNT GOULD HOSPITAL",
#     "website": "",
#     "address1": "MOUNT GOULD ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "PLYMOUTH",
#     "county": "DEVON",
#     "latitude": 50.37910560957554,
#     "longitude": -4.112683344124941,
#     "postcode": "PL4 7QD",
#     "geocode_coordinates": "SRID=27700;POINT (-4.112683344124941 50.37910560957554)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RK9",
#       "name": "UNIVERSITY HOSPITALS PLYMOUTH NHS TRUST",
#       "address_line_1": "DERRIFORD HOSPITAL",
#       "address_line_2": "DERRIFORD ROAD",
#       "town": "PLYMOUTH",
#       "postcode": "PL6 8DH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000037",
#       "name": "NHS Devon Integrated Care Board",
#       "ods_code": "QJK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RH5A8",
#     "name": "MUSGROVE PARK HOSPITAL",
#     "website": "",
#     "address1": "MUSGROVE PARK",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "TAUNTON",
#     "county": "",
#     "latitude": 51.01144171713463,
#     "longitude": -3.121313219854067,
#     "postcode": "TA1 5DA",
#     "geocode_coordinates": "SRID=27700;POINT (-3.121313219854067 51.01144171713463)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ137"
#     },
#     "trust": {
#       "ods_code": "RH5",
#       "name": "SOMERSET NHS FOUNDATION TRUST",
#       "address_line_1": "TRUST MANAGEMENT",
#       "address_line_2": "LYDEARD HOUSE",
#       "town": "TAUNTON",
#       "postcode": "TA1 5DA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000038",
#       "name": "NHS Somerset Integrated Care Board",
#       "ods_code": "QSL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A3CJ",
#     "name": "NEATH PORT TALBOT HOSPITAL",
#     "website": "",
#     "address1": "BAGLAN WAY",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "PORT TALBOT",
#     "county": "WEST GLAMORGAN",
#     "latitude": 51.59929960775662,
#     "longitude": -3.7997706458406086,
#     "postcode": "SA12 7BX",
#     "geocode_coordinates": "SRID=27700;POINT (-3.799770645840609 51.59929960775662)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A3",
#       "boundary_identifier": "W11000031",
#       "name": "Swansea Bay University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "7A623",
#     "name": "NEVILL HALL CHILDRENS CENTRE",
#     "website": "",
#     "address1": "BRECON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ABERGAVENNY",
#     "county": "",
#     "latitude": 51.82444440250398,
#     "longitude": -3.0326164868528998,
#     "postcode": "NP7 7EG",
#     "geocode_coordinates": "SRID=27700;POINT (-3.0326164868529 51.82444440250398)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A6",
#       "boundary_identifier": "W11000028",
#       "name": "Aneurin Bevan University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RK5HP",
#     "name": "NEWARK HOSPITAL",
#     "website": "",
#     "address1": "BOUNDARY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NEWARK",
#     "county": "NOTTINGHAMSHIRE",
#     "latitude": 53.06751,
#     "longitude": -0.80616,
#     "postcode": "NG24 4DE",
#     "geocode_coordinates": "SRID=27700;POINT (-0.80616 53.06751)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RK5",
#       "name": "SHERWOOD FOREST HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "KINGS MILL HOSPITAL",
#       "address_line_2": "MANSFIELD ROAD",
#       "town": "SUTTON-IN-ASHFIELD",
#       "postcode": "NG17 4JL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000060",
#       "name": "NHS Nottingham and Nottinghamshire Integrated Care Board",
#       "ods_code": "QT1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RL403",
#     "name": "NEW CROSS HOSPITAL",
#     "website": "http://www.royalwolverhampton.nhs.uk/",
#     "address1": "WOLVERHAMPTON ROAD",
#     "address2": "HEATH TOWN",
#     "address3": "",
#     "telephone": "",
#     "city": "WOLVERHAMPTON",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.59972763,
#     "longitude": -2.095540524,
#     "postcode": "WV10 0QP",
#     "geocode_coordinates": "SRID=27700;POINT (-2.095540524 52.59972763)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ222"
#     },
#     "trust": {
#       "ods_code": "RL4",
#       "name": "THE ROYAL WOLVERHAMPTON NHS TRUST",
#       "address_line_1": "NEW CROSS HOSPITAL",
#       "address_line_2": "WOLVERHAMPTON ROAD",
#       "town": "WOLVERHAMPTON",
#       "postcode": "WV10 0QP",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000062",
#       "name": "NHS Black Country Integrated Care Board",
#       "ods_code": "QUA"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1HNH",
#     "name": "NEWHAM GENERAL HOSPITAL",
#     "website": "http://www.bartshealth.nhs.uk",
#     "address1": "GLEN ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.52277756,
#     "longitude": 0.034731604,
#     "postcode": "E13 8SL",
#     "geocode_coordinates": "SRID=27700;POINT (0.034731604 51.52277756)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ058"
#     },
#     "trust": {
#       "ods_code": "R1H",
#       "name": "BARTS HEALTH NHS TRUST",
#       "address_line_1": "THE ROYAL LONDON HOSPITAL",
#       "address_line_2": "80 NEWARK STREET",
#       "town": "LONDON",
#       "postcode": "E1 2ES",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000029",
#       "name": "NHS North East London Integrated Care Board",
#       "ods_code": "QMF"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Newham",
#       "gss_code": "E09000025"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RY8NA",
#     "name": "NEWHOLME HOSPITAL",
#     "website": "http://www.dchs.nhs.uk/home_redesign/our-services/find_services_by_location/newholmehospital/",
#     "address1": "BASLOW ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BAKEWELL",
#     "county": "DERBYSHIRE",
#     "latitude": 53.21879578,
#     "longitude": -1.672325253,
#     "postcode": "DE45 1AD",
#     "geocode_coordinates": "SRID=27700;POINT (-1.672325253 53.21879578)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RY8",
#       "name": "DERBYSHIRE COMMUNITY HEALTH SERVICES NHS FOUNDATION TRUST",
#       "address_line_1": "TRUST HQ, ASH GREEN DISABILITY CTR",
#       "address_line_2": "ASHGATE ROAD",
#       "town": "CHESTERFIELD",
#       "postcode": "S42 7JE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000058",
#       "name": "NHS Derby and Derbyshire Integrated Care Board",
#       "ods_code": "QJ2"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBK58",
#     "name": "NEW INVENTION HEALTH CENTRE",
#     "website": "",
#     "address1": "66 CANNOCK ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WILLENHALL",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.60933623348631,
#     "longitude": -2.039815918790231,
#     "postcode": "WV12 5RZ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.039815918790231 52.60933623348631)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RBK",
#       "name": "WALSALL HEALTHCARE NHS TRUST",
#       "address_line_1": "MANOR HOSPITAL",
#       "address_line_2": "MOAT ROAD",
#       "town": "WALSALL",
#       "postcode": "WS2 9PS",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000062",
#       "name": "NHS Black Country Integrated Care Board",
#       "ods_code": "QUA"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A4H1",
#     "name": "NOAHS ARK CHILDRENS HOSPITAL FOR WALES",
#     "website": "",
#     "address1": "CARDIFF & VALE UNIVERSITY HEALTH BD",
#     "address2": "HEATH PARK",
#     "address3": "",
#     "telephone": "",
#     "city": "CARDIFF",
#     "county": "SOUTH GLAMORGAN",
#     "latitude": 51.50821561439174,
#     "longitude": -3.187478640298089,
#     "postcode": "CF14 4XW",
#     "geocode_coordinates": "SRID=27700;POINT (-3.187478640298089 51.50821561439174)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A4",
#       "boundary_identifier": "W11000029",
#       "name": "Cardiff and Vale University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RM102",
#     "name": "NORFOLK & NORWICH UNIVERSITY HOSPITAL",
#     "website": "http://www.nnuh.nhs.uk",
#     "address1": "COLNEY LANE",
#     "address2": "COLNEY",
#     "address3": "",
#     "telephone": "",
#     "city": "NORWICH",
#     "county": "NORFOLK",
#     "latitude": 52.61754227,
#     "longitude": 1.22118938,
#     "postcode": "NR4 7UY",
#     "geocode_coordinates": "SRID=27700;POINT (1.22118938 52.61754227)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ002"
#     },
#     "trust": {
#       "ods_code": "RM1",
#       "name": "NORFOLK AND NORWICH UNIVERSITY HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "COLNEY LANE",
#       "address_line_2": "COLNEY",
#       "town": "NORWICH",
#       "postcode": "NR4 7UY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000022",
#       "name": "NHS Norfolk and Waveney Integrated Care Board",
#       "ods_code": "QMM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RNS01",
#     "name": "NORTHAMPTON GENERAL HOSPITAL (ACUTE)",
#     "website": "",
#     "address1": "CLIFTONVILLE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NORTHAMPTON",
#     "county": "NORTHAMPTONSHIRE",
#     "latitude": 52.23605347,
#     "longitude": -0.883829474,
#     "postcode": "NN1 5BD",
#     "geocode_coordinates": "SRID=27700;POINT (-0.883829474 52.23605347)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ004"
#     },
#     "trust": {
#       "ods_code": "RNS",
#       "name": "NORTHAMPTON GENERAL HOSPITAL NHS TRUST",
#       "address_line_1": "CLIFTONVILLE",
#       "address_line_2": "",
#       "town": "NORTHAMPTON",
#       "postcode": "NN1 5BD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000059",
#       "name": "NHS Northamptonshire Integrated Care Board",
#       "ods_code": "QPM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RH880",
#     "name": "NORTH DEVON DISTRICT HOSPITAL",
#     "website": "",
#     "address1": "RALEIGH PARK",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BARNSTAPLE",
#     "county": "DEVON",
#     "latitude": 51.09169453822436,
#     "longitude": -4.050650933822214,
#     "postcode": "EX31 4JB",
#     "geocode_coordinates": "SRID=27700;POINT (-4.050650933822214 51.09169453822436)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ100"
#     },
#     "trust": {
#       "ods_code": "RH8",
#       "name": "ROYAL DEVON UNIVERSITY HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL DEVON UNIVERSITY NHS FT",
#       "address_line_2": "BARRACK ROAD",
#       "town": "EXETER",
#       "postcode": "EX2 5DW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000037",
#       "name": "NHS Devon Integrated Care Board",
#       "ods_code": "QJK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R0A66",
#     "name": "NORTH MANCHESTER GENERAL HOSPITAL",
#     "website": "",
#     "address1": "DELAUNAYS ROAD",
#     "address2": "CRUMPSALL",
#     "address3": "",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.51753825484743,
#     "longitude": -2.227934753662899,
#     "postcode": "M8 5RB",
#     "geocode_coordinates": "SRID=27700;POINT (-2.227934753662899 53.51753825484743)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ136"
#     },
#     "trust": {
#       "ods_code": "R0A",
#       "name": "MANCHESTER UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "COBBETT HOUSE",
#       "address_line_2": "OXFORD ROAD",
#       "town": "MANCHESTER",
#       "postcode": "M13 9WL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RAPNM",
#     "name": "NORTH MIDDLESEX HOSPITAL",
#     "website": "http://www.northmid.nhs.uk",
#     "address1": "STERLING WAY",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.61309433,
#     "longitude": -0.07373514,
#     "postcode": "N18 1QX",
#     "geocode_coordinates": "SRID=27700;POINT (-0.07373514 51.61309433)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ199"
#     },
#     "trust": {
#       "ods_code": "RAP",
#       "name": "NORTH MIDDLESEX UNIVERSITY HOSPITAL NHS TRUST",
#       "address_line_1": "NORTH MIDDLESEX HOSPITAL",
#       "address_line_2": "STERLING WAY",
#       "town": "LONDON",
#       "postcode": "N18 1QX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Enfield",
#       "gss_code": "E09000010"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTFFS",
#     "name": "NORTH TYNESIDE GENERAL HOSPITAL",
#     "website": "https://www.northumbria.nhs.uk/north-tyneside",
#     "address1": "RAKE LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NORTH SHIELDS",
#     "county": "TYNE AND WEAR",
#     "latitude": 55.02524185,
#     "longitude": -1.467324495,
#     "postcode": "NE29 8NH",
#     "geocode_coordinates": "SRID=27700;POINT (-1.467324495 55.02524185)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ120"
#     },
#     "trust": {
#       "ods_code": "RTF",
#       "name": "NORTHUMBRIA HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "NORTH TYNESIDE GENERAL HOSPITAL",
#       "address_line_2": "RAKE LANE",
#       "town": "NORTH SHIELDS",
#       "postcode": "NE29 8NH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTF86",
#     "name": "NORTHUMBRIA SPECIALIST EMERGENCY CARE HOSPITAL",
#     "website": "https://www.northumbria.nhs.uk/emergency/",
#     "address1": "NORTHUMBRIA WAY",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CRAMLINGTON",
#     "county": "NORTHUMBERLAND",
#     "latitude": 55.07406998,
#     "longitude": -1.569669127,
#     "postcode": "NE23 6NZ",
#     "geocode_coordinates": "SRID=27700;POINT (-1.569669127 55.07406998)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTF",
#       "name": "NORTHUMBRIA HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "NORTH TYNESIDE GENERAL HOSPITAL",
#       "address_line_2": "RAKE LANE",
#       "town": "NORTH SHIELDS",
#       "postcode": "NE29 8NH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1K01",
#     "name": "NORTHWICK PARK HOSPITAL",
#     "website": "http://www.lnwh.nhs.uk/",
#     "address1": "WATFORD ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HARROW",
#     "county": "MIDDLESEX",
#     "latitude": 51.57540894,
#     "longitude": -0.322022736,
#     "postcode": "HA1 3UJ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.322022736 51.57540894)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ089"
#     },
#     "trust": {
#       "ods_code": "R1K",
#       "name": "LONDON NORTH WEST UNIVERSITY HEALTHCARE NHS TRUST",
#       "address_line_1": "NORTHWICK PARK HOSPITAL",
#       "address_line_2": "WATFORD ROAD",
#       "town": "HARROW",
#       "postcode": "HA1 3UJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000027",
#       "name": "NHS North West London Integrated Care Board",
#       "ods_code": "QRV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RY312",
#     "name": "NORWICH COMMUNITY HOSPITAL",
#     "website": "http://www.norfolkcommunityhealthandcare.nhs.uk",
#     "address1": "BOWTHORPE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NORWICH",
#     "county": "NORFOLK",
#     "latitude": 52.63391876,
#     "longitude": 1.262482047,
#     "postcode": "NR2 3TU",
#     "geocode_coordinates": "SRID=27700;POINT (1.262482047 52.63391876)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RY3",
#       "name": "NORFOLK COMMUNITY HEALTH AND CARE NHS TRUST",
#       "address_line_1": "NORWICH COMMUNITY HOSPITAL",
#       "address_line_2": "BOWTHORPE ROAD",
#       "town": "NORWICH",
#       "postcode": "NR2 3TU",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000022",
#       "name": "NHS Norfolk and Waveney Integrated Care Board",
#       "ods_code": "QMM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RX1RA",
#     "name": "NOTTINGHAM UNIVERSITY HOSPITALS NHS TRUST - QUEEN'S MEDICAL CENTRE CAMPUS",
#     "website": null,
#     "address1": "NOTTINGHAM UNIVERSITY HOSPITAL",
#     "address2": null,
#     "address3": null,
#     "telephone": null,
#     "city": "NOTTINGHAM",
#     "county": null,
#     "latitude": 52.943799,
#     "longitude": -1.185957,
#     "postcode": "NG7 2UH",
#     "geocode_coordinates": "SRID=27700;POINT (-1.185957 52.943799)",
#     "active": true,
#     "published_at": "2006-04-01",
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ042"
#     },
#     "trust": {
#       "ods_code": "RX1",
#       "name": "NOTTINGHAM UNIVERSITY HOSPITALS NHS TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "QUEENS MEDICAL CENTRE",
#       "town": "NOTTINGHAM",
#       "postcode": "NG7 2UH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000060",
#       "name": "NHS Nottingham and Nottinghamshire Integrated Care Board",
#       "ods_code": "QT1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJC1V",
#     "name": "NUFFIELD WARWICKSHIRE HOSPITAL",
#     "website": "",
#     "address1": "THE CHASE",
#     "address2": "BLACKDOWN",
#     "address3": "",
#     "telephone": "",
#     "city": "LEAMINGTON SPA",
#     "county": "",
#     "latitude": 52.31102428092342,
#     "longitude": -1.539027380726561,
#     "postcode": "CV32 6RW",
#     "geocode_coordinates": "SRID=27700;POINT (-1.539027380726561 52.31102428092342)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RJC",
#       "name": "SOUTH WARWICKSHIRE UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "WARWICK HOSPITAL",
#       "address_line_2": "LAKIN ROAD",
#       "town": "WARWICK",
#       "postcode": "CV34 5BW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000018",
#       "name": "NHS Coventry and Warwickshire Integrated Care Board",
#       "ods_code": "QWU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVY02",
#     "name": "ORMSKIRK & DISTRICT GENERAL HOSPITAL",
#     "website": "http://www.southportandormskirk.nhs.uk",
#     "address1": "WIGAN ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ORMSKIRK",
#     "county": "LANCASHIRE",
#     "latitude": 53.56462097,
#     "longitude": -2.871237278,
#     "postcode": "L39 2AZ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.871237278 53.56462097)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ110"
#     },
#     "trust": {
#       "ods_code": "RVY",
#       "name": "SOUTHPORT AND ORMSKIRK HOSPITAL NHS TRUST",
#       "address_line_1": "TOWN LANE",
#       "address_line_2": "",
#       "town": "SOUTHPORT",
#       "postcode": "PR8 6PN",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVNE9",
#     "name": "OSPREY COURT",
#     "website": "",
#     "address1": "UNIT 1-2",
#     "address2": "OSPREY COURT",
#     "address3": "HAWKFIELD BUSINESS PARK",
#     "telephone": "",
#     "city": "BRISTOL",
#     "county": "AVON",
#     "latitude": 51.411698943237695,
#     "longitude": -2.5924267932069522,
#     "postcode": "BS14 0BB",
#     "geocode_coordinates": "SRID=27700;POINT (-2.592426793206952 51.4116989432377)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RVN",
#       "name": "AVON AND WILTSHIRE MENTAL HEALTH PARTNERSHIP NHS TRUST",
#       "address_line_1": "BATH NHS HOUSE",
#       "address_line_2": "NEWBRIDGE HILL",
#       "town": "BATH",
#       "postcode": "BA1 3QE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000040",
#       "name": "NHS Bath and North East Somerset, Swindon and Wiltshire Integrated Care Board",
#       "ods_code": "QOX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RKE04",
#     "name": "PAEDIATRICS WHITTINGTON",
#     "website": "",
#     "address1": "MAGDALA AVENUE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.566442088321025,
#     "longitude": -0.1388682606380006,
#     "postcode": "N19 5NF",
#     "geocode_coordinates": "SRID=27700;POINT (-0.1388682606380006 51.56644208832103)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RKE",
#       "name": "WHITTINGTON HEALTH NHS TRUST",
#       "address_line_1": "THE WHITTINGTON HOSPITAL",
#       "address_line_2": "MAGDALA AVENUE",
#       "town": "LONDON",
#       "postcode": "N19 5NF",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Islington",
#       "gss_code": "E09000019"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVJT4",
#     "name": "PATCHWAY LOCALITY HUB",
#     "website": "",
#     "address1": "RODWAY ROAD",
#     "address2": "PATCHWAY",
#     "address3": "",
#     "telephone": "",
#     "city": "BRISTOL",
#     "county": "AVON",
#     "latitude": 51.53153185971164,
#     "longitude": -2.5764474476942887,
#     "postcode": "BS34 5PE",
#     "geocode_coordinates": "SRID=27700;POINT (-2.576447447694289 51.53153185971164)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RVJ",
#       "name": "NORTH BRISTOL NHS TRUST",
#       "address_line_1": "SOUTHMEAD HOSPITAL",
#       "address_line_2": "SOUTHMEAD ROAD",
#       "town": "BRISTOL",
#       "postcode": "BS10 5NB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000039",
#       "name": "NHS Bristol, North Somerset and South Gloucestershire Integrated Care Board",
#       "ods_code": "QUY"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RYGHP",
#     "name": "PAYBODY BUILDING",
#     "website": "",
#     "address1": "COVENTRY HEALTH CENTRE",
#     "address2": "STONEY STANTON ROAD",
#     "address3": "",
#     "telephone": "",
#     "city": "COVENTRY",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.414650840431534,
#     "longitude": -1.5059966663377762,
#     "postcode": "CV1 4FS",
#     "geocode_coordinates": "SRID=27700;POINT (-1.505996666337776 52.41465084043153)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RYG",
#       "name": "COVENTRY AND WARWICKSHIRE PARTNERSHIP NHS TRUST",
#       "address_line_1": "WAYSIDE HOUSE",
#       "address_line_2": "WILSONS LANE",
#       "town": "COVENTRY",
#       "postcode": "CV6 6NY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000018",
#       "name": "NHS Coventry and Warwickshire Integrated Care Board",
#       "ods_code": "QWU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RM330",
#     "name": "PENDLETON GATEWAY",
#     "website": "",
#     "address1": "1 BROADWALK",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SALFORD",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.48857472553247,
#     "longitude": -2.284088128527958,
#     "postcode": "M6 5FX",
#     "geocode_coordinates": "SRID=27700;POINT (-2.284088128527958 53.48857472553247)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RM3",
#       "name": "NORTHERN CARE ALLIANCE NHS FOUNDATION TRUST",
#       "address_line_1": "SALFORD ROYAL",
#       "address_line_2": "STOTT LANE",
#       "town": "SALFORD",
#       "postcode": "M6 8HD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RGN80",
#     "name": "PETERBOROUGH CITY HOSPITAL",
#     "website": "https://www.nwangliaft.nhs.uk/",
#     "address1": "EDITH CAVELL CAMPUS",
#     "address2": "BRETTON GATE",
#     "address3": "BRETTON",
#     "telephone": "",
#     "city": "PETERBOROUGH",
#     "county": "CAMBRIDGESHIRE",
#     "latitude": 52.58392334,
#     "longitude": -0.279370904,
#     "postcode": "PE3 9GZ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.279370904 52.58392334)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ131"
#     },
#     "trust": {
#       "ods_code": "RGN",
#       "name": "NORTH WEST ANGLIA NHS FOUNDATION TRUST",
#       "address_line_1": "PETERBOROUGH CITY HOSPITAL",
#       "address_line_2": "BRETTON GATE",
#       "town": "PETERBOROUGH",
#       "postcode": "PE3 9GZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000056",
#       "name": "NHS Cambridgeshire and Peterborough Integrated Care Board",
#       "ods_code": "QUE"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWDLA",
#     "name": "PILGRIM HOSPITAL AND COMMUNITY PAEDIATRICS",
#     "website": "http://www.ulh.nhs.uk",
#     "address1": "SIBSEY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BOSTON",
#     "county": "LINCOLNSHIRE",
#     "latitude": 52.99112701,
#     "longitude": -0.009952853,
#     "postcode": "PE21 9QS",
#     "geocode_coordinates": "SRID=27700;POINT (-0.009952852999999999 52.99112701)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ128"
#     },
#     "trust": {
#       "ods_code": "RWD",
#       "name": "UNITED LINCOLNSHIRE HOSPITALS NHS TRUST",
#       "address_line_1": "LINCOLN COUNTY HOSPITAL",
#       "address_line_2": "GREETWELL ROAD",
#       "town": "LINCOLN",
#       "postcode": "LN2 5QY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000013",
#       "name": "NHS Lincolnshire Integrated Care Board",
#       "ods_code": "QJM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXF05",
#     "name": "PINDERFIELDS GENERAL HOSPITAL",
#     "website": "http://www.midyorks.nhs.uk",
#     "address1": "ABERFORD ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WAKEFIELD",
#     "county": "WEST YORKSHIRE",
#     "latitude": 53.69242096,
#     "longitude": -1.488540292,
#     "postcode": "WF1 4DG",
#     "geocode_coordinates": "SRID=27700;POINT (-1.488540292 53.69242096)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ003"
#     },
#     "trust": {
#       "ods_code": "RXF",
#       "name": "MID YORKSHIRE HOSPITALS NHS TRUST",
#       "address_line_1": "PINDERFIELDS HOSPITAL",
#       "address_line_2": "ABERFORD ROAD",
#       "town": "WAKEFIELD",
#       "postcode": "WF1 4DG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000054",
#       "name": "NHS West Yorkshire Integrated Care Board",
#       "ods_code": "QWO"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R0D01",
#     "name": "POOLE HOSPITAL",
#     "website": "",
#     "address1": "LONGFLEET ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "POOLE",
#     "county": "",
#     "latitude": 50.72147613368994,
#     "longitude": -1.9730246133611542,
#     "postcode": "BH15 2JB",
#     "geocode_coordinates": "SRID=27700;POINT (-1.973024613361154 50.72147613368994)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ054"
#     },
#     "trust": {
#       "ods_code": "R0D",
#       "name": "UNIVERSITY HOSPITALS DORSET NHS FOUNDATION TRUST",
#       "address_line_1": "MANAGEMENT OFFICES",
#       "address_line_2": "POOLE HOSPITAL",
#       "town": "POOLE",
#       "postcode": "BH15 2JB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000041",
#       "name": "NHS Dorset Integrated Care Board",
#       "ods_code": "QVV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A5B3",
#     "name": "PRINCE CHARLES HOSPITAL SITE",
#     "website": "",
#     "address1": "PRINCE CHARLES HOSPITAL",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "MERTHYR TYDFIL",
#     "county": "MID GLAMORGAN",
#     "latitude": 51.7642467133928,
#     "longitude": -3.3851091212405837,
#     "postcode": "CF47 9DT",
#     "geocode_coordinates": "SRID=27700;POINT (-3.385109121240584 51.7642467133928)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A5",
#       "boundary_identifier": "W11000030",
#       "name": "Cwm Taf Morgannwg University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "7A2AL",
#     "name": "PRINCE PHILIP HOSPITAL",
#     "website": "",
#     "address1": "BRYNGWYN MAWR",
#     "address2": "DAFEN",
#     "address3": "",
#     "telephone": "",
#     "city": "LLANELLI",
#     "county": "DYFED",
#     "latitude": 51.69187728463355,
#     "longitude": -4.136129731794417,
#     "postcode": "SA14 8QF",
#     "geocode_coordinates": "SRID=27700;POINT (-4.136129731794417 51.69187728463355)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A2",
#       "boundary_identifier": "W11000025",
#       "name": "Hywel Dda University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RQWG0",
#     "name": "PRINCESS ALEXANDRA HOSPITAL",
#     "website": "http://www.pah.nhs.uk/",
#     "address1": "HAMSTEL ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HARLOW",
#     "county": "ESSEX",
#     "latitude": 51.77153015,
#     "longitude": 0.085471295,
#     "postcode": "CM20 1QX",
#     "geocode_coordinates": "SRID=27700;POINT (0.085471295 51.77153015)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ200"
#     },
#     "trust": {
#       "ods_code": "RQW",
#       "name": "THE PRINCESS ALEXANDRA HOSPITAL NHS TRUST",
#       "address_line_1": "HAMSTEL ROAD",
#       "address_line_2": "",
#       "town": "HARLOW",
#       "postcode": "CM20 1QX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000025",
#       "name": "NHS Hertfordshire and West Essex Integrated Care Board",
#       "ods_code": "QM7"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RHM12",
#     "name": "PRINCESS ANNE HOSPITAL",
#     "website": "http://www.uhs.nhs.uk",
#     "address1": "COXFORD ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SOUTHAMPTON",
#     "county": "HAMPSHIRE",
#     "latitude": 50.93526077,
#     "longitude": -1.434849381,
#     "postcode": "SO16 5YA",
#     "geocode_coordinates": "SRID=27700;POINT (-1.434849381 50.93526077)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RHM",
#       "name": "UNIVERSITY HOSPITAL SOUTHAMPTON NHS FOUNDATION TRUST",
#       "address_line_1": "SOUTHAMPTON GENERAL HOSPITAL",
#       "address_line_2": "TREMONA ROAD",
#       "town": "SOUTHAMPTON",
#       "postcode": "SO16 6YD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A3B7",
#     "name": "PRINCESS OF WALES HOSPITAL",
#     "website": "",
#     "address1": "COITY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BRIDGEND",
#     "county": "MID GLAMORGAN",
#     "latitude": 51.517616936821376,
#     "longitude": -3.571760230503241,
#     "postcode": "CF31 1RQ",
#     "geocode_coordinates": "SRID=27700;POINT (-3.571760230503241 51.51761693682138)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A3",
#       "boundary_identifier": "W11000031",
#       "name": "Swansea Bay University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RJZ30",
#     "name": "PRINCESS ROYAL UNIVERSITY HOSPITAL",
#     "website": "http://pruh.kch.nhs.uk/",
#     "address1": "FARNBOROUGH COMMON",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ORPINGTON",
#     "county": "KENT",
#     "latitude": 51.36624146,
#     "longitude": 0.059160762,
#     "postcode": "BR6 8ND",
#     "geocode_coordinates": "SRID=27700;POINT (0.059160762 51.36624146)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ085"
#     },
#     "trust": {
#       "ods_code": "RJZ",
#       "name": "KING'S COLLEGE HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "DENMARK HILL",
#       "address_line_2": "",
#       "town": "LONDON",
#       "postcode": "SE5 9RS",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000030",
#       "name": "NHS South East London Integrated Care Board",
#       "ods_code": "QKK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RX1CP",
#     "name": "QMC COMMUNITY PAEDIATRICS",
#     "website": "",
#     "address1": "NOTTINGHAM UNIVERSITY HOSPITAL",
#     "address2": "QUEENS MEDICAL CENTRE",
#     "address3": "DERBY ROAD",
#     "telephone": "",
#     "city": "NOTTINGHAM",
#     "county": "NOTTINGHAMSHIRE",
#     "latitude": 52.94378634553726,
#     "longitude": -1.1841889169193678,
#     "postcode": "NG7 2UH",
#     "geocode_coordinates": "SRID=27700;POINT (-1.184188916919368 52.94378634553726)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RX1",
#       "name": "NOTTINGHAM UNIVERSITY HOSPITALS NHS TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "QUEENS MEDICAL CENTRE",
#       "town": "NOTTINGHAM",
#       "postcode": "NG7 2UH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000060",
#       "name": "NHS Nottingham and Nottinghamshire Integrated Care Board",
#       "ods_code": "QT1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RX1PD",
#     "name": "QMC PAEDIATRICS",
#     "website": "",
#     "address1": "NOTTINGHAM UNIVERSITY HOSPITAL",
#     "address2": "QUEENS MEDICAL CENTRE",
#     "address3": "DERBY ROAD",
#     "telephone": "",
#     "city": "NOTTINGHAM",
#     "county": "NOTTINGHAMSHIRE",
#     "latitude": 52.94378634553726,
#     "longitude": -1.1841889169193678,
#     "postcode": "NG7 2UH",
#     "geocode_coordinates": "SRID=27700;POINT (-1.184188916919368 52.94378634553726)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RX1",
#       "name": "NOTTINGHAM UNIVERSITY HOSPITALS NHS TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "QUEENS MEDICAL CENTRE",
#       "town": "NOTTINGHAM",
#       "postcode": "NG7 2UH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000060",
#       "name": "NHS Nottingham and Nottinghamshire Integrated Care Board",
#       "ods_code": "QT1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RHU03",
#     "name": "QUEEN ALEXANDRA HOSPITAL",
#     "website": "http://www.porthosp.nhs.uk",
#     "address1": "SOUTHWICK HILL ROAD",
#     "address2": "COSHAM",
#     "address3": "",
#     "telephone": "",
#     "city": "PORTSMOUTH",
#     "county": "HAMPSHIRE",
#     "latitude": 50.85029984,
#     "longitude": -1.069917679,
#     "postcode": "PO6 3LY",
#     "geocode_coordinates": "SRID=27700;POINT (-1.069917679 50.85029984)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ238"
#     },
#     "trust": {
#       "ods_code": "RHU",
#       "name": "PORTSMOUTH HOSPITALS UNIVERSITY NATIONAL HEALTH SERVICE TRUST",
#       "address_line_1": "QUEEN ALEXANDRA HOSPITAL",
#       "address_line_2": "SOUTHWICK HILL ROAD",
#       "town": "PORTSMOUTH",
#       "postcode": "PO6 3LY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RYJ04",
#     "name": "QUEEN CHARLOTTE'S HOSPITAL",
#     "website": "https://www.imperial.nhs.uk/our-locations/queen-charlottes-and-chelsea-hospital",
#     "address1": "DU CANE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.51742172,
#     "longitude": -0.234706819,
#     "postcode": "W12 0HS",
#     "geocode_coordinates": "SRID=27700;POINT (-0.234706819 51.51742172)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RYJ",
#       "name": "IMPERIAL COLLEGE HEALTHCARE NHS TRUST",
#       "address_line_1": "THE BAYS",
#       "address_line_2": "ST MARYS HOSPITAL",
#       "town": "LONDON",
#       "postcode": "W2 1BL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000027",
#       "name": "NHS North West London Integrated Care Board",
#       "ods_code": "QRV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Hammersmith and Fulham",
#       "gss_code": "E09000013"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RR7EN",
#     "name": "QUEEN ELIZABETH HOSPITAL",
#     "website": "http://www.qegateshead.nhs.uk",
#     "address1": "SHERIFF HILL",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "GATESHEAD",
#     "county": "TYNE AND WEAR",
#     "latitude": 54.93938446,
#     "longitude": -1.580765486,
#     "postcode": "NE9 6SX",
#     "geocode_coordinates": "SRID=27700;POINT (-1.580765486 54.93938446)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ107"
#     },
#     "trust": {
#       "ods_code": "RR7",
#       "name": "GATESHEAD HEALTH NHS FOUNDATION TRUST",
#       "address_line_1": "QUEEN ELIZABETH HOSPITAL",
#       "address_line_2": "SHERIFF HILL",
#       "town": "GATESHEAD",
#       "postcode": "NE9 6SX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJ231",
#     "name": "QUEEN ELIZABETH HOSPITAL",
#     "website": "http://www.lewishamandgreenwich.nhs.uk/",
#     "address1": "STADIUM ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.47819138,
#     "longitude": 0.050057109,
#     "postcode": "SE18 4QH",
#     "geocode_coordinates": "SRID=27700;POINT (0.050057109 51.47819138)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ151"
#     },
#     "trust": {
#       "ods_code": "RJ2",
#       "name": "LEWISHAM AND GREENWICH NHS TRUST",
#       "address_line_1": "UNIVERSITY HOSPITAL LEWISHAM",
#       "address_line_2": "LEWISHAM HIGH STREET",
#       "town": "LONDON",
#       "postcode": "SE13 6LH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000030",
#       "name": "NHS South East London Integrated Care Board",
#       "ods_code": "QKK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Greenwich",
#       "gss_code": "E09000011"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWH20",
#     "name": "QUEEN ELIZABETH II HOSPITAL AND COMMUNITY PAEDIATRICS",
#     "website": "http://www.newqeii.info/",
#     "address1": "HOWLANDS",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WELWYN GARDEN CITY",
#     "county": "HERTFORDSHIRE",
#     "latitude": 51.78336716,
#     "longitude": -0.188622087,
#     "postcode": "AL7 4HQ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.188622087 51.78336716)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ099"
#     },
#     "trust": {
#       "ods_code": "RWH",
#       "name": "EAST AND NORTH HERTFORDSHIRE NHS TRUST",
#       "address_line_1": "LISTER HOSPITAL",
#       "address_line_2": "COREYS MILL LANE",
#       "town": "STEVENAGE",
#       "postcode": "SG1 4AB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000025",
#       "name": "NHS Hertfordshire and West Essex Integrated Care Board",
#       "ods_code": "QM7"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVV09",
#     "name": "QUEEN ELIZABETH THE QUEEN MOTHER HOSPITAL",
#     "website": "http://www.ekhuft.nhs.uk/qeqm",
#     "address1": "ST PETERS ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "MARGATE",
#     "county": "KENT",
#     "latitude": 51.37805176,
#     "longitude": 1.389398694,
#     "postcode": "CT9 4AN",
#     "geocode_coordinates": "SRID=27700;POINT (1.389398694 51.37805176)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ024"
#     },
#     "trust": {
#       "ods_code": "RVV",
#       "name": "EAST KENT HOSPITALS UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "KENT & CANTERBURY HOSPITAL",
#       "address_line_2": "ETHELBERT ROAD",
#       "town": "CANTERBURY",
#       "postcode": "CT1 3NG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000032",
#       "name": "NHS Kent and Medway Integrated Care Board",
#       "ods_code": "QKS"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVR07",
#     "name": "QUEEN MARY'S HOSPITAL FOR CHILDREN",
#     "website": "http://www.epsom-sthelier.nhs.uk",
#     "address1": "WRYTHE LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CARSHALTON",
#     "county": "SURREY",
#     "latitude": 51.38018799,
#     "longitude": -0.183718503,
#     "postcode": "SM5 1AA",
#     "geocode_coordinates": "SRID=27700;POINT (-0.183718503 51.38018799)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ050"
#     },
#     "trust": {
#       "ods_code": "RVR",
#       "name": "EPSOM AND ST HELIER UNIVERSITY HOSPITALS NHS TRUST",
#       "address_line_1": "ST HELIER HOSPITAL",
#       "address_line_2": "WRYTHE LANE",
#       "town": "CARSHALTON",
#       "postcode": "SM5 1AA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000063",
#       "name": "NHS Surrey Heartlands Integrated Care Board",
#       "ods_code": "QXU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RN7QM",
#     "name": "QUEEN MARY'S HOSPITAL SIDCUP",
#     "website": "",
#     "address1": "FROGNAL AVENUE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SIDCUP",
#     "county": "KENT",
#     "latitude": 51.41924154086068,
#     "longitude": 0.1034220330275305,
#     "postcode": "DA14 6LT",
#     "geocode_coordinates": "SRID=27700;POINT (0.1034220330275305 51.41924154086068)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RN7",
#       "name": "DARTFORD AND GRAVESHAM NHS TRUST",
#       "address_line_1": "DARENT VALLEY HOSPITAL",
#       "address_line_2": "DARENTH WOOD ROAD",
#       "town": "DARTFORD",
#       "postcode": "DA2 8DA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000032",
#       "name": "NHS Kent and Medway Integrated Care Board",
#       "ods_code": "QKS"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RF4QH",
#     "name": "QUEEN'S HOSPITAL",
#     "website": "http://www.bhrhospitals.nhs.uk",
#     "address1": "ROM VALLEY WAY",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ROMFORD",
#     "county": "ESSEX",
#     "latitude": 51.56942749,
#     "longitude": 0.180405304,
#     "postcode": "RM7 0AG",
#     "geocode_coordinates": "SRID=27700;POINT (0.180405304 51.56942749)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ232"
#     },
#     "trust": {
#       "ods_code": "RF4",
#       "name": "BARKING, HAVERING AND REDBRIDGE UNIVERSITY HOSPITALS NHS TRUST",
#       "address_line_1": "QUEENS HOSPITAL",
#       "address_line_2": "ROM VALLEY WAY",
#       "town": "ROMFORD",
#       "postcode": "RM7 0AG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000029",
#       "name": "NHS North East London Integrated Care Board",
#       "ods_code": "QMF"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWF11",
#     "name": "QUEEN VICTORIA HOSPITAL",
#     "website": "",
#     "address1": "HOLTYE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "EAST GRINSTEAD",
#     "county": "WEST SUSSEX",
#     "latitude": 51.135209751134006,
#     "longitude": -0.0011303249790203587,
#     "postcode": "RH19 3DZ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.001130324979020359 51.13520975113401)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RWF",
#       "name": "MAIDSTONE AND TUNBRIDGE WELLS NHS TRUST",
#       "address_line_1": "THE MAIDSTONE HOSPITAL",
#       "address_line_2": "HERMITAGE LANE",
#       "town": "MAIDSTONE",
#       "postcode": "ME16 9QQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000032",
#       "name": "NHS Kent and Medway Integrated Care Board",
#       "ods_code": "QKS"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTG14",
#     "name": "RIPLEY HOSPITAL",
#     "website": "",
#     "address1": "SANDHAM LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "RIPLEY",
#     "county": "DERBYSHIRE",
#     "latitude": 53.048059214497236,
#     "longitude": -1.409870024857542,
#     "postcode": "DE5 3HE",
#     "geocode_coordinates": "SRID=27700;POINT (-1.409870024857542 53.04805921449724)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTG",
#       "name": "UNIVERSITY HOSPITALS OF DERBY AND BURTON NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL DERBY HOSPITAL",
#       "address_line_2": "UTTOXETER ROAD",
#       "town": "DERBY",
#       "postcode": "DE22 3NE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000058",
#       "name": "NHS Derby and Derbyshire Integrated Care Board",
#       "ods_code": "QJ2"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJC49",
#     "name": "RIVERSLEY PARK CENTRE",
#     "website": "",
#     "address1": "COTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NUNEATON",
#     "county": "WARWICKSHIRE",
#     "latitude": 52.518697799442705,
#     "longitude": -1.466747350783283,
#     "postcode": "CV11 5TY",
#     "geocode_coordinates": "SRID=27700;POINT (-1.466747350783283 52.51869779944271)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RJC",
#       "name": "SOUTH WARWICKSHIRE UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "WARWICK HOSPITAL",
#       "address_line_2": "LAKIN ROAD",
#       "town": "WARWICK",
#       "postcode": "CV34 5BW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000018",
#       "name": "NHS Coventry and Warwickshire Integrated Care Board",
#       "ods_code": "QWU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RLQ22",
#     "name": "ROSS ROAD HEALTH CLINIC & CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "ROSS ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HEREFORD",
#     "county": "HEREFORDSHIRE",
#     "latitude": 52.04679652818128,
#     "longitude": -2.720555916976644,
#     "postcode": "HR2 7RL",
#     "geocode_coordinates": "SRID=27700;POINT (-2.720555916976644 52.04679652818128)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RLQ",
#       "name": "WYE VALLEY NHS TRUST",
#       "address_line_1": "COUNTY HOSPITAL",
#       "address_line_2": "27 UNION WALK",
#       "town": "HEREFORD",
#       "postcode": "HR1 2ER",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000019",
#       "name": "NHS Herefordshire and Worcestershire Integrated Care Board",
#       "ods_code": "QGH"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RFRPA",
#     "name": "ROTHERHAM DISTRICT GENERAL HOSPITAL",
#     "website": "http://www.therotherhamft.nhs.uk",
#     "address1": "MOORGATE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ROTHERHAM",
#     "county": "SOUTH YORKSHIRE",
#     "latitude": 53.41397476,
#     "longitude": -1.342865467,
#     "postcode": "S60 2UD",
#     "geocode_coordinates": "SRID=27700;POINT (-1.342865467 53.41397476)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ164"
#     },
#     "trust": {
#       "ods_code": "RFR",
#       "name": "THE ROTHERHAM NHS FOUNDATION TRUST",
#       "address_line_1": "MOORGATE ROAD",
#       "address_line_2": "",
#       "town": "ROTHERHAM",
#       "postcode": "S60 2UD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000061",
#       "name": "NHS South Yorkshire Integrated Care Board",
#       "ods_code": "QF7"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Trent Epilepsy Network",
#       "boundary_identifier": "TEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RRF02",
#     "name": "ROYAL ALBERT EDWARD INFIRMARY",
#     "website": "http://www.wwl.nhs.uk/hospitals/raei.aspx",
#     "address1": "WIGAN LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WIGAN",
#     "county": "LANCASHIRE",
#     "latitude": 53.55774307,
#     "longitude": -2.629076481,
#     "postcode": "WN1 2NN",
#     "geocode_coordinates": "SRID=27700;POINT (-2.629076481 53.55774307)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ104"
#     },
#     "trust": {
#       "ods_code": "RRF",
#       "name": "WRIGHTINGTON, WIGAN AND LEIGH NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL ALBERT EDWARD INFIRMARY",
#       "address_line_2": "WIGAN LANE",
#       "town": "WIGAN",
#       "postcode": "WN1 2NN",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "G0W1C",
#     "name": "ROYAL ALEXANDRA CHILDREN’S HOSPITAL",
#     "website": "",
#     "address1": "EASTERN ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BRIGHTON",
#     "county": "EAST SUSSEX",
#     "latitude": 50.81947,
#     "longitude": -0.11818,
#     "postcode": "BN2 5BE",
#     "geocode_coordinates": "SRID=27700;POINT (-0.11818 50.81947)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ135"
#     },
#     "trust": {
#       "ods_code": "RYR",
#       "name": "UNIVERSITY HOSPITALS SUSSEX NHS FOUNDATION TRUST",
#       "address_line_1": "WORTHING HOSPITAL",
#       "address_line_2": "LYNDHURST ROAD",
#       "town": "WORTHING",
#       "postcode": "BN11 2DH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000064",
#       "name": "NHS Sussex Integrated Care Board",
#       "ods_code": "QNX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RHW01",
#     "name": "ROYAL BERKSHIRE HOSPITAL",
#     "website": "http://www.royalberkshire.nhs.uk",
#     "address1": "LONDON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "READING",
#     "county": "BERKSHIRE",
#     "latitude": 51.4510231,
#     "longitude": -0.959315777,
#     "postcode": "RG1 5AN",
#     "geocode_coordinates": "SRID=27700;POINT (-0.959315777 51.4510231)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ035"
#     },
#     "trust": {
#       "ods_code": "RHW",
#       "name": "ROYAL BERKSHIRE NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL BERKSHIRE HOSPITAL",
#       "address_line_2": "LONDON ROAD",
#       "town": "READING",
#       "postcode": "RG1 5AN",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000044",
#       "name": "NHS Buckinghamshire, Oxfordshire and Berkshire West Integrated Care Board",
#       "ods_code": "QU9"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXR20",
#     "name": "ROYAL BLACKBURN HOSPITAL",
#     "website": "http://www.elht.nhs.uk",
#     "address1": "HASLINGDEN ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BLACKBURN",
#     "county": "LANCASHIRE",
#     "latitude": 53.73556519,
#     "longitude": -2.462701321,
#     "postcode": "BB2 3HH",
#     "geocode_coordinates": "SRID=27700;POINT (-2.462701321 53.73556519)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ091"
#     },
#     "trust": {
#       "ods_code": "RXR",
#       "name": "EAST LANCASHIRE HOSPITALS NHS TRUST",
#       "address_line_1": "ROYAL BLACKBURN HOSPITAL",
#       "address_line_2": "HASLINGDEN ROAD",
#       "town": "BLACKBURN",
#       "postcode": "BB2 3HH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000048",
#       "name": "NHS Lancashire and South Cumbria Integrated Care Board",
#       "ods_code": "QE1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RMC01",
#     "name": "ROYAL BOLTON HOSPITAL",
#     "website": "http://www.boltonft.nhs.uk",
#     "address1": "MINERVA ROAD",
#     "address2": "FARNWORTH",
#     "address3": "",
#     "telephone": "",
#     "city": "BOLTON",
#     "county": "LANCASHIRE",
#     "latitude": 53.55396271,
#     "longitude": -2.429878712,
#     "postcode": "BL4 0JR",
#     "geocode_coordinates": "SRID=27700;POINT (-2.429878712 53.55396271)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ177"
#     },
#     "trust": {
#       "ods_code": "RMC",
#       "name": "BOLTON NHS FOUNDATION TRUST",
#       "address_line_1": "THE ROYAL BOLTON HOSPITAL",
#       "address_line_2": "MINERVA ROAD",
#       "town": "BOLTON",
#       "postcode": "BL4 0JR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R0D02",
#     "name": "ROYAL BOURNEMOUTH HOSPITAL",
#     "website": "",
#     "address1": "CASTLE LANE EAST",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BOURNEMOUTH",
#     "county": "",
#     "latitude": 50.74748611,
#     "longitude": -1.820505619,
#     "postcode": "BH7 7DW",
#     "geocode_coordinates": "SRID=27700;POINT (-1.820505619 50.74748611)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "R0D",
#       "name": "UNIVERSITY HOSPITALS DORSET NHS FOUNDATION TRUST",
#       "address_line_1": "MANAGEMENT OFFICES",
#       "address_line_2": "POOLE HOSPITAL",
#       "town": "POOLE",
#       "postcode": "BH15 2JB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000041",
#       "name": "NHS Dorset Integrated Care Board",
#       "ods_code": "QVV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "REF12",
#     "name": "ROYAL CORNWALL HOSPITAL (TRELISKE)",
#     "website": "http://www.royalcornwall.nhs.uk",
#     "address1": "TRELISKE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "TRURO",
#     "county": "CORNWALL",
#     "latitude": 50.26656723,
#     "longitude": -5.094250202,
#     "postcode": "TR1 3LJ",
#     "geocode_coordinates": "SRID=27700;POINT (-5.094250202 50.26656723)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ067"
#     },
#     "trust": {
#       "ods_code": "REF",
#       "name": "ROYAL CORNWALL HOSPITALS NHS TRUST",
#       "address_line_1": "ROYAL CORNWALL HOSPITAL",
#       "address_line_2": "TRELISKE",
#       "town": "TRURO",
#       "postcode": "TR1 3LJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000036",
#       "name": "NHS Cornwall and the Isles of Scilly Integrated Care Board",
#       "ods_code": "QT6"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTGFG",
#     "name": "ROYAL DERBY HOSPITAL",
#     "website": "https://www.uhdb.nhs.uk/",
#     "address1": "UTTOXETER ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "DERBY",
#     "county": "DERBYSHIRE",
#     "latitude": 52.91155624,
#     "longitude": -1.514264703,
#     "postcode": "DE22 3NE",
#     "geocode_coordinates": "SRID=27700;POINT (-1.514264703 52.91155624)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ005"
#     },
#     "trust": {
#       "ods_code": "RTG",
#       "name": "UNIVERSITY HOSPITALS OF DERBY AND BURTON NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL DERBY HOSPITAL",
#       "address_line_2": "UTTOXETER ROAD",
#       "town": "DERBY",
#       "postcode": "DE22 3NE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000058",
#       "name": "NHS Derby and Derbyshire Integrated Care Board",
#       "ods_code": "QJ2"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RK963",
#     "name": "ROYAL DEVON & EXETER FOUNDATION HOSPITAL",
#     "website": "",
#     "address1": "BARRACK ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "EXETER",
#     "county": "DEVON",
#     "latitude": 50.71705628305987,
#     "longitude": -3.5057143220612685,
#     "postcode": "EX2 5DW",
#     "geocode_coordinates": "SRID=27700;POINT (-3.505714322061269 50.71705628305987)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RK9",
#       "name": "UNIVERSITY HOSPITALS PLYMOUTH NHS TRUST",
#       "address_line_1": "DERRIFORD HOSPITAL",
#       "address_line_2": "DERRIFORD ROAD",
#       "town": "PLYMOUTH",
#       "postcode": "PL6 8DH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000037",
#       "name": "NHS Devon Integrated Care Board",
#       "ods_code": "QJK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RH801",
#     "name": "ROYAL DEVON & EXETER HOSPITAL (WONFORD)",
#     "website": "http://www.rdehospital.nhs.uk/",
#     "address1": "BARRACK ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "EXETER",
#     "county": "DEVON",
#     "latitude": 50.71670914,
#     "longitude": -3.506666422,
#     "postcode": "EX2 5DW",
#     "geocode_coordinates": "SRID=27700;POINT (-3.506666422 50.71670914)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ060"
#     },
#     "trust": {
#       "ods_code": "RH8",
#       "name": "ROYAL DEVON UNIVERSITY HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL DEVON UNIVERSITY NHS FT",
#       "address_line_2": "BARRACK ROAD",
#       "town": "EXETER",
#       "postcode": "EX2 5DW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000037",
#       "name": "NHS Devon Integrated Care Board",
#       "ods_code": "QJK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RAL01",
#     "name": "ROYAL FREE HOSPITAL",
#     "website": "http://www.royalfree.nhs.uk/",
#     "address1": "POND STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.55322266,
#     "longitude": -0.165309235,
#     "postcode": "NW3 2QG",
#     "geocode_coordinates": "SRID=27700;POINT (-0.165309235 51.55322266)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ157"
#     },
#     "trust": {
#       "ods_code": "RAL",
#       "name": "ROYAL FREE LONDON NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL FREE HOSPITAL",
#       "address_line_2": "POND STREET",
#       "town": "LONDON",
#       "postcode": "NW3 2QG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Camden",
#       "gss_code": "E09000007"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A6AR",
#     "name": "ROYAL GWENT HOSPITAL",
#     "website": "",
#     "address1": "CARDIFF ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NEWPORT",
#     "county": "GWENT",
#     "latitude": 51.58019390984616,
#     "longitude": -2.9959470071754546,
#     "postcode": "NP20 2UB",
#     "geocode_coordinates": "SRID=27700;POINT (-2.995947007175455 51.58019390984616)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A6",
#       "boundary_identifier": "W11000028",
#       "name": "Aneurin Bevan University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RN541",
#     "name": "ROYAL HAMPSHIRE COUNTY HOSPITAL",
#     "website": "http://www.hampshirehospitals.nhs.uk",
#     "address1": "ROMSEY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WINCHESTER",
#     "county": "HAMPSHIRE",
#     "latitude": 51.06171036,
#     "longitude": -1.329156041,
#     "postcode": "SO22 5DG",
#     "geocode_coordinates": "SRID=27700;POINT (-1.329156041 51.06171036)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ034"
#     },
#     "trust": {
#       "ods_code": "RN5",
#       "name": "HAMPSHIRE HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "BASINGSTOKE AND NORTH HAMPSHIRE HOS",
#       "address_line_2": "ALDERMASTON ROAD",
#       "town": "BASINGSTOKE",
#       "postcode": "RG24 9NA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R0A03",
#     "name": "ROYAL MANCHESTER CHILDREN'S HOSPITAL",
#     "website": "https://mft.nhs.uk/rmch/",
#     "address1": "OXFORD ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.46046829,
#     "longitude": -2.224475861,
#     "postcode": "M13 9WL",
#     "geocode_coordinates": "SRID=27700;POINT (-2.224475861 53.46046829)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ136"
#     },
#     "trust": {
#       "ods_code": "R0A",
#       "name": "MANCHESTER UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "COBBETT HOUSE",
#       "address_line_2": "OXFORD ROAD",
#       "town": "MANCHESTER",
#       "postcode": "M13 9WL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RM317",
#     "name": "ROYAL OLDHAM HOSPITAL",
#     "website": "",
#     "address1": "ROCHDALE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "OLDHAM",
#     "county": "LANCASHIRE",
#     "latitude": 53.55276952726198,
#     "longitude": -2.12276427085255,
#     "postcode": "OL1 2JH",
#     "geocode_coordinates": "SRID=27700;POINT (-2.12276427085255 53.55276952726198)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RM3",
#       "name": "NORTHERN CARE ALLIANCE NHS FOUNDATION TRUST",
#       "address_line_1": "SALFORD ROYAL",
#       "address_line_2": "STOTT LANE",
#       "town": "SALFORD",
#       "postcode": "M6 8HD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXN02",
#     "name": "ROYAL PRESTON HOSPITAL",
#     "website": "http://www.lancsteachinghospitals.nhs.uk",
#     "address1": "SHAROE GREEN LANE NORTH",
#     "address2": "FULWOOD",
#     "address3": "",
#     "telephone": "",
#     "city": "PRESTON",
#     "county": "LANCASHIRE",
#     "latitude": 53.79151154,
#     "longitude": -2.706829548,
#     "postcode": "PR2 9HT",
#     "geocode_coordinates": "SRID=27700;POINT (-2.706829548 53.79151154)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ183"
#     },
#     "trust": {
#       "ods_code": "RXN",
#       "name": "LANCASHIRE TEACHING HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL PRESTON HOSPITAL",
#       "address_line_2": "SHAROE GREEN LANE",
#       "town": "PRESTON",
#       "postcode": "PR2 9HT",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000048",
#       "name": "NHS Lancashire and South Cumbria Integrated Care Board",
#       "ods_code": "QE1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXWAS",
#     "name": "ROYAL SHREWSBURY HOSPITAL",
#     "website": "http://www.sath.nhs.uk/",
#     "address1": "MYTTON OAK ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SHREWSBURY",
#     "county": "SHROPSHIRE",
#     "latitude": 52.70926285,
#     "longitude": -2.793676376,
#     "postcode": "SY3 8XQ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.793676376 52.70926285)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RXW",
#       "name": "THE SHREWSBURY AND TELFORD HOSPITAL NHS TRUST",
#       "address_line_1": "MYTTON OAK ROAD",
#       "address_line_2": "",
#       "town": "SHREWSBURY",
#       "postcode": "SY3 8XQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000011",
#       "name": "NHS Shropshire, Telford and Wrekin Integrated Care Board",
#       "ods_code": "QOC"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RHM02",
#     "name": "ROYAL SOUTH HANTS HOSPITAL",
#     "website": "",
#     "address1": "GRAHAM ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SOUTHAMPTON",
#     "county": "HAMPSHIRE",
#     "latitude": 50.91243896406982,
#     "longitude": -1.395580557527431,
#     "postcode": "SO14 0YG",
#     "geocode_coordinates": "SRID=27700;POINT (-1.395580557527431 50.91243896406982)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RHM",
#       "name": "UNIVERSITY HOSPITAL SOUTHAMPTON NHS FOUNDATION TRUST",
#       "address_line_1": "SOUTHAMPTON GENERAL HOSPITAL",
#       "address_line_2": "TREMONA ROAD",
#       "town": "SOUTHAMPTON",
#       "postcode": "SO16 6YD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJE01",
#     "name": "ROYAL STOKE UNIVERSITY HOSPITAL",
#     "website": "https://www.uhnm.nhs.uk",
#     "address1": "NEWCASTLE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "STOKE-ON-TRENT",
#     "county": "STAFFORDSHIRE",
#     "latitude": 53.00324631,
#     "longitude": -2.211784124,
#     "postcode": "ST4 6QG",
#     "geocode_coordinates": "SRID=27700;POINT (-2.211784124 53.00324631)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ078"
#     },
#     "trust": {
#       "ods_code": "RJE",
#       "name": "UNIVERSITY HOSPITALS OF NORTH MIDLANDS NHS TRUST",
#       "address_line_1": "NEWCASTLE ROAD",
#       "address_line_2": "",
#       "town": "STOKE-ON-TRENT",
#       "postcode": "ST4 6QG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000010",
#       "name": "NHS Staffordshire and Stoke-on-Trent Integrated Care Board",
#       "ods_code": "QNC"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RA201",
#     "name": "ROYAL SURREY COUNTY HOSPITAL",
#     "website": "http://www.royalsurrey.nhs.uk",
#     "address1": "EGERTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "GUILDFORD",
#     "county": "SURREY",
#     "latitude": 51.24101639,
#     "longitude": -0.60744828,
#     "postcode": "GU2 7XX",
#     "geocode_coordinates": "SRID=27700;POINT (-0.60744828 51.24101639)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ088"
#     },
#     "trust": {
#       "ods_code": "RA2",
#       "name": "ROYAL SURREY COUNTY HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "EGERTON ROAD",
#       "address_line_2": "",
#       "town": "GUILDFORD",
#       "postcode": "GU2 7XX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000063",
#       "name": "NHS Surrey Heartlands Integrated Care Board",
#       "ods_code": "QXU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RD130",
#     "name": "ROYAL UNITED HOSPITAL",
#     "website": "",
#     "address1": "COMBE PARK",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BATH",
#     "county": "AVON",
#     "latitude": 51.39191421412843,
#     "longitude": -2.3901410048590637,
#     "postcode": "BA1 3NG",
#     "geocode_coordinates": "SRID=27700;POINT (-2.390141004859064 51.39191421412843)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ068"
#     },
#     "trust": {
#       "ods_code": "RD1",
#       "name": "ROYAL UNITED HOSPITALS BATH NHS FOUNDATION TRUST",
#       "address_line_1": "COMBE PARK",
#       "address_line_2": "",
#       "town": "BATH",
#       "postcode": "BA1 3NG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000040",
#       "name": "NHS Bath and North East Somerset, Swindon and Wiltshire Integrated Care Board",
#       "ods_code": "QOX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVV03",
#     "name": "ROYAL VICTORIA HOSPITAL (FOLKESTONE)",
#     "website": "",
#     "address1": "RADNOR PARK AVENUE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "FOLKESTONE",
#     "county": "KENT",
#     "latitude": 51.08610340124624,
#     "longitude": 1.1728709210454833,
#     "postcode": "CT19 5BN",
#     "geocode_coordinates": "SRID=27700;POINT (1.172870921045483 51.08610340124624)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ024"
#     },
#     "trust": {
#       "ods_code": "RVV",
#       "name": "EAST KENT HOSPITALS UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "KENT & CANTERBURY HOSPITAL",
#       "address_line_2": "ETHELBERT ROAD",
#       "town": "CANTERBURY",
#       "postcode": "CT1 3NG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000032",
#       "name": "NHS Kent and Medway Integrated Care Board",
#       "ods_code": "QKS"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBK10",
#     "name": "RUSHALL MEDICAL CENTRE",
#     "website": "",
#     "address1": "107 LICHFIELD ROAD",
#     "address2": "RUSHALL",
#     "address3": "",
#     "telephone": "",
#     "city": "WALSALL",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.608415215290684,
#     "longitude": -1.9586749294735848,
#     "postcode": "WS4 1HB",
#     "geocode_coordinates": "SRID=27700;POINT (-1.958674929473585 52.60841521529068)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RBK",
#       "name": "WALSALL HEALTHCARE NHS TRUST",
#       "address_line_1": "MANOR HOSPITAL",
#       "address_line_2": "MOAT ROAD",
#       "town": "WALSALL",
#       "postcode": "WS2 9PS",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000062",
#       "name": "NHS Black Country Integrated Care Board",
#       "ods_code": "QUA"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RNA01",
#     "name": "RUSSELLS HALL HOSPITAL",
#     "website": "https://www.dgft.nhs.uk/",
#     "address1": "PENSNETT ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "DUDLEY",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.50294876,
#     "longitude": -2.118503094,
#     "postcode": "DY1 2HQ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.118503094 52.50294876)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ240"
#     },
#     "trust": {
#       "ods_code": "RNA",
#       "name": "THE DUDLEY GROUP NHS FOUNDATION TRUST",
#       "address_line_1": "RUSSELLS HALL HOSPITAL",
#       "address_line_2": "PENSNETT ROAD",
#       "town": "DUDLEY",
#       "postcode": "DY1 2HQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000062",
#       "name": "NHS Black Country Integrated Care Board",
#       "ods_code": "QUA"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RCU02",
#     "name": "RYEGATE CHILDREN'S CENTRE",
#     "website": "",
#     "address1": "TAPTON CRESCENT ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SHEFFIELD",
#     "county": "SOUTH YORKSHIRE",
#     "latitude": 53.37768457660176,
#     "longitude": -1.5127835592201522,
#     "postcode": "S10 5DD",
#     "geocode_coordinates": "SRID=27700;POINT (-1.512783559220152 53.37768457660176)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RCU",
#       "name": "SHEFFIELD CHILDREN'S NHS FOUNDATION TRUST",
#       "address_line_1": "WESTERN BANK",
#       "address_line_2": "",
#       "town": "SHEFFIELD",
#       "postcode": "S10 2TH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000061",
#       "name": "NHS South Yorkshire Integrated Care Board",
#       "ods_code": "QF7"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Trent Epilepsy Network",
#       "boundary_identifier": "TEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RM301",
#     "name": "SALFORD ROYAL",
#     "website": "https://www.northerncarealliance.nhs.uk/",
#     "address1": "STOTT LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SALFORD",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.48754883,
#     "longitude": -2.323409557,
#     "postcode": "M6 8HD",
#     "geocode_coordinates": "SRID=27700;POINT (-2.323409557 53.48754883)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ231"
#     },
#     "trust": {
#       "ods_code": "RM3",
#       "name": "NORTHERN CARE ALLIANCE NHS FOUNDATION TRUST",
#       "address_line_1": "SALFORD ROYAL",
#       "address_line_2": "STOTT LANE",
#       "town": "SALFORD",
#       "postcode": "M6 8HD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RNZ02",
#     "name": "SALISBURY DISTRICT HOSPITAL",
#     "website": "http://www.salisbury.nhs.uk",
#     "address1": "ODSTOCK ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SALISBURY",
#     "county": "WILTSHIRE",
#     "latitude": 51.04394913,
#     "longitude": -1.789808512,
#     "postcode": "SP2 8BJ",
#     "geocode_coordinates": "SRID=27700;POINT (-1.789808512 51.04394913)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ169"
#     },
#     "trust": {
#       "ods_code": "RNZ",
#       "name": "SALISBURY NHS FOUNDATION TRUST",
#       "address_line_1": "SALISBURY DISTRICT HOSPITAL",
#       "address_line_2": "ODSTOCK ROAD",
#       "town": "SALISBURY",
#       "postcode": "SP2 8BJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000040",
#       "name": "NHS Bath and North East Somerset, Swindon and Wiltshire Integrated Care Board",
#       "ods_code": "QOX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTG54",
#     "name": "SAMUEL JOHNSON COMMUNITY HOSPITAL",
#     "website": "https://www.uhdb.nhs.uk",
#     "address1": "TRENT VALLEY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LICHFIELD",
#     "county": "STAFFORDSHIRE",
#     "latitude": 52.68593979,
#     "longitude": -1.815455794,
#     "postcode": "WS13 6EF",
#     "geocode_coordinates": "SRID=27700;POINT (-1.815455794 52.68593979)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTG",
#       "name": "UNIVERSITY HOSPITALS OF DERBY AND BURTON NHS FOUNDATION TRUST",
#       "address_line_1": "ROYAL DERBY HOSPITAL",
#       "address_line_2": "UTTOXETER ROAD",
#       "town": "DERBY",
#       "postcode": "DE22 3NE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000058",
#       "name": "NHS Derby and Derbyshire Integrated Care Board",
#       "ods_code": "QJ2"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RM366",
#     "name": "SANDRINGHAM HOUSE",
#     "website": "",
#     "address1": "WINDSOR STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SALFORD",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.47949508450214,
#     "longitude": -2.2794789420216426,
#     "postcode": "M5 4DG",
#     "geocode_coordinates": "SRID=27700;POINT (-2.279478942021643 53.47949508450214)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RM3",
#       "name": "NORTHERN CARE ALLIANCE NHS FOUNDATION TRUST",
#       "address_line_1": "SALFORD ROYAL",
#       "address_line_2": "STOTT LANE",
#       "town": "SALFORD",
#       "postcode": "M6 8HD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXK01",
#     "name": "SANDWELL GENERAL HOSPITAL",
#     "website": "http://www.swbh.nhs.uk",
#     "address1": "LYNDON",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WEST BROMWICH",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.52807999,
#     "longitude": -1.988857388,
#     "postcode": "B71 4HJ",
#     "geocode_coordinates": "SRID=27700;POINT (-1.988857388 52.52807999)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ223"
#     },
#     "trust": {
#       "ods_code": "RXK",
#       "name": "SANDWELL AND WEST BIRMINGHAM HOSPITALS NHS TRUST",
#       "address_line_1": "CITY HOSPITAL",
#       "address_line_2": "DUDLEY ROAD",
#       "town": "BIRMINGHAM",
#       "postcode": "B18 7QH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000055",
#       "name": "NHS Birmingham and Solihull Integrated Care Board",
#       "ods_code": "QHL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RCBCA",
#     "name": "SCARBOROUGH GENERAL HOSPITAL",
#     "website": "http://www.york.nhs.uk",
#     "address1": "WOODLANDS DRIVE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SCARBOROUGH",
#     "county": "NORTH YORKSHIRE",
#     "latitude": 54.28170776,
#     "longitude": -0.43473798,
#     "postcode": "YO12 6QL",
#     "geocode_coordinates": "SRID=27700;POINT (-0.43473798 54.28170776)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ112"
#     },
#     "trust": {
#       "ods_code": "RCB",
#       "name": "YORK AND SCARBOROUGH TEACHING HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "YORK HOSPITAL",
#       "address_line_2": "WIGGINTON ROAD",
#       "town": "YORK",
#       "postcode": "YO31 8HE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000051",
#       "name": "NHS Humber and North Yorkshire Integrated Care Board",
#       "ods_code": "QOQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJL32",
#     "name": "SCUNTHORPE GENERAL HOSPITAL",
#     "website": "http://www.nlg.nhs.uk/hospitals/scunthorpe",
#     "address1": "CLIFF GARDENS",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SCUNTHORPE",
#     "county": "SOUTH HUMBERSIDE",
#     "latitude": 53.58758545,
#     "longitude": -0.667584062,
#     "postcode": "DN15 7BH",
#     "geocode_coordinates": "SRID=27700;POINT (-0.667584062 53.58758545)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ053"
#     },
#     "trust": {
#       "ods_code": "RJL",
#       "name": "NORTHERN LINCOLNSHIRE AND GOOLE NHS FOUNDATION TRUST",
#       "address_line_1": "DIANA PRINCESS OF WALES HOSPITAL",
#       "address_line_2": "SCARTHO ROAD",
#       "town": "GRIMSBY",
#       "postcode": "DN33 2BA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000051",
#       "name": "NHS Humber and North Yorkshire Integrated Care Board",
#       "ods_code": "QOQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Trent Epilepsy Network",
#       "boundary_identifier": "TEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RDRMK",
#     "name": "SEASIDE VIEW CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "BRIGHTON GENERAL HOSPITAL",
#     "address2": "ELM GROVE",
#     "address3": "",
#     "telephone": "",
#     "city": "BRIGHTON",
#     "county": "EAST SUSSEX",
#     "latitude": 50.83118,
#     "longitude": -0.1145,
#     "postcode": "BN2 3EW",
#     "geocode_coordinates": "SRID=27700;POINT (-0.1145 50.83118)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RDR",
#       "name": "SUSSEX COMMUNITY NHS FOUNDATION TRUST",
#       "address_line_1": "BRIGHTON GENERAL HOSPITAL",
#       "address_line_2": "ELM GROVE",
#       "town": "BRIGHTON",
#       "postcode": "BN2 3EW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000064",
#       "name": "NHS Sussex Integrated Care Board",
#       "ods_code": "QNX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RCUEF",
#     "name": "SHEFFIELD CHILDREN'S HOSPITAL",
#     "website": "http://www.sheffieldchildrens.nhs.uk/",
#     "address1": "WESTERN BANK",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SHEFFIELD",
#     "county": "SOUTH YORKSHIRE",
#     "latitude": 53.38060379,
#     "longitude": -1.490613818,
#     "postcode": "S10 2TH",
#     "geocode_coordinates": "SRID=27700;POINT (-1.490613818 53.38060379)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ219"
#     },
#     "trust": {
#       "ods_code": "RCU",
#       "name": "SHEFFIELD CHILDREN'S NHS FOUNDATION TRUST",
#       "address_line_1": "WESTERN BANK",
#       "address_line_2": "",
#       "town": "SHEFFIELD",
#       "postcode": "S10 2TH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000061",
#       "name": "NHS South Yorkshire Integrated Care Board",
#       "ods_code": "QF7"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Trent Epilepsy Network",
#       "boundary_identifier": "TEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RKE54",
#     "name": "SIMMONS HOUSE",
#     "website": "",
#     "address1": "WHITTINGTON HEALTH",
#     "address2": "ST. LUKES WOODSIDE HOSPITAL",
#     "address3": "WOODSIDE AVENUE",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.5871549291953,
#     "longitude": -0.1487583672793104,
#     "postcode": "N10 3HU",
#     "geocode_coordinates": "SRID=27700;POINT (-0.1487583672793104 51.5871549291953)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RKE",
#       "name": "WHITTINGTON HEALTH NHS TRUST",
#       "address_line_1": "THE WHITTINGTON HOSPITAL",
#       "address_line_2": "MAGDALA AVENUE",
#       "town": "LONDON",
#       "postcode": "N19 5NF",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Haringey",
#       "gss_code": "E09000014"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A3C4",
#     "name": "SINGLETON HOSPITAL",
#     "website": "",
#     "address1": "SKETTY LANE",
#     "address2": "SKETTY",
#     "address3": "",
#     "telephone": "",
#     "city": "SWANSEA",
#     "county": "WEST GLAMORGAN",
#     "latitude": 51.60947883960302,
#     "longitude": -3.9845510304974274,
#     "postcode": "SA2 8QA",
#     "geocode_coordinates": "SRID=27700;POINT (-3.984551030497427 51.60947883960302)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A3",
#       "boundary_identifier": "W11000031",
#       "name": "Swansea Bay University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RWDLB",
#     "name": "SKEGNESS & DISTRICT GENERAL HOSPITAL",
#     "website": "",
#     "address1": "DOROTHY AVENUE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SKEGNESS",
#     "county": "LINCOLNSHIRE",
#     "latitude": 53.14513129808872,
#     "longitude": 0.33316904076485293,
#     "postcode": "PE25 2BS",
#     "geocode_coordinates": "SRID=27700;POINT (0.3331690407648529 53.14513129808872)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RWD",
#       "name": "UNITED LINCOLNSHIRE HOSPITALS NHS TRUST",
#       "address_line_1": "LINCOLN COUNTY HOSPITAL",
#       "address_line_2": "GREETWELL ROAD",
#       "town": "LINCOLN",
#       "postcode": "LN2 5QY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000013",
#       "name": "NHS Lincolnshire Integrated Care Board",
#       "ods_code": "QJM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RRK99",
#     "name": "SOLIHULL HOSPITAL",
#     "website": "https://www.uhb.nhs.uk",
#     "address1": "LODE LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SOLIHULL",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.4171257,
#     "longitude": -1.774350882,
#     "postcode": "B91 2JL",
#     "geocode_coordinates": "SRID=27700;POINT (-1.774350882 52.4171257)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RRK",
#       "name": "UNIVERSITY HOSPITALS BIRMINGHAM NHS FOUNDATION TRUST",
#       "address_line_1": "QUEEN ELIZABETH HOSPITAL",
#       "address_line_2": "MINDELSOHN WAY",
#       "town": "BIRMINGHAM",
#       "postcode": "B15 2GW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000055",
#       "name": "NHS Birmingham and Solihull Integrated Care Board",
#       "ods_code": "QHL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RHM01",
#     "name": "SOUTHAMPTON GENERAL HOSPITAL",
#     "website": "http://www.uhs.nhs.uk",
#     "address1": "TREMONA ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SOUTHAMPTON",
#     "county": "HAMPSHIRE",
#     "latitude": 50.93302155,
#     "longitude": -1.435089946,
#     "postcode": "SO16 6YD",
#     "geocode_coordinates": "SRID=27700;POINT (-1.435089946 50.93302155)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ109"
#     },
#     "trust": {
#       "ods_code": "RHM",
#       "name": "UNIVERSITY HOSPITAL SOUTHAMPTON NHS FOUNDATION TRUST",
#       "address_line_1": "SOUTHAMPTON GENERAL HOSPITAL",
#       "address_line_2": "TREMONA ROAD",
#       "town": "SOUTHAMPTON",
#       "postcode": "SO16 6YD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RA773",
#     "name": "SOUTH BRISTOL COMMUNITY HOSPITAL",
#     "website": "http://www.uhbristol.nhs.uk/patients-and-visitors/your-hospitals/south-bristol-community-hospital/",
#     "address1": "HENGROVE PROMENADE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BRISTOL",
#     "county": "AVON",
#     "latitude": 51.41099548,
#     "longitude": -2.584929228,
#     "postcode": "BS14 0DE",
#     "geocode_coordinates": "SRID=27700;POINT (-2.584929228 51.41099548)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RA7",
#       "name": "UNIVERSITY HOSPITALS BRISTOL AND WESTON NHS FOUNDATION TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "MARLBOROUGH STREET",
#       "town": "BRISTOL",
#       "postcode": "BS1 3NU",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000039",
#       "name": "NHS Bristol, North Somerset and South Gloucestershire Integrated Care Board",
#       "ods_code": "QUY"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RAJ01",
#     "name": "SOUTHEND HOSPITAL",
#     "website": "https://www.mse.nhs.uk",
#     "address1": "PRITTLEWELL CHASE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WESTCLIFF-ON-SEA",
#     "county": "ESSEX",
#     "latitude": 51.55383682,
#     "longitude": 0.688631773,
#     "postcode": "SS0 0RY",
#     "geocode_coordinates": "SRID=27700;POINT (0.688631773 51.55383682)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ146"
#     },
#     "trust": {
#       "ods_code": "RAJ",
#       "name": "MID AND SOUTH ESSEX NHS FOUNDATION TRUST",
#       "address_line_1": "PRITTLEWELL CHASE",
#       "address_line_2": "",
#       "town": "WESTCLIFF-ON-SEA",
#       "postcode": "SS0 0RY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000026",
#       "name": "NHS Mid and South Essex Integrated Care Board",
#       "ods_code": "QH8"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVJ72",
#     "name": "SOUTH GLOUCESTERSHIRE COMMUNITY HEALTH SERVICES",
#     "website": "",
#     "address1": "8 BROOK OFFICE PARK",
#     "address2": "EMERSONS GREEN",
#     "address3": "",
#     "telephone": "",
#     "city": "BRISTOL",
#     "county": "AVON",
#     "latitude": 51.531696956239784,
#     "longitude": -2.5728256133103904,
#     "postcode": "BS16 7FL",
#     "geocode_coordinates": "SRID=27700;POINT (-2.57282561331039 51.53169695623978)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RVJ",
#       "name": "NORTH BRISTOL NHS TRUST",
#       "address_line_1": "SOUTHMEAD HOSPITAL",
#       "address_line_2": "SOUTHMEAD ROAD",
#       "town": "BRISTOL",
#       "postcode": "BS10 5NB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000039",
#       "name": "NHS Bristol, North Somerset and South Gloucestershire Integrated Care Board",
#       "ods_code": "QUY"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R0B0Q",
#     "name": "SOUTH TYNESIDE DISTRICT HOSPITAL",
#     "website": null,
#     "address1": "HARTON LANE",
#     "address2": null,
#     "address3": null,
#     "telephone": null,
#     "city": "SOUTH SHIELDS",
#     "county": null,
#     "latitude": 54.971208,
#     "longitude": -1.428468,
#     "postcode": "NE34 0PL",
#     "geocode_coordinates": "SRID=27700;POINT (-1.428468 54.971208)",
#     "active": true,
#     "published_at": "2019-03-13",
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ141"
#     },
#     "trust": {
#       "ods_code": "R0B",
#       "name": "SOUTH TYNESIDE AND SUNDERLAND NHS FOUNDATION TRUST",
#       "address_line_1": "SUNDERLAND ROYAL HOSPITAL",
#       "address_line_2": "KAYLL ROAD",
#       "town": "SUNDERLAND",
#       "postcode": "SR4 7TP",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWG07",
#     "name": "SPIRE BUSHEY HOSPITAL",
#     "website": "",
#     "address1": "HEATHBOURNE ROAD",
#     "address2": "BUSHEY HEATH",
#     "address3": "",
#     "telephone": "",
#     "city": "BUSHEY",
#     "county": "",
#     "latitude": 51.637390004846814,
#     "longitude": -0.3305057868647216,
#     "postcode": "WD23 1RD",
#     "geocode_coordinates": "SRID=27700;POINT (-0.3305057868647216 51.63739000484681)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RWG",
#       "name": "WEST HERTFORDSHIRE TEACHING HOSPITALS NHS TRUST",
#       "address_line_1": "TRUST OFFICES",
#       "address_line_2": "WATFORD GENERAL HOSPITAL",
#       "town": "WATFORD",
#       "postcode": "WD18 0HB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000025",
#       "name": "NHS Hertfordshire and West Essex Integrated Care Board",
#       "ods_code": "QM7"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RNN82",
#     "name": "SPRINGBOARD CHILD DEVELOPMENT CENTRE",
#     "website": "",
#     "address1": "ORTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CARLISLE",
#     "county": "CUMBRIA",
#     "latitude": 54.88822587966728,
#     "longitude": -2.972025091691566,
#     "postcode": "CA2 7HE",
#     "geocode_coordinates": "SRID=27700;POINT (-2.972025091691566 54.88822587966728)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RNN",
#       "name": "NORTH CUMBRIA INTEGRATED CARE NHS FOUNDATION TRUST",
#       "address_line_1": "PILLARS BUILDING",
#       "address_line_2": "CUMBERLAND INFIRMARY",
#       "town": "CARLISLE",
#       "postcode": "CA2 7HY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTK23",
#     "name": "STAINES HEALTH CENTRE",
#     "website": "",
#     "address1": "KNOWLE GREEN",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "STAINES",
#     "county": "MIDDLESEX",
#     "latitude": 51.429085727109076,
#     "longitude": -0.5006946625144656,
#     "postcode": "TW18 1XD",
#     "geocode_coordinates": "SRID=27700;POINT (-0.5006946625144656 51.42908572710908)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTK",
#       "name": "ASHFORD AND ST PETER'S HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "ST PETERS HOSPITAL",
#       "address_line_2": "GUILDFORD ROAD",
#       "town": "CHERTSEY",
#       "postcode": "KT16 0PZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000063",
#       "name": "NHS Surrey Heartlands Integrated Care Board",
#       "ods_code": "QXU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RX160",
#     "name": "ST ANN'S VALLEY CENTRE",
#     "website": "",
#     "address1": "2 LIVINGSTONE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NOTTINGHAM",
#     "county": "NOTTINGHAMSHIRE",
#     "latitude": 52.96281834731625,
#     "longitude": -1.1361160766496041,
#     "postcode": "NG3 3GG",
#     "geocode_coordinates": "SRID=27700;POINT (-1.136116076649604 52.96281834731625)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RX1",
#       "name": "NOTTINGHAM UNIVERSITY HOSPITALS NHS TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "QUEENS MEDICAL CENTRE",
#       "town": "NOTTINGHAM",
#       "postcode": "NG7 2UH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000060",
#       "name": "NHS Nottingham and Nottinghamshire Integrated Care Board",
#       "ods_code": "QT1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWJ09",
#     "name": "STEPPING HILL HOSPITAL",
#     "website": "http://www.stockport.nhs.uk",
#     "address1": "POPLAR GROVE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "STOCKPORT",
#     "county": "CHESHIRE",
#     "latitude": 53.38378143,
#     "longitude": -2.132004976,
#     "postcode": "SK2 7JE",
#     "geocode_coordinates": "SRID=27700;POINT (-2.132004976 53.38378143)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ069"
#     },
#     "trust": {
#       "ods_code": "RWJ",
#       "name": "STOCKPORT NHS FOUNDATION TRUST",
#       "address_line_1": "STEPPING HILL HOSPITAL",
#       "address_line_2": "POPLAR GROVE",
#       "town": "STOCKPORT",
#       "postcode": "SK2 7JE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJ701",
#     "name": "ST GEORGE'S HOSPITAL (TOOTING)",
#     "website": "http://www.stgeorges.nhs.uk",
#     "address1": "BLACKSHAW ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.42668152,
#     "longitude": -0.175704554,
#     "postcode": "SW17 0QT",
#     "geocode_coordinates": "SRID=27700;POINT (-0.175704554 51.42668152)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ023"
#     },
#     "trust": {
#       "ods_code": "RJ7",
#       "name": "ST GEORGE'S UNIVERSITY HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "ST GEORGE'S HOSPITAL",
#       "address_line_2": "BLACKSHAW ROAD",
#       "town": "LONDON",
#       "postcode": "SW17 0QT",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000031",
#       "name": "NHS South West London Integrated Care Board",
#       "ods_code": "QWE"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Wandsworth",
#       "gss_code": "E09000032"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBN02",
#     "name": "ST HELENS HOSPITAL",
#     "website": "http://www.sthk.nhs.uk",
#     "address1": "MARSHALLS CROSS ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ST. HELENS",
#     "county": "MERSEYSIDE",
#     "latitude": 53.43953323,
#     "longitude": -2.718886852,
#     "postcode": "WA9 3DA",
#     "geocode_coordinates": "SRID=27700;POINT (-2.718886852 53.43953323)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RBN",
#       "name": "ST HELENS AND KNOWSLEY TEACHING HOSPITALS NHS TRUST",
#       "address_line_1": "WHISTON HOSPITAL",
#       "address_line_2": "WARRINGTON ROAD",
#       "town": "PRESCOT",
#       "postcode": "L35 5DR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RDE90",
#     "name": "ST HELENS HOUSE",
#     "website": "",
#     "address1": "571 FOXHALL ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "IPSWICH",
#     "county": "",
#     "latitude": 52.05222911984776,
#     "longitude": 1.196965668228381,
#     "postcode": "IP3 8LX",
#     "geocode_coordinates": "SRID=27700;POINT (1.196965668228381 52.05222911984776)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RDE",
#       "name": "EAST SUFFOLK AND NORTH ESSEX NHS FOUNDATION TRUST",
#       "address_line_1": "COLCHESTER DIST GENERAL HOSPITAL",
#       "address_line_2": "TURNER ROAD",
#       "town": "COLCHESTER",
#       "postcode": "CO4 5JL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000023",
#       "name": "NHS Suffolk and North East Essex Integrated Care Board",
#       "ods_code": "QJG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVR05",
#     "name": "ST HELIER HOSPITAL",
#     "website": "http://www.epsom-sthelier.nhs.uk",
#     "address1": "WRYTHE LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CARSHALTON",
#     "county": "SURREY",
#     "latitude": 51.38018799,
#     "longitude": -0.183718503,
#     "postcode": "SM5 1AA",
#     "geocode_coordinates": "SRID=27700;POINT (-0.183718503 51.38018799)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ050"
#     },
#     "trust": {
#       "ods_code": "RVR",
#       "name": "EPSOM AND ST HELIER UNIVERSITY HOSPITALS NHS TRUST",
#       "address_line_1": "ST HELIER HOSPITAL",
#       "address_line_2": "WRYTHE LANE",
#       "town": "CARSHALTON",
#       "postcode": "SM5 1AA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000063",
#       "name": "NHS Surrey Heartlands Integrated Care Board",
#       "ods_code": "QXU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RR813",
#     "name": "ST JAMES'S UNIVERSITY HOSPITAL",
#     "website": "http://www.leedsth.nhs.uk",
#     "address1": "BECKETT STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LEEDS",
#     "county": "WEST YORKSHIRE",
#     "latitude": 53.80687332,
#     "longitude": -1.520343781,
#     "postcode": "LS9 7TF",
#     "geocode_coordinates": "SRID=27700;POINT (-1.520343781 53.80687332)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RR8",
#       "name": "LEEDS TEACHING HOSPITALS NHS TRUST",
#       "address_line_1": "ST. JAMES'S UNIVERSITY HOSPITAL",
#       "address_line_2": "BECKETT STREET",
#       "town": "LEEDS",
#       "postcode": "LS9 7TF",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000054",
#       "name": "NHS West Yorkshire Integrated Care Board",
#       "ods_code": "QWO"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBK70",
#     "name": "ST JOHNS MEDICAL CENTRE M91007",
#     "website": "",
#     "address1": "HIGH STREET",
#     "address2": "WALSALL WOOD",
#     "address3": "",
#     "telephone": "",
#     "city": "WALSALL",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.625493402530005,
#     "longitude": -1.9347685780981938,
#     "postcode": "WS9 9LP",
#     "geocode_coordinates": "SRID=27700;POINT (-1.934768578098194 52.62549340253)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RBK",
#       "name": "WALSALL HEALTHCARE NHS TRUST",
#       "address_line_1": "MANOR HOSPITAL",
#       "address_line_2": "MOAT ROAD",
#       "town": "WALSALL",
#       "postcode": "WS2 9PS",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000062",
#       "name": "NHS Black Country Integrated Care Board",
#       "ods_code": "QUA"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RAE05",
#     "name": "ST LUKES HOSPITAL",
#     "website": null,
#     "address1": "LITTLE HORTON LANE",
#     "address2": null,
#     "address3": null,
#     "telephone": null,
#     "city": "BRADFORD",
#     "county": null,
#     "latitude": 53.783714,
#     "longitude": -1.760706,
#     "postcode": "BD5 0NA",
#     "geocode_coordinates": "SRID=27700;POINT (-1.760706 53.783714)",
#     "active": true,
#     "published_at": "1991-04-01",
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ105"
#     },
#     "trust": {
#       "ods_code": "RAE",
#       "name": "BRADFORD TEACHING HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "BRADFORD ROYAL INFIRMARY",
#       "address_line_2": "DUCKWORTH LANE",
#       "town": "BRADFORD",
#       "postcode": "BD9 6RJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000054",
#       "name": "NHS West Yorkshire Integrated Care Board",
#       "ods_code": "QWO"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1F01",
#     "name": "ST MARY'S HOSPITAL",
#     "website": "https://www.iow.nhs.uk/our-services/mental-health-services/isle-talk.htm",
#     "address1": "PARKHURST ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NEWPORT",
#     "county": "ISLE OF WIGHT",
#     "latitude": 50.71084595,
#     "longitude": -1.301358461,
#     "postcode": "PO30 5TG",
#     "geocode_coordinates": "SRID=27700;POINT (-1.301358461 50.71084595)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ075"
#     },
#     "trust": {
#       "ods_code": "R1F",
#       "name": "ISLE OF WIGHT NHS TRUST",
#       "address_line_1": "ST MARYS HOSPITAL",
#       "address_line_2": "PARKHURST ROAD",
#       "town": "NEWPORT",
#       "postcode": "PO30 5TG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RP1A1",
#     "name": "ST MARY'S HOSPITAL",
#     "website": "http://www.nhft.nhs.uk",
#     "address1": "77 LONDON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "KETTERING",
#     "county": "NORTHAMPTONSHIRE",
#     "latitude": 52.39410019,
#     "longitude": -0.722185016,
#     "postcode": "NN15 7PW",
#     "geocode_coordinates": "SRID=27700;POINT (-0.722185016 52.39410019)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RP1",
#       "name": "NORTHAMPTONSHIRE HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "ST MARYS HOSPITAL",
#       "address_line_2": "77 LONDON ROAD",
#       "town": "KETTERING",
#       "postcode": "NN15 7PW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000059",
#       "name": "NHS Northamptonshire Integrated Care Board",
#       "ods_code": "QPM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RYJ01",
#     "name": "ST MARY'S HOSPITAL (HQ)",
#     "website": "https://www.imperial.nhs.uk/our-locations/st-marys-hospital",
#     "address1": "PRAED STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.51697159,
#     "longitude": -0.173555061,
#     "postcode": "W2 1NY",
#     "geocode_coordinates": "SRID=27700;POINT (-0.173555061 51.51697159)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ202"
#     },
#     "trust": {
#       "ods_code": "RYJ",
#       "name": "IMPERIAL COLLEGE HEALTHCARE NHS TRUST",
#       "address_line_1": "THE BAYS",
#       "address_line_2": "ST MARYS HOSPITAL",
#       "town": "LONDON",
#       "postcode": "W2 1BL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000027",
#       "name": "NHS North West London Integrated Care Board",
#       "ods_code": "QRV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Westminster",
#       "gss_code": "E09000033"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RA707",
#     "name": "ST MICHAEL'S HOSPITAL",
#     "website": "http://www.uhbristol.nhs.uk/your-hospitals/st-michaels-hospital.html",
#     "address1": "SOUTHWELL STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BRISTOL",
#     "county": "",
#     "latitude": 51.45913696,
#     "longitude": -2.599376917,
#     "postcode": "BS2 8EG",
#     "geocode_coordinates": "SRID=27700;POINT (-2.599376917 51.45913696)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RA7",
#       "name": "UNIVERSITY HOSPITALS BRISTOL AND WESTON NHS FOUNDATION TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "MARLBOROUGH STREET",
#       "town": "BRISTOL",
#       "postcode": "BS1 3NU",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000039",
#       "name": "NHS Bristol, North Somerset and South Gloucestershire Integrated Care Board",
#       "ods_code": "QUY"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXQ02",
#     "name": "STOKE MANDEVILLE HOSPITAL",
#     "website": "http://www.buckshealthcare.nhs.uk/For%20patients%20and%20visitors/stoke-mandeville-hospital.htm",
#     "address1": "MANDEVILLE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "AYLESBURY",
#     "county": "BUCKINGHAMSHIRE",
#     "latitude": 51.79797745,
#     "longitude": -0.801997542,
#     "postcode": "HP21 8AL",
#     "geocode_coordinates": "SRID=27700;POINT (-0.801997542 51.79797745)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ028"
#     },
#     "trust": {
#       "ods_code": "RXQ",
#       "name": "BUCKINGHAMSHIRE HEALTHCARE NHS TRUST",
#       "address_line_1": "AMERSHAM HOSPITAL",
#       "address_line_2": "WHIELDEN STREET",
#       "town": "AMERSHAM",
#       "postcode": "HP7 0JD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000044",
#       "name": "NHS Buckinghamshire, Oxfordshire and Berkshire West Integrated Care Board",
#       "ods_code": "QU9"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTK01",
#     "name": "ST PETER'S HOSPITAL",
#     "website": "http://www.ashfordstpeters.nhs.uk",
#     "address1": "GUILDFORD ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CHERTSEY",
#     "county": "SURREY",
#     "latitude": 51.37783432,
#     "longitude": -0.527046025,
#     "postcode": "KT16 0PZ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.527046025 51.37783432)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ176"
#     },
#     "trust": {
#       "ods_code": "RTK",
#       "name": "ASHFORD AND ST PETER'S HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "ST PETERS HOSPITAL",
#       "address_line_2": "GUILDFORD ROAD",
#       "town": "CHERTSEY",
#       "postcode": "KT16 0PZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000063",
#       "name": "NHS Surrey Heartlands Integrated Care Board",
#       "ods_code": "QXU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RX128",
#     "name": "STRELLEY HEALTH CENTRE",
#     "website": "",
#     "address1": "116 STRELLEY ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NOTTINGHAM",
#     "county": "NOTTINGHAMSHIRE",
#     "latitude": 52.97347694794381,
#     "longitude": -1.2266910978761432,
#     "postcode": "NG8 6LN",
#     "geocode_coordinates": "SRID=27700;POINT (-1.226691097876143 52.97347694794381)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RX1",
#       "name": "NOTTINGHAM UNIVERSITY HOSPITALS NHS TRUST",
#       "address_line_1": "TRUST HEADQUARTERS",
#       "address_line_2": "QUEENS MEDICAL CENTRE",
#       "town": "NOTTINGHAM",
#       "postcode": "NG7 2UH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000060",
#       "name": "NHS Nottingham and Nottinghamshire Integrated Care Board",
#       "ods_code": "QT1"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Children's Epilepsy Workstream in Trent",
#       "boundary_identifier": "CEWT",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RYR16",
#     "name": "ST RICHARD'S HOSPITAL",
#     "website": "https://www.uhsussex.nhs.uk/",
#     "address1": "SPITALFIELD LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CHICHESTER",
#     "county": "WEST SUSSEX",
#     "latitude": 50.84355545,
#     "longitude": -0.768012762,
#     "postcode": "PO19 6SE",
#     "geocode_coordinates": "SRID=27700;POINT (-0.768012762 50.84355545)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ031"
#     },
#     "trust": {
#       "ods_code": "RYR",
#       "name": "UNIVERSITY HOSPITALS SUSSEX NHS FOUNDATION TRUST",
#       "address_line_1": "WORTHING HOSPITAL",
#       "address_line_2": "LYNDHURST ROAD",
#       "town": "WORTHING",
#       "postcode": "BN11 2DH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000064",
#       "name": "NHS Sussex Integrated Care Board",
#       "ods_code": "QNX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWJ04",
#     "name": "ST THOMAS HOSPITAL",
#     "website": "",
#     "address1": "SHAW HEATH",
#     "address2": "GILMORE STREET",
#     "address3": "",
#     "telephone": "",
#     "city": "STOCKPORT",
#     "county": "CHESHIRE",
#     "latitude": 53.401726817055895,
#     "longitude": -2.160042086204846,
#     "postcode": "SK3 8DN",
#     "geocode_coordinates": "SRID=27700;POINT (-2.160042086204846 53.40172681705589)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RWJ",
#       "name": "STOCKPORT NHS FOUNDATION TRUST",
#       "address_line_1": "STEPPING HILL HOSPITAL",
#       "address_line_2": "POPLAR GROVE",
#       "town": "STOCKPORT",
#       "postcode": "SK2 7JE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJ122",
#     "name": "ST THOMAS' HOSPITAL",
#     "website": "https://www.guysandstthomas.nhs.uk",
#     "address1": "WESTMINSTER BRIDGE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.49795914,
#     "longitude": -0.118890636,
#     "postcode": "SE1 7EH",
#     "geocode_coordinates": "SRID=27700;POINT (-0.118890636 51.49795914)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ082"
#     },
#     "trust": {
#       "ods_code": "RJ1",
#       "name": "GUY'S AND ST THOMAS' NHS FOUNDATION TRUST",
#       "address_line_1": "ST THOMAS' HOSPITAL",
#       "address_line_2": "WESTMINSTER BRIDGE ROAD",
#       "town": "LONDON",
#       "postcode": "SE1 7EH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000030",
#       "name": "NHS South East London Integrated Care Board",
#       "ods_code": "QKK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Lambeth",
#       "gss_code": "E09000022"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A6AT",
#     "name": "ST WOOLOS COMMUNITY",
#     "website": "",
#     "address1": "131 STOW HILL",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NEWPORT",
#     "county": "GWENT",
#     "latitude": 51.58256284027904,
#     "longitude": -3.002913490019792,
#     "postcode": "NP20 4SZ",
#     "geocode_coordinates": "SRID=27700;POINT (-3.002913490019792 51.58256284027904)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A6",
#       "boundary_identifier": "W11000028",
#       "name": "Aneurin Bevan University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "R0B01",
#     "name": "SUNDERLAND ROYAL HOSPITAL",
#     "website": "",
#     "address1": "KAYLL ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SUNDERLAND",
#     "county": "",
#     "latitude": 54.90221024,
#     "longitude": -1.410297871,
#     "postcode": "SR4 7TP",
#     "geocode_coordinates": "SRID=27700;POINT (-1.410297871 54.90221024)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ080"
#     },
#     "trust": {
#       "ods_code": "R0B",
#       "name": "SOUTH TYNESIDE AND SUNDERLAND NHS FOUNDATION TRUST",
#       "address_line_1": "SUNDERLAND ROYAL HOSPITAL",
#       "address_line_2": "KAYLL ROAD",
#       "town": "SUNDERLAND",
#       "postcode": "SR4 7TP",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RN341",
#     "name": "SWINDON HEALTH CENTRE",
#     "website": "",
#     "address1": "CARFAX STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SWINDON",
#     "county": "WILTSHIRE",
#     "latitude": 51.563553146767845,
#     "longitude": -1.7808641421440663,
#     "postcode": "SN1 1ED",
#     "geocode_coordinates": "SRID=27700;POINT (-1.780864142144066 51.56355314676784)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RN3",
#       "name": "GREAT WESTERN HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "GREAT WESTERN HOSPITAL",
#       "address_line_2": "MARLBOROUGH ROAD",
#       "town": "SWINDON",
#       "postcode": "SN3 6BB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000040",
#       "name": "NHS Bath and North East Somerset, Swindon and Wiltshire Integrated Care Board",
#       "ods_code": "QOX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RM357",
#     "name": "SWINTON GATEWAY",
#     "website": "",
#     "address1": "100 CHORLEY ROAD",
#     "address2": "SWINTON",
#     "address3": "",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.51252327906953,
#     "longitude": -2.3414097174362394,
#     "postcode": "M27 6BP",
#     "geocode_coordinates": "SRID=27700;POINT (-2.341409717436239 53.51252327906953)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RM3",
#       "name": "NORTHERN CARE ALLIANCE NHS FOUNDATION TRUST",
#       "address_line_1": "SALFORD ROYAL",
#       "address_line_2": "STOTT LANE",
#       "town": "SALFORD",
#       "postcode": "M6 8HD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RMP01",
#     "name": "TAMESIDE GENERAL HOSPITAL",
#     "website": "http://www.tamesidehospital.nhs.uk",
#     "address1": "FOUNTAIN STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ASHTON-UNDER-LYNE",
#     "county": "LANCASHIRE",
#     "latitude": 53.49153519,
#     "longitude": -2.071418524,
#     "postcode": "OL6 9RW",
#     "geocode_coordinates": "SRID=27700;POINT (-2.071418524 53.49153519)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ140"
#     },
#     "trust": {
#       "ods_code": "RMP",
#       "name": "TAMESIDE AND GLOSSOP INTEGRATED CARE NHS FOUNDATION TRUST",
#       "address_line_1": "TAMESIDE GENERAL HOSPITAL",
#       "address_line_2": "FOUNTAIN STREET",
#       "town": "ASHTON-UNDER-LYNE",
#       "postcode": "OL6 9RW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1CD1",
#     "name": "THE ADELAIDE HEALTH CENTRE",
#     "website": "",
#     "address1": "WILLIAM MACLEOD WAY",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SOUTHAMPTON",
#     "county": "HAMPSHIRE",
#     "latitude": 50.92486696906429,
#     "longitude": -1.4478521063594827,
#     "postcode": "SO16 4XE",
#     "geocode_coordinates": "SRID=27700;POINT (-1.447852106359483 50.92486696906429)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "R1C",
#       "name": "SOLENT NHS TRUST",
#       "address_line_1": "SOLENT NHS TRUST HEADQUARTERS",
#       "address_line_2": "HIGHPOINT VENUE",
#       "town": "SOUTHAMPTON",
#       "postcode": "SO19 8BR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A6G9",
#     "name": "THE GRANGE UNIVERSITY HOSPITAL",
#     "website": "",
#     "address1": "CAERLEON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "CWMBRAN",
#     "county": "",
#     "latitude": 51.64835102816606,
#     "longitude": -2.9959835016593503,
#     "postcode": "NP44 8YN",
#     "geocode_coordinates": "SRID=27700;POINT (-2.99598350165935 51.64835102816606)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A6",
#       "boundary_identifier": "W11000028",
#       "name": "Aneurin Bevan University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RN325",
#     "name": "THE GREAT WESTERN HOSPITAL",
#     "website": "https://www.gwh.nhs.uk",
#     "address1": "MARLBOROUGH ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SWINDON",
#     "county": "WILTSHIRE",
#     "latitude": 51.53853226,
#     "longitude": -1.727185845,
#     "postcode": "SN3 6BB",
#     "geocode_coordinates": "SRID=27700;POINT (-1.727185845 51.53853226)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ221"
#     },
#     "trust": {
#       "ods_code": "RN3",
#       "name": "GREAT WESTERN HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "GREAT WESTERN HOSPITAL",
#       "address_line_2": "MARLBOROUGH ROAD",
#       "town": "SWINDON",
#       "postcode": "SN3 6BB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000040",
#       "name": "NHS Bath and North East Somerset, Swindon and Wiltshire Integrated Care Board",
#       "ods_code": "QOX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTRAT",
#     "name": "THE JAMES COOK UNIVERSITY HOSPITAL",
#     "website": "https://www.southtees.nhs.uk/",
#     "address1": "MARTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "MIDDLESBROUGH",
#     "county": "CLEVELAND",
#     "latitude": 54.55175781,
#     "longitude": -1.214789987,
#     "postcode": "TS4 3BW",
#     "geocode_coordinates": "SRID=27700;POINT (-1.214789987 54.55175781)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ133"
#     },
#     "trust": {
#       "ods_code": "RTR",
#       "name": "SOUTH TEES HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "JAMES COOK UNIVERSITY HOSPITAL",
#       "address_line_2": "MARTON ROAD",
#       "town": "MIDDLESBROUGH",
#       "postcode": "TS4 3BW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000051",
#       "name": "NHS Humber and North Yorkshire Integrated Care Board",
#       "ods_code": "QOQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWF03",
#     "name": "THE MAIDSTONE HOSPITAL",
#     "website": "http://www.mtw.nhs.uk/",
#     "address1": "HERMITAGE LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "MAIDSTONE",
#     "county": "KENT",
#     "latitude": 51.27366257,
#     "longitude": 0.483988225,
#     "postcode": "ME16 9QQ",
#     "geocode_coordinates": "SRID=27700;POINT (0.483988225 51.27366257)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ125"
#     },
#     "trust": {
#       "ods_code": "RWF",
#       "name": "MAIDSTONE AND TUNBRIDGE WELLS NHS TRUST",
#       "address_line_1": "THE MAIDSTONE HOSPITAL",
#       "address_line_2": "HERMITAGE LANE",
#       "town": "MAIDSTONE",
#       "postcode": "ME16 9QQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000032",
#       "name": "NHS Kent and Medway Integrated Care Board",
#       "ods_code": "QKS"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A3LE",
#     "name": "THE MOUNT SURGERY",
#     "website": "",
#     "address1": "MARGAM ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "PORT TALBOT",
#     "county": "WEST GLAMORGAN",
#     "latitude": 51.582985138982984,
#     "longitude": -3.768102780225508,
#     "postcode": "SA13 2BN",
#     "geocode_coordinates": "SRID=27700;POINT (-3.768102780225508 51.58298513898298)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A3",
#       "boundary_identifier": "W11000031",
#       "name": "Swansea Bay University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RJC66",
#     "name": "THE ORCHARD CENTRE",
#     "website": "",
#     "address1": "LOWER HILLMORTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "RUGBY",
#     "county": "WARWICKSHIRE",
#     "latitude": 52.370419434583766,
#     "longitude": -1.252717489422648,
#     "postcode": "CV21 3SR",
#     "geocode_coordinates": "SRID=27700;POINT (-1.252717489422648 52.37041943458377)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RJC",
#       "name": "SOUTH WARWICKSHIRE UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "WARWICK HOSPITAL",
#       "address_line_2": "LAKIN ROAD",
#       "town": "WARWICK",
#       "postcode": "CV34 5BW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000018",
#       "name": "NHS Coventry and Warwickshire Integrated Care Board",
#       "ods_code": "QWU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXWAT",
#     "name": "THE PRINCESS ROYAL HOSPITAL",
#     "website": "http://www.sath.nhs.uk",
#     "address1": "APLEY CASTLE",
#     "address2": "GRAINGER DRIVE",
#     "address3": "",
#     "telephone": "",
#     "city": "TELFORD",
#     "county": "SHROPSHIRE",
#     "latitude": 52.71211243,
#     "longitude": -2.511476278,
#     "postcode": "TF1 6TF",
#     "geocode_coordinates": "SRID=27700;POINT (-2.511476278 52.71211243)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ094"
#     },
#     "trust": {
#       "ods_code": "RXW",
#       "name": "THE SHREWSBURY AND TELFORD HOSPITAL NHS TRUST",
#       "address_line_1": "MYTTON OAK ROAD",
#       "address_line_2": "",
#       "town": "SHREWSBURY",
#       "postcode": "SY3 8XQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000011",
#       "name": "NHS Shropshire, Telford and Wrekin Integrated Care Board",
#       "ods_code": "QOC"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RCX70",
#     "name": "THE QUEEN ELIZABETH HOSPITAL",
#     "website": "http://www.qehkl.nhs.uk",
#     "address1": "GAYTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "KING'S LYNN",
#     "county": "NORFOLK",
#     "latitude": 52.75660706,
#     "longitude": 0.446693152,
#     "postcode": "PE30 4ET",
#     "geocode_coordinates": "SRID=27700;POINT (0.446693152 52.75660706)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ156"
#     },
#     "trust": {
#       "ods_code": "RCX",
#       "name": "THE QUEEN ELIZABETH HOSPITAL, KING'S LYNN, NHS FOUNDATION TRUST",
#       "address_line_1": "QUEEN ELIZABETH HOSPITAL",
#       "address_line_2": "GAYTON ROAD",
#       "town": "KING'S LYNN",
#       "postcode": "PE30 4ET",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000022",
#       "name": "NHS Norfolk and Waveney Integrated Care Board",
#       "ods_code": "QMM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A5B1",
#     "name": "THE ROYAL GLAMORGAN HOSPITAL AND COMMUNITY PAEDIATRICS",
#     "website": "",
#     "address1": "YNYSMAERDY",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "PONTYCLUN",
#     "county": "MID GLAMORGAN",
#     "latitude": 51.54786257990656,
#     "longitude": -3.3914877354776594,
#     "postcode": "CF72 8XR",
#     "geocode_coordinates": "SRID=27700;POINT (-3.391487735477659 51.54786257990656)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A5",
#       "boundary_identifier": "W11000030",
#       "name": "Cwm Taf Morgannwg University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "R1H12",
#     "name": "THE ROYAL LONDON HOSPITAL",
#     "website": "http://www.bartshealth.nhs.uk/",
#     "address1": "WHITECHAPEL",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.51869965,
#     "longitude": -0.060150061,
#     "postcode": "E1 1BB",
#     "geocode_coordinates": "SRID=27700;POINT (-0.060150061 51.51869965)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ059"
#     },
#     "trust": {
#       "ods_code": "R1H",
#       "name": "BARTS HEALTH NHS TRUST",
#       "address_line_1": "THE ROYAL LONDON HOSPITAL",
#       "address_line_2": "80 NEWARK STREET",
#       "town": "LONDON",
#       "postcode": "E1 2ES",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000029",
#       "name": "NHS North East London Integrated Care Board",
#       "ods_code": "QMF"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Tower Hamlets",
#       "gss_code": "E09000030"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTD02",
#     "name": "THE ROYAL VICTORIA INFIRMARY",
#     "website": "http://www.newcastle-hospitals.nhs.uk/",
#     "address1": "QUEEN VICTORIA ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "NEWCASTLE UPON TYNE",
#     "county": "TYNE AND WEAR",
#     "latitude": 54.98021698,
#     "longitude": -1.618839502,
#     "postcode": "NE1 4LP",
#     "geocode_coordinates": "SRID=27700;POINT (-1.618839502 54.98021698)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ032"
#     },
#     "trust": {
#       "ods_code": "RTD",
#       "name": "THE NEWCASTLE UPON TYNE HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "FREEMAN HOSPITAL",
#       "address_line_2": "FREEMAN ROAD",
#       "town": "NEWCASTLE UPON TYNE",
#       "postcode": "NE7 7DN",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWFTW",
#     "name": "THE TUNBRIDGE WELLS HOSPITAL",
#     "website": "http://www.mtw.nhs.uk",
#     "address1": "TONBRIDGE ROAD",
#     "address2": "PEMBURY",
#     "address3": "",
#     "telephone": "",
#     "city": "TUNBRIDGE WELLS",
#     "county": "KENT",
#     "latitude": 51.14845276,
#     "longitude": 0.307484597,
#     "postcode": "TN2 4QJ",
#     "geocode_coordinates": "SRID=27700;POINT (0.307484597 51.14845276)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ216"
#     },
#     "trust": {
#       "ods_code": "RWF",
#       "name": "MAIDSTONE AND TUNBRIDGE WELLS NHS TRUST",
#       "address_line_1": "THE MAIDSTONE HOSPITAL",
#       "address_line_2": "HERMITAGE LANE",
#       "town": "MAIDSTONE",
#       "postcode": "ME16 9QQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000032",
#       "name": "NHS Kent and Medway Integrated Care Board",
#       "ods_code": "QKS"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RKEQ4",
#     "name": "THE WHITTINGTON HOSPITAL",
#     "website": "https://www.whittington.nhs.uk",
#     "address1": "MAGDALA AVENUE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.56647873,
#     "longitude": -0.139077902,
#     "postcode": "N19 5NF",
#     "geocode_coordinates": "SRID=27700;POINT (-0.139077902 51.56647873)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ045"
#     },
#     "trust": {
#       "ods_code": "RKE",
#       "name": "WHITTINGTON HEALTH NHS TRUST",
#       "address_line_1": "THE WHITTINGTON HOSPITAL",
#       "address_line_2": "MAGDALA AVENUE",
#       "town": "LONDON",
#       "postcode": "N19 5NF",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Islington",
#       "gss_code": "E09000019"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RA901",
#     "name": "TORBAY HOSPITAL",
#     "website": "http://www.torbayandsouthdevon.nhs.uk/",
#     "address1": "NEWTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "TORQUAY",
#     "county": "DEVON",
#     "latitude": 50.48232269,
#     "longitude": -3.553790569,
#     "postcode": "TQ2 7AA",
#     "geocode_coordinates": "SRID=27700;POINT (-3.553790569 50.48232269)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ152"
#     },
#     "trust": {
#       "ods_code": "RA9",
#       "name": "TORBAY AND SOUTH DEVON NHS FOUNDATION TRUST",
#       "address_line_1": "TORBAY HOSPITAL",
#       "address_line_2": "NEWTON ROAD",
#       "town": "TORQUAY",
#       "postcode": "TQ2 7AA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000037",
#       "name": "NHS Devon Integrated Care Board",
#       "ods_code": "QJK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RM321",
#     "name": "TRAFFORD GENERAL HOSPITAL",
#     "website": "",
#     "address1": "MOORSIDE ROAD",
#     "address2": "URMSTON",
#     "address3": "",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.453839217199565,
#     "longitude": -2.3690510967929255,
#     "postcode": "M41 5SL",
#     "geocode_coordinates": "SRID=27700;POINT (-2.369051096792925 53.45383921719957)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RM3",
#       "name": "NORTHERN CARE ALLIANCE NHS FOUNDATION TRUST",
#       "address_line_1": "SALFORD ROYAL",
#       "address_line_2": "STOTT LANE",
#       "town": "SALFORD",
#       "postcode": "M6 8HD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "Q3K9W",
#     "name": "TRAFFORD LOCAL CARE ORGANISATION",
#     "website": "",
#     "address1": "TOWN HALL",
#     "address2": "TALBOT ROAD",
#     "address3": "STRETFORD",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "",
#     "latitude": 53.45898933439508,
#     "longitude": -2.2877698025722513,
#     "postcode": "M32 0TH",
#     "geocode_coordinates": "SRID=27700;POINT (-2.287769802572251 53.45898933439508)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ136"
#     },
#     "trust": {
#       "ods_code": "R0A",
#       "name": "MANCHESTER UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "COBBETT HOUSE",
#       "address_line_2": "OXFORD ROAD",
#       "town": "MANCHESTER",
#       "postcode": "M13 9WL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RRV03",
#     "name": "UNIVERSITY COLLEGE HOSPITAL",
#     "website": "https://www.uclh.nhs.uk/our-services/our-hospitals/university-college-hospital",
#     "address1": "235 EUSTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.5248909,
#     "longitude": -0.136896163,
#     "postcode": "NW1 2BU",
#     "geocode_coordinates": "SRID=27700;POINT (-0.136896163 51.5248909)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ203"
#     },
#     "trust": {
#       "ods_code": "RRV",
#       "name": "UNIVERSITY COLLEGE LONDON HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "250 EUSTON ROAD",
#       "address_line_2": "",
#       "town": "LONDON",
#       "postcode": "NW1 2PG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000028",
#       "name": "NHS North Central London Integrated Care Board",
#       "ods_code": "QMJ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Camden",
#       "gss_code": "E09000007"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RKB01",
#     "name": "UNIVERSITY HOSPITAL (COVENTRY)",
#     "website": "http://www.uhcw.nhs.uk",
#     "address1": "CLIFFORD BRIDGE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "COVENTRY",
#     "county": "WEST MIDLANDS",
#     "latitude": 52.42121506,
#     "longitude": -1.438388586,
#     "postcode": "CV2 2DX",
#     "geocode_coordinates": "SRID=27700;POINT (-1.438388586 52.42121506)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ122"
#     },
#     "trust": {
#       "ods_code": "RKB",
#       "name": "UNIVERSITY HOSPITALS COVENTRY AND WARWICKSHIRE NHS TRUST",
#       "address_line_1": "WALSGRAVE GENERAL HOSPITAL",
#       "address_line_2": "CLIFFORD BRIDGE ROAD",
#       "town": "COVENTRY",
#       "postcode": "CV2 2DX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000018",
#       "name": "NHS Coventry and Warwickshire Integrated Care Board",
#       "ods_code": "QWU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJ224",
#     "name": "UNIVERSITY HOSPITAL LEWISHAM",
#     "website": "http://www.lewishamandgreenwich.nhs.uk",
#     "address1": "LEWISHAM HIGH STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.453022,
#     "longitude": -0.017927881,
#     "postcode": "SE13 6LH",
#     "geocode_coordinates": "SRID=27700;POINT (-0.017927881 51.453022)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ118"
#     },
#     "trust": {
#       "ods_code": "RJ2",
#       "name": "LEWISHAM AND GREENWICH NHS TRUST",
#       "address_line_1": "UNIVERSITY HOSPITAL LEWISHAM",
#       "address_line_2": "LEWISHAM HIGH STREET",
#       "town": "LONDON",
#       "postcode": "SE13 6LH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000030",
#       "name": "NHS South East London Integrated Care Board",
#       "ods_code": "QKK"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Lewisham",
#       "gss_code": "E09000023"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A4C1",
#     "name": "UNIVERSITY HOSPITAL LLANDOUGH",
#     "website": "",
#     "address1": "PENLAN ROAD",
#     "address2": "LLANDOUGH",
#     "address3": "",
#     "telephone": "",
#     "city": "PENARTH",
#     "county": "SOUTH GLAMORGAN",
#     "latitude": 51.448919571524335,
#     "longitude": -3.2018747900282367,
#     "postcode": "CF64 2XX",
#     "geocode_coordinates": "SRID=27700;POINT (-3.201874790028237 51.44891957152434)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A4",
#       "boundary_identifier": "W11000029",
#       "name": "Cardiff and Vale University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RVWAA",
#     "name": "UNIVERSITY HOSPITAL OF HARTLEPOOL",
#     "website": "http://www.nth.nhs.uk",
#     "address1": "HOLDFORTH ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HARTLEPOOL",
#     "county": "CLEVELAND",
#     "latitude": 54.70240021,
#     "longitude": -1.227821112,
#     "postcode": "TS24 9AH",
#     "geocode_coordinates": "SRID=27700;POINT (-1.227821112 54.70240021)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RVW",
#       "name": "NORTH TEES AND HARTLEPOOL NHS FOUNDATION TRUST",
#       "address_line_1": "UNIVERSITY HOSPITAL OF HARTLEPOOL",
#       "address_line_2": "HOLDFORTH ROAD",
#       "town": "HARTLEPOOL",
#       "postcode": "TS24 9AH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RXPCP",
#     "name": "UNIVERSITY HOSPITAL OF NORTH DURHAM",
#     "website": "http://www.cddft.nhs.uk/",
#     "address1": "NORTH ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "DURHAM",
#     "county": "COUNTY DURHAM",
#     "latitude": 54.78850174,
#     "longitude": -1.593818784,
#     "postcode": "DH1 5TW",
#     "geocode_coordinates": "SRID=27700;POINT (-1.593818784 54.78850174)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ162"
#     },
#     "trust": {
#       "ods_code": "RXP",
#       "name": "COUNTY DURHAM AND DARLINGTON NHS FOUNDATION TRUST",
#       "address_line_1": "DARLINGTON MEMORIAL HOSPITAL",
#       "address_line_2": "HOLLYHURST ROAD",
#       "town": "DARLINGTON",
#       "postcode": "DL3 6HX",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVWAE",
#     "name": "UNIVERSITY HOSPITAL OF NORTH TEES",
#     "website": "http://www.nth.nhs.uk",
#     "address1": "HARDWICK ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "STOCKTON-ON-TEES",
#     "county": "CLEVELAND",
#     "latitude": 54.58285904,
#     "longitude": -1.347565413,
#     "postcode": "TS19 8PE",
#     "geocode_coordinates": "SRID=27700;POINT (-1.347565413 54.58285904)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ163"
#     },
#     "trust": {
#       "ods_code": "RVW",
#       "name": "NORTH TEES AND HARTLEPOOL NHS FOUNDATION TRUST",
#       "address_line_1": "UNIVERSITY HOSPITAL OF HARTLEPOOL",
#       "address_line_2": "HOLDFORTH ROAD",
#       "town": "HARTLEPOOL",
#       "postcode": "TS24 9AH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWX85",
#     "name": "UPTON HOSPITAL",
#     "website": "https://www.berkshirehealthcare.nhs.uk/our-sites/slough/upton-hospital/",
#     "address1": "ALBERT STREET",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SLOUGH",
#     "county": "BERKSHIRE",
#     "latitude": 51.50535965,
#     "longitude": -0.593743086,
#     "postcode": "SL1 2BJ",
#     "geocode_coordinates": "SRID=27700;POINT (-0.593743086 51.50535965)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RWX",
#       "name": "BERKSHIRE HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "FITZWILLIAM HOUSE",
#       "address_line_2": "SKIMPED HILL LANE",
#       "town": "BRACKNELL",
#       "postcode": "RG12 1BQ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000044",
#       "name": "NHS Buckinghamshire, Oxfordshire and Berkshire West Integrated Care Board",
#       "ods_code": "QU9"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBL02",
#     "name": "VICTORIA CENTRAL HOSPITAL",
#     "website": "http://www.wuth.nhs.uk",
#     "address1": "MILL LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WALLASEY",
#     "county": "MERSEYSIDE",
#     "latitude": 53.41566086,
#     "longitude": -3.045850515,
#     "postcode": "CH44 5UF",
#     "geocode_coordinates": "SRID=27700;POINT (-3.045850515 53.41566086)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RBL",
#       "name": "WIRRAL UNIVERSITY TEACHING HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "ARROWE PARK HOSPITAL",
#       "address_line_2": "ARROWE PARK ROAD",
#       "town": "WIRRAL",
#       "postcode": "CH49 5PE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RM331",
#     "name": "WALKDEN GATEWAY",
#     "website": "",
#     "address1": "2 SMITH STREET",
#     "address2": "WORSLEY",
#     "address3": "",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.52506063219724,
#     "longitude": -2.397698469004914,
#     "postcode": "M28 3EZ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.397698469004914 53.52506063219724)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RM3",
#       "name": "NORTHERN CARE ALLIANCE NHS FOUNDATION TRUST",
#       "address_line_1": "SALFORD ROYAL",
#       "address_line_2": "STOTT LANE",
#       "town": "SALFORD",
#       "postcode": "M6 8HD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RTFED",
#     "name": "WANSBECK HOSPITAL",
#     "website": "https://www.northumbria.nhs.uk/wansbeck",
#     "address1": "WOODHORN LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ASHINGTON",
#     "county": "NORTHUMBERLAND",
#     "latitude": 55.18431091,
#     "longitude": -1.546586394,
#     "postcode": "NE63 9JJ",
#     "geocode_coordinates": "SRID=27700;POINT (-1.546586394 55.18431091)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RTF",
#       "name": "NORTHUMBRIA HEALTHCARE NHS FOUNDATION TRUST",
#       "address_line_1": "NORTH TYNESIDE GENERAL HOSPITAL",
#       "address_line_2": "RAKE LANE",
#       "town": "NORTH SHIELDS",
#       "postcode": "NE29 8NH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Paediatric Epilepsy Network for the North East and Cumbria",
#       "boundary_identifier": "PENNEC",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWWWH",
#     "name": "WARRINGTON HOSPITAL",
#     "website": "http://www.whh.nhs.uk",
#     "address1": "LOVELY LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WARRINGTON",
#     "county": "CHESHIRE",
#     "latitude": 53.39397812,
#     "longitude": -2.610702753,
#     "postcode": "WA5 1QG",
#     "geocode_coordinates": "SRID=27700;POINT (-2.610702753 53.39397812)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ049"
#     },
#     "trust": {
#       "ods_code": "RWW",
#       "name": "WARRINGTON AND HALTON TEACHING HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "WARRINGTON HOSPITAL",
#       "address_line_2": "LOVELY LANE",
#       "town": "WARRINGTON",
#       "postcode": "WA5 1QG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RJC02",
#     "name": "WARWICK HOSPITAL",
#     "website": "http://www.swft.nhs.uk",
#     "address1": "LAKIN ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WARWICK",
#     "county": "WARWICKSHIRE",
#     "latitude": 52.28995132,
#     "longitude": -1.583200693,
#     "postcode": "CV34 5BW",
#     "geocode_coordinates": "SRID=27700;POINT (-1.583200693 52.28995132)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ138"
#     },
#     "trust": {
#       "ods_code": "RJC",
#       "name": "SOUTH WARWICKSHIRE UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "WARWICK HOSPITAL",
#       "address_line_2": "LAKIN ROAD",
#       "town": "WARWICK",
#       "postcode": "CV34 5BW",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000018",
#       "name": "NHS Coventry and Warwickshire Integrated Care Board",
#       "ods_code": "QWU"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RWG02",
#     "name": "WATFORD GENERAL HOSPITAL",
#     "website": "https://www.westhertshospitals.nhs.uk",
#     "address1": "VICARAGE ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WATFORD",
#     "county": "HERTFORDSHIRE",
#     "latitude": 51.64859009,
#     "longitude": -0.405277938,
#     "postcode": "WD18 0HB",
#     "geocode_coordinates": "SRID=27700;POINT (-0.405277938 51.64859009)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ172"
#     },
#     "trust": {
#       "ods_code": "RWG",
#       "name": "WEST HERTFORDSHIRE TEACHING HOSPITALS NHS TRUST",
#       "address_line_1": "TRUST OFFICES",
#       "address_line_2": "WATFORD GENERAL HOSPITAL",
#       "town": "WATFORD",
#       "postcode": "WD18 0HB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000025",
#       "name": "NHS Hertfordshire and West Essex Integrated Care Board",
#       "ods_code": "QM7"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RNNBX",
#     "name": "WEST CUMBERLAND HOSPITAL",
#     "website": "",
#     "address1": "HOMEWOOD",
#     "address2": "HENSINGHAM",
#     "address3": "",
#     "telephone": "",
#     "city": "WHITEHAVEN",
#     "county": "CUMBRIA",
#     "latitude": 54.530056,
#     "longitude": -3.562582731,
#     "postcode": "CA28 8JG",
#     "geocode_coordinates": "SRID=27700;POINT (-3.562582731 54.530056)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ022"
#     },
#     "trust": {
#       "ods_code": "RNN",
#       "name": "NORTH CUMBRIA INTEGRATED CARE NHS FOUNDATION TRUST",
#       "address_line_1": "PILLARS BUILDING",
#       "address_line_2": "CUMBERLAND INFIRMARY",
#       "town": "CARLISLE",
#       "postcode": "CA2 7HY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1C03",
#     "name": "WESTERN COMMUNITY HOSPITAL",
#     "website": "https://www.southernhealth.nhs.uk/locations/western-community-hospital/",
#     "address1": "WILLIAM MACLEOD WAY",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SOUTHAMPTON",
#     "county": "HAMPSHIRE",
#     "latitude": 50.92525101,
#     "longitude": -1.446025729,
#     "postcode": "SO16 4XE",
#     "geocode_coordinates": "SRID=27700;POINT (-1.446025729 50.92525101)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "R1C",
#       "name": "SOLENT NHS TRUST",
#       "address_line_1": "SOLENT NHS TRUST HEADQUARTERS",
#       "address_line_2": "HIGHPOINT VENUE",
#       "town": "SOUTHAMPTON",
#       "postcode": "SO19 8BR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000042",
#       "name": "NHS Hampshire and Isle of Wight Integrated Care Board",
#       "ods_code": "QRL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RQM91",
#     "name": "WEST MIDDLESEX UNIVERSITY HOSPITAL",
#     "website": "http://www.chelwest.nhs.uk",
#     "address1": "TWICKENHAM ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "ISLEWORTH",
#     "county": "MIDDLESEX",
#     "latitude": 51.47364807,
#     "longitude": -0.324419945,
#     "postcode": "TW7 6AF",
#     "geocode_coordinates": "SRID=27700;POINT (-0.324419945 51.47364807)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ182"
#     },
#     "trust": {
#       "ods_code": "RQM",
#       "name": "CHELSEA AND WESTMINSTER HOSPITAL NHS FOUNDATION TRUST",
#       "address_line_1": "CHELSEA & WESTMINSTER HOSPITAL",
#       "address_line_2": "369 FULHAM ROAD",
#       "town": "LONDON",
#       "postcode": "SW10 9NH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000027",
#       "name": "NHS North West London Integrated Care Board",
#       "ods_code": "QRV"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVJJ8",
#     "name": "WESTON GENERAL HOSPITAL",
#     "website": "",
#     "address1": "GRANGE ROAD",
#     "address2": "UPHILL",
#     "address3": "",
#     "telephone": "",
#     "city": "WESTON-SUPER-MARE",
#     "county": "AVON",
#     "latitude": 51.32239856900821,
#     "longitude": -2.972724858256704,
#     "postcode": "BS23 4TQ",
#     "geocode_coordinates": "SRID=27700;POINT (-2.972724858256704 51.32239856900821)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RVJ",
#       "name": "NORTH BRISTOL NHS TRUST",
#       "address_line_1": "SOUTHMEAD HOSPITAL",
#       "address_line_2": "SOUTHMEAD ROAD",
#       "town": "BRISTOL",
#       "postcode": "BS10 5NB",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000039",
#       "name": "NHS Bristol, North Somerset and South Gloucestershire Integrated Care Board",
#       "ods_code": "QUY"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RGR50",
#     "name": "WEST SUFFOLK HOSPITAL",
#     "website": "http://www.wsh.nhs.uk",
#     "address1": "HARDWICK LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BURY ST. EDMUNDS",
#     "county": "SUFFOLK",
#     "latitude": 52.23166275,
#     "longitude": 0.70919019,
#     "postcode": "IP33 2QZ",
#     "geocode_coordinates": "SRID=27700;POINT (0.7091901900000001 52.23166275)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ072"
#     },
#     "trust": {
#       "ods_code": "RGR",
#       "name": "WEST SUFFOLK NHS FOUNDATION TRUST",
#       "address_line_1": "WEST SUFFOLK HOSPITAL",
#       "address_line_2": "HARDWICK LANE",
#       "town": "BURY ST. EDMUNDS",
#       "postcode": "IP33 2QZ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000023",
#       "name": "NHS Suffolk and North East Essex Integrated Care Board",
#       "ods_code": "QJG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y61",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000007",
#       "name": "East of England"
#     },
#     "openuk_network": {
#       "name": "Eastern Paediatric Epilepsy Network",
#       "boundary_identifier": "EPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RDU50",
#     "name": "WEXHAM PARK HOSPITAL",
#     "website": "https://www.fhft.nhs.uk/",
#     "address1": "WEXHAM",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "SLOUGH",
#     "county": "BERKSHIRE",
#     "latitude": 51.53200912,
#     "longitude": -0.573977947,
#     "postcode": "SL2 4HL",
#     "geocode_coordinates": "SRID=27700;POINT (-0.573977947 51.53200912)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ021"
#     },
#     "trust": {
#       "ods_code": "RDU",
#       "name": "FRIMLEY HEALTH NHS FOUNDATION TRUST",
#       "address_line_1": "PORTSMOUTH ROAD",
#       "address_line_2": "FRIMLEY",
#       "town": "CAMBERLEY",
#       "postcode": "GU16 7UJ",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000034",
#       "name": "NHS Frimley Integrated Care Board",
#       "ods_code": "QNQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South West Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SWTPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R1HKH",
#     "name": "WHIPPS CROSS UNIVERSITY HOSPITAL",
#     "website": "http://www.bartshealth.nhs.uk/",
#     "address1": "WHIPPS CROSS ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "LONDON",
#     "county": "GREATER LONDON",
#     "latitude": 51.57883072,
#     "longitude": 0.002652787,
#     "postcode": "E11 1NR",
#     "geocode_coordinates": "SRID=27700;POINT (0.002652787 51.57883072)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ036"
#     },
#     "trust": {
#       "ods_code": "R1H",
#       "name": "BARTS HEALTH NHS TRUST",
#       "address_line_1": "THE ROYAL LONDON HOSPITAL",
#       "address_line_2": "80 NEWARK STREET",
#       "town": "LONDON",
#       "postcode": "E1 2ES",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000029",
#       "name": "NHS North East London Integrated Care Board",
#       "ods_code": "QMF"
#     },
#     "nhs_england_region": {
#       "region_code": "Y56",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000003",
#       "name": "London"
#     },
#     "openuk_network": {
#       "name": "North Thames Paediatric Epilepsy Network",
#       "boundary_identifier": "NTPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": {
#       "name": "Waltham Forest",
#       "gss_code": "E09000031"
#     },
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RBN01",
#     "name": "WHISTON HOSPITAL",
#     "website": "http://www.sthk.nhs.uk",
#     "address1": "WARRINGTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "PRESCOT",
#     "county": "MERSEYSIDE",
#     "latitude": 53.42047501,
#     "longitude": -2.784939051,
#     "postcode": "L35 5DR",
#     "geocode_coordinates": "SRID=27700;POINT (-2.784939051 53.42047501)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ153"
#     },
#     "trust": {
#       "ods_code": "RBN",
#       "name": "ST HELENS AND KNOWSLEY TEACHING HOSPITALS NHS TRUST",
#       "address_line_1": "WHISTON HOSPITAL",
#       "address_line_2": "WARRINGTON ROAD",
#       "town": "PRESCOT",
#       "postcode": "L35 5DR",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000008",
#       "name": "NHS Cheshire and Merseyside Integrated Care Board",
#       "ods_code": "QYG"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RVV01",
#     "name": "WILLIAM HARVEY HOSPITAL (ASHFORD)",
#     "website": "http://www.ekhuft.nhs.uk/williamharvey",
#     "address1": "KENNINGTON ROAD",
#     "address2": "WILLESBOROUGH",
#     "address3": "",
#     "telephone": "",
#     "city": "ASHFORD",
#     "county": "KENT",
#     "latitude": 51.14148712,
#     "longitude": 0.916223049,
#     "postcode": "TN24 0LZ",
#     "geocode_coordinates": "SRID=27700;POINT (0.916223049 51.14148712)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ024"
#     },
#     "trust": {
#       "ods_code": "RVV",
#       "name": "EAST KENT HOSPITALS UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "KENT & CANTERBURY HOSPITAL",
#       "address_line_2": "ETHELBERT ROAD",
#       "town": "CANTERBURY",
#       "postcode": "CT1 3NG",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000032",
#       "name": "NHS Kent and Medway Integrated Care Board",
#       "ods_code": "QKS"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "South East Thames Paediatric Epilepsy Group",
#       "boundary_identifier": "SETPEG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RM311",
#     "name": "WITHINGTON COMMUNITY HOSPITAL",
#     "website": "",
#     "address1": "WITHINGTON COMMUNITY HOSPITAL",
#     "address2": "NELL LANE",
#     "address3": "",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.42582006024377,
#     "longitude": -2.2442890475733615,
#     "postcode": "M20 2LR",
#     "geocode_coordinates": "SRID=27700;POINT (-2.244289047573361 53.42582006024377)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RM3",
#       "name": "NORTHERN CARE ALLIANCE NHS FOUNDATION TRUST",
#       "address_line_1": "SALFORD ROYAL",
#       "address_line_2": "STOTT LANE",
#       "town": "SALFORD",
#       "postcode": "M6 8HD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A2BL",
#     "name": "WITHYBUSH GENERAL HOSPITAL",
#     "website": "",
#     "address1": "FISHGUARD ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HAVERFORDWEST",
#     "county": "DYFED",
#     "latitude": 51.81279926221023,
#     "longitude": -4.964727234183426,
#     "postcode": "SA61 2PZ",
#     "geocode_coordinates": "SRID=27700;POINT (-4.964727234183426 51.81279926221023)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A2",
#       "boundary_identifier": "W11000025",
#       "name": "Hywel Dda University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RWP50",
#     "name": "WORCESTERSHIRE ROYAL HOSPITAL",
#     "website": "http://www.worcsacute.nhs.uk/our-hospitals/worcestershire-royal-hospital/",
#     "address1": "CHARLES HASTINGS WAY",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WORCESTER",
#     "county": "WORCESTERSHIRE",
#     "latitude": 52.19151688,
#     "longitude": -2.179341078,
#     "postcode": "WR5 1DD",
#     "geocode_coordinates": "SRID=27700;POINT (-2.179341078 52.19151688)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ225"
#     },
#     "trust": {
#       "ods_code": "RWP",
#       "name": "WORCESTERSHIRE ACUTE HOSPITALS NHS TRUST",
#       "address_line_1": "WORCESTERSHIRE ROYAL HOSPITAL",
#       "address_line_2": "CHARLES HASTINGS WAY",
#       "town": "WORCESTER",
#       "postcode": "WR5 1DD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000019",
#       "name": "NHS Herefordshire and Worcestershire Integrated Care Board",
#       "ods_code": "QGH"
#     },
#     "nhs_england_region": {
#       "region_code": "Y60",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000011",
#       "name": "Midlands"
#     },
#     "openuk_network": {
#       "name": "Birmingham Regional Paediatric Neurology Forum",
#       "boundary_identifier": "BRPNF",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RNN42",
#     "name": "WORKINGTON COMMUNITY HOSPITAL",
#     "website": "",
#     "address1": "PARK LANE",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WORKINGTON",
#     "county": "CUMBRIA",
#     "latitude": 54.642892871753546,
#     "longitude": -3.5507700187869427,
#     "postcode": "CA14 2RW",
#     "geocode_coordinates": "SRID=27700;POINT (-3.550770018786943 54.64289287175355)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RNN",
#       "name": "NORTH CUMBRIA INTEGRATED CARE NHS FOUNDATION TRUST",
#       "address_line_1": "PILLARS BUILDING",
#       "address_line_2": "CUMBERLAND INFIRMARY",
#       "town": "CARLISLE",
#       "postcode": "CA2 7HY",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000050",
#       "name": "NHS North East and North Cumbria Integrated Care Board",
#       "ods_code": "QHM"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RYR18",
#     "name": "WORTHING HOSPITAL",
#     "website": "https://www.uhsussex.nhs.uk/",
#     "address1": "LYNDHURST ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "WORTHING",
#     "county": "WEST SUSSEX",
#     "latitude": 50.81669235,
#     "longitude": -0.363415062,
#     "postcode": "BN11 2DH",
#     "geocode_coordinates": "SRID=27700;POINT (-0.363415062 50.81669235)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ018"
#     },
#     "trust": {
#       "ods_code": "RYR",
#       "name": "UNIVERSITY HOSPITALS SUSSEX NHS FOUNDATION TRUST",
#       "address_line_1": "WORTHING HOSPITAL",
#       "address_line_2": "LYNDHURST ROAD",
#       "town": "WORTHING",
#       "postcode": "BN11 2DH",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000064",
#       "name": "NHS Sussex Integrated Care Board",
#       "ods_code": "QNX"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Wessex Paediatric Neurosciences Network",
#       "boundary_identifier": "WPNN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RY661",
#     "name": "WORTLEY BECK HEALTH CENTRE",
#     "website": "",
#     "address1": "RING ROAD",
#     "address2": "LOWER WORTLEY",
#     "address3": "",
#     "telephone": "",
#     "city": "LEEDS",
#     "county": "WEST YORKSHIRE",
#     "latitude": 53.78266025523274,
#     "longitude": -1.6002387438514194,
#     "postcode": "LS12 5SG",
#     "geocode_coordinates": "SRID=27700;POINT (-1.600238743851419 53.78266025523274)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RY6",
#       "name": "LEEDS COMMUNITY HEALTHCARE NHS TRUST",
#       "address_line_1": "STOCKDALE HOUSE",
#       "address_line_2": "8 VICTORIA ROAD",
#       "town": "LEEDS",
#       "postcode": "LS6 1PF",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000054",
#       "name": "NHS West Yorkshire Integrated Care Board",
#       "ods_code": "QWO"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A1A4",
#     "name": "WREXHAM MAELOR HOSPITAL",
#     "website": "",
#     "address1": "CROESNEWYDD ROAD",
#     "address2": "WREXHAM TECHNOLOGY PARK",
#     "address3": "",
#     "telephone": "",
#     "city": "WREXHAM",
#     "county": "CLWYD",
#     "latitude": 53.047169693895974,
#     "longitude": -3.008734102325263,
#     "postcode": "LL13 7TD",
#     "geocode_coordinates": "SRID=27700;POINT (-3.008734102325263 53.04716969389597)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A1",
#       "boundary_identifier": "W11000023",
#       "name": "Betsi Cadwaladr University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "RXQ50",
#     "name": "WYCOMBE HOSPITAL",
#     "website": "http://www.buckshealthcare.nhs.uk",
#     "address1": "QUEEN ALEXANDRA ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "HIGH WYCOMBE",
#     "county": "BUCKINGHAMSHIRE",
#     "latitude": 51.62644196,
#     "longitude": -0.753413498,
#     "postcode": "HP11 2TT",
#     "geocode_coordinates": "SRID=27700;POINT (-0.753413498 51.62644196)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ038"
#     },
#     "trust": {
#       "ods_code": "RXQ",
#       "name": "BUCKINGHAMSHIRE HEALTHCARE NHS TRUST",
#       "address_line_1": "AMERSHAM HOSPITAL",
#       "address_line_2": "WHIELDEN STREET",
#       "town": "AMERSHAM",
#       "postcode": "HP7 0JD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000044",
#       "name": "NHS Buckinghamshire, Oxfordshire and Berkshire West Integrated Care Board",
#       "ods_code": "QU9"
#     },
#     "nhs_england_region": {
#       "region_code": "Y59",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000005",
#       "name": "South East"
#     },
#     "openuk_network": {
#       "name": "Oxford region epilepsy interest group",
#       "boundary_identifier": "ORENG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "R0A07",
#     "name": "WYTHENSHAWE HOSPITAL",
#     "website": "",
#     "address1": "SOUTHMOOR ROAD",
#     "address2": "WYTHENSHAWE",
#     "address3": "",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.38792,
#     "longitude": -2.29319,
#     "postcode": "M23 9LT",
#     "geocode_coordinates": "SRID=27700;POINT (-2.29319 53.38792)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ136"
#     },
#     "trust": {
#       "ods_code": "R0A",
#       "name": "MANCHESTER UNIVERSITY NHS FOUNDATION TRUST",
#       "address_line_1": "COBBETT HOUSE",
#       "address_line_2": "OXFORD ROAD",
#       "town": "MANCHESTER",
#       "postcode": "M13 9WL",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RM325",
#     "name": "WYTHENSHAWE HOSPITAL",
#     "website": "",
#     "address1": "SOUTHMOOR ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "MANCHESTER",
#     "county": "GREATER MANCHESTER",
#     "latitude": 53.38911906358711,
#     "longitude": -2.2919031193396626,
#     "postcode": "M23 9LT",
#     "geocode_coordinates": "SRID=27700;POINT (-2.291903119339663 53.38911906358711)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": {
#       "ods_code": "RM3",
#       "name": "NORTHERN CARE ALLIANCE NHS FOUNDATION TRUST",
#       "address_line_1": "SALFORD ROYAL",
#       "address_line_2": "STOTT LANE",
#       "town": "SALFORD",
#       "postcode": "M6 8HD",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000057",
#       "name": "NHS Greater Manchester Integrated Care Board",
#       "ods_code": "QOP"
#     },
#     "nhs_england_region": {
#       "region_code": "Y62",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000010",
#       "name": "North West"
#     },
#     "openuk_network": {
#       "name": "North West Children and Young People's Epilepsy Interest Group",
#       "boundary_identifier": "NWEIG",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RA430",
#     "name": "YEOVIL DISTRICT HOSPITAL",
#     "website": "http://www.yeovilhospital.nhs.uk/",
#     "address1": "HIGHER KINGSTON",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "YEOVIL",
#     "county": "SOMERSET",
#     "latitude": 50.94484711,
#     "longitude": -2.634698391,
#     "postcode": "BA21 4AT",
#     "geocode_coordinates": "SRID=27700;POINT (-2.634698391 50.94484711)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ173"
#     },
#     "trust": {
#       "ods_code": "RH5",
#       "name": "SOMERSET NHS FOUNDATION TRUST",
#       "address_line_1": "TRUST MANAGEMENT",
#       "address_line_2": "LYDEARD HOUSE",
#       "town": "TAUNTON",
#       "postcode": "TA1 5DA",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000038",
#       "name": "NHS Somerset Integrated Care Board",
#       "ods_code": "QSL"
#     },
#     "nhs_england_region": {
#       "region_code": "Y58",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000006",
#       "name": "South West"
#     },
#     "openuk_network": {
#       "name": "South West Interest Group Paediatric Epilepsy",
#       "boundary_identifier": "SWIPE",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "RCB55",
#     "name": "YORK HOSPITAL",
#     "website": "http://www.york.nhs.uk",
#     "address1": "WIGGINTON ROAD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "YORK",
#     "county": "NORTH YORKSHIRE",
#     "latitude": 53.96895218,
#     "longitude": -1.084269643,
#     "postcode": "YO31 8HE",
#     "geocode_coordinates": "SRID=27700;POINT (-1.084269643 53.96895218)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": {
#       "pz_code": "PZ114"
#     },
#     "trust": {
#       "ods_code": "RCB",
#       "name": "YORK AND SCARBOROUGH TEACHING HOSPITALS NHS FOUNDATION TRUST",
#       "address_line_1": "YORK HOSPITAL",
#       "address_line_2": "WIGGINTON ROAD",
#       "town": "YORK",
#       "postcode": "YO31 8HE",
#       "country": "ENGLAND",
#       "telephone": null,
#       "website": null,
#       "active": true,
#       "published_at": null
#     },
#     "local_health_board": null,
#     "integrated_care_board": {
#       "boundary_identifier": "E54000051",
#       "name": "NHS Humber and North Yorkshire Integrated Care Board",
#       "ods_code": "QOQ"
#     },
#     "nhs_england_region": {
#       "region_code": "Y63",
#       "publication_date": "2022-07-30",
#       "boundary_identifier": "E40000012",
#       "name": "North East and Yorkshire"
#     },
#     "openuk_network": {
#       "name": "Yorkshire Paediatric Neurology Network",
#       "boundary_identifier": "YPEN",
#       "country": "England",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "E92000001",
#       "name": "England"
#     }
#   },
#   {
#     "ods_code": "7A1A1",
#     "name": "YSBYTY GLAN CLWYD",
#     "website": "",
#     "address1": "GLAN CLWYD HOSPITAL",
#     "address2": "RHUDDLAN ROAD",
#     "address3": "BODELWYDDAN",
#     "telephone": "",
#     "city": "RHYL",
#     "county": "CLWYD",
#     "latitude": 53.271949025221794,
#     "longitude": -3.496429715048846,
#     "postcode": "LL18 5UJ",
#     "geocode_coordinates": "SRID=27700;POINT (-3.496429715048846 53.27194902522179)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A1",
#       "boundary_identifier": "W11000023",
#       "name": "Betsi Cadwaladr University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "7A1AU",
#     "name": "YSBYTY GWYNEDD",
#     "website": "",
#     "address1": "PENRHOSGARNEDD",
#     "address2": "",
#     "address3": "",
#     "telephone": "",
#     "city": "BANGOR",
#     "county": "GWYNEDD",
#     "latitude": 53.20922110492283,
#     "longitude": -4.159410640189676,
#     "postcode": "LL57 2PW",
#     "geocode_coordinates": "SRID=27700;POINT (-4.159410640189676 53.20922110492283)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A1",
#       "boundary_identifier": "W11000023",
#       "name": "Betsi Cadwaladr University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "Mersey and North Wales network 'Epilepsy In Childhood' interest group",
#       "boundary_identifier": "EPIC",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   },
#   {
#     "ods_code": "7A6AV",
#     "name": "YSBYTY YSTRAD FAWR",
#     "website": "",
#     "address1": "YSTRAD FAWR WAY",
#     "address2": "YSTRAD MYNACH",
#     "address3": "",
#     "telephone": "",
#     "city": "HENGOED",
#     "county": "MID GLAMORGAN",
#     "latitude": 51.63419223712743,
#     "longitude": -3.233903238440721,
#     "postcode": "CF82 7EP",
#     "geocode_coordinates": "SRID=27700;POINT (-3.233903238440721 51.63419223712743)",
#     "active": true,
#     "published_at": null,
#     "paediatric_diabetes_unit": null,
#     "trust": null,
#     "local_health_board": {
#       "ods_code": "7A6",
#       "boundary_identifier": "W11000028",
#       "name": "Aneurin Bevan University Health Board"
#     },
#     "integrated_care_board": null,
#     "nhs_england_region": null,
#     "openuk_network": {
#       "name": "South Wales Epilepsy Forum",
#       "boundary_identifier": "SWEP",
#       "country": "Wales",
#       "publication_date": "2022-12-08"
#     },
#     "london_borough": null,
#     "country": {
#       "boundary_identifier": "W92000004",
#       "name": "Wales"
#     }
#   }
# ]
