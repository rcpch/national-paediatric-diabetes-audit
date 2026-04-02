from dataclasses import dataclass

# @dataclass
# class PaediatricDiabetesUnit:
#     pz_code: str


@dataclass
class Trust:
    ods_code: str
    name: str
    address_line_1: str
    address_line_2: str
    town: str
    postcode: str
    country: str
    telephone: str | None
    website: str | None
    active: bool
    published_at: str | None


@dataclass
class IntegratedCareBoard:
    boundary_identifier: str
    name: str
    ods_code: str


@dataclass
class NHSEnglandRegion:
    region_code: str
    publication_date: str
    boundary_identifier: str
    name: str


@dataclass
class OpenUKNetwork:
    name: str
    boundary_identifier: str
    country: str
    publication_date: str


@dataclass
class Country:
    boundary_identifier: str
    name: str
