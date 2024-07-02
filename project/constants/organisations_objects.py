from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class PaediatricDiabetesUnit:
    pz_code: str


@dataclass
class Trust:
    ods_code: str
    name: str
    address_line_1: str
    address_line_2: str
    town: str
    postcode: str
    country: str
    telephone: Optional[str]
    website: Optional[str]
    active: bool
    published_at: Optional[str]


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


@dataclass
class OrganisationRCPCH:
    ods_code: str
    name: str
    website: Optional[str]
    address1: str
    address2: Optional[str]
    address3: Optional[str]
    telephone: Optional[str]
    city: str
    county: str
    latitude: float
    longitude: float
    postcode: str
    geocode_coordinates: str
    active: bool
    published_at: Optional[str]
    paediatric_diabetes_unit: PaediatricDiabetesUnit
    trust: Trust
    local_health_board: Optional[str]
    integrated_care_board: IntegratedCareBoard
    nhs_england_region: NHSEnglandRegion
    openuk_network: OpenUKNetwork
    london_borough: Optional[str]
    country: Country

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "OrganisationRCPCH":
        return cls(
            ods_code=data["ods_code"],
            name=data["name"],
            website=data.get("website"),
            address1=data["address1"],
            address2=data.get("address2"),
            address3=data.get("address3"),
            telephone=data.get("telephone"),
            city=data["city"],
            county=data["county"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            postcode=data["postcode"],
            geocode_coordinates=data["geocode_coordinates"],
            active=data["active"],
            published_at=data.get("published_at"),
            paediatric_diabetes_unit=PaediatricDiabetesUnit(
                pz_code=data["paediatric_diabetes_unit"]["pz_code"]
            ),
            trust=Trust(
                ods_code=data["trust"]["ods_code"],
                name=data["trust"]["name"],
                address_line_1=data["trust"]["address_line_1"],
                address_line_2=data["trust"]["address_line_2"],
                town=data["trust"]["town"],
                postcode=data["trust"]["postcode"],
                country=data["trust"]["country"],
                telephone=data["trust"].get("telephone"),
                website=data["trust"].get("website"),
                active=data["trust"]["active"],
                published_at=data["trust"].get("published_at"),
            ),
            local_health_board=data.get("local_health_board"),
            integrated_care_board=IntegratedCareBoard(
                boundary_identifier=data["integrated_care_board"][
                    "boundary_identifier"
                ],
                name=data["integrated_care_board"]["name"],
                ods_code=data["integrated_care_board"]["ods_code"],
            ),
            nhs_england_region=NHSEnglandRegion(
                region_code=data["nhs_england_region"]["region_code"],
                publication_date=data["nhs_england_region"]["publication_date"],
                boundary_identifier=data["nhs_england_region"]["boundary_identifier"],
                name=data["nhs_england_region"]["name"],
            ),
            openuk_network=OpenUKNetwork(
                name=data["openuk_network"]["name"],
                boundary_identifier=data["openuk_network"]["boundary_identifier"],
                country=data["openuk_network"]["country"],
                publication_date=data["openuk_network"]["publication_date"],
            ),
            london_borough=data.get("london_borough"),
            country=Country(
                boundary_identifier=data["country"]["boundary_identifier"],
                name=data["country"]["name"],
            ),
        )
