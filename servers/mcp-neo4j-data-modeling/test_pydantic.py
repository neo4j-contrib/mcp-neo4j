from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, Field


class Patient(BaseModel):
    id: str
    first: str = Field(..., description="Patient's first name")
    last: str = Field(..., description="Patient's last name")
    birthdate: datetime = Field(..., description="Patient's date of birth")
    gender: str = Field(..., description="Patient's gender identity")
    address: str = Field(..., description="Patient's street address")
    city: str = Field(..., description="City where patient resides")
    state: str = Field(..., description="State/province where patient resides")
    county: str = Field(..., description="County where patient resides")
    location: tuple[float, float] = Field(
        ..., description="Geographic coordinates of patient's location"
    )
    latitude: float = Field(
        ..., description="Latitude coordinate of patient's location"
    )
    longitude: float = Field(
        ..., description="Longitude coordinate of patient's location"
    )
    ethnicity: str = Field(..., description="Patient's ethnic background")
    race: str = Field(..., description="Patient's racial background")
    martial: str = Field(..., description="Patient's marital status")
    prefix: str = Field(..., description="Patient's name prefix (e.g., Dr., Mr., Ms.)")
    birthplace: str = Field(..., description="City/country where patient was born")
    deathdate: datetime = Field(..., description="Date of patient's death if deceased")
    drivers: str = Field(..., description="Patient's driver's license number")
    healthcare_coverage: float = Field(
        ..., description="Amount of healthcare coverage in currency"
    )
    healthcare_expenses: float = Field(
        ..., description="Total healthcare expenses incurred"
    )


class Encounter(BaseModel):
    id: str
    code: str = Field(..., description="Encounter code or identifier")
    description: str = Field(
        ..., description="Encounter description or reason for visit"
    )
    class_: str = Field(
        ...,
        description="Encounter class (emergency, outpatient, inpatient, etc.)",
        alias="class",
    )
    start: str = Field(..., description="Encounter start date and time")
    end: str = Field(..., description="Encounter end date and time")
    isStart: bool = Field(..., description="Whether this is the start of the encounter")
    isEnd: bool = Field(..., description="Whether this is the end of the encounter")
    baseCost: float = Field(..., description="Base cost of the encounter")
    claimCost: float = Field(..., description="Claim cost for the encounter")
    coveredAmount: float = Field(..., description="Amount covered by insurance")


class Provider(BaseModel):
    id: str
    name: str = Field(..., description="Provider's full name")
    address: str = Field(..., description="Provider's practice address")
    location: tuple[float, float] = Field(
        ..., description="Geographic coordinates of provider's practice location"
    )


class Organization(BaseModel):
    id: str
    name: str = Field(..., description="Healthcare organization name")
    address: str = Field(..., description="Organization's address")
    city: str = Field(..., description="City where organization is located")
    location: tuple[float, float] = Field(
        ..., description="Geographic coordinates of organization location"
    )


class Condition(BaseModel):
    code: str
    description: str = Field(..., description="Medical condition description")
    start: str = Field(..., description="Date when condition was diagnosed")
    stop: str = Field(..., description="Date when condition was resolved (Optional)")
    isEnd: bool = Field(..., description="Indicates if condition is resolved")
    total_drug_pairings: int = Field(
        ..., description="Number of drug combinations prescribed for this condition"
    )


class Drug(BaseModel):
    code: str
    description: str = Field(..., description="Drug description")
    start: str = Field(..., description="Date when drug was prescribed")
    stop: str = Field(
        ...,
        description="Date when drug prescription ended (Optional), Conditional on isEnd property",
    )
    isEnd: bool = Field(
        ..., description="Indicates if drug prescription is discontinued"
    )
    basecost: str = Field(..., description="Base cost of the drug before insurance")
    totalcost: str = Field(
        ..., description="Total cost of the drug including insurance"
    )


class Procedure(BaseModel):
    code: str
    description: str = Field(..., description="Medical procedure description")


class Observation(BaseModel):
    code: str
    description: str = Field(..., description="Observation description")
    category: str = Field(..., description="Category of observation")
    type: str = Field(..., description="Type of observation measurement")


class Device(BaseModel):
    code: str
    description: str = Field(..., description="Medical device description")


class CarePlan(BaseModel):
    id: str
    code: str = Field(..., description="Care plan code or identifier")
    description: str = Field(..., description="Care plan description")
    start: str = Field(..., description="Date when care plan was initiated")
    end: str = Field(
        ...,
        description="Date when care plan was completed (Optional) and conditional on isEnd property",
    )
    isEnd: bool = Field(..., description="Indicates if care plan is completed")
    reasoncode: str = Field(..., description="Reason code for care plan creation")


class Allergy(BaseModel):
    code: str
    description: str = Field(..., description="Allergy description and symptoms")
    category: str = Field(..., description="Category of allergy")
    system: str = Field(..., description="Body system affected by the allergy")
    type: str = Field(..., description="Type of allergic reaction")


class Reaction(BaseModel):
    id: str
    description: str = Field(
        ..., description="Description of allergic reaction symptoms"
    )


class Payer(BaseModel):
    id: str
    name: str = Field(..., description="Insurance payer name")


class Speciality(BaseModel):
    name: str


class HasEncounter(BaseModel):
    start_node_Patient_id: str
    end_node_Encounter_id: str

    start_node_label: ClassVar[str] = "Patient"
    end_node_label: ClassVar[str] = "Encounter"
    pattern: ClassVar[str] = "(:Patient)-[:HAS_ENCOUNTER]->(:Encounter)"


class First(BaseModel):
    start_node_Patient_id: str
    end_node_Encounter_id: str

    start_node_label: ClassVar[str] = "Patient"
    end_node_label: ClassVar[str] = "Encounter"
    pattern: ClassVar[str] = "(:Patient)-[:FIRST]->(:Encounter)"


class Last(BaseModel):
    start_node_Patient_id: str
    end_node_Encounter_id: str

    start_node_label: ClassVar[str] = "Patient"
    end_node_label: ClassVar[str] = "Encounter"
    pattern: ClassVar[str] = "(:Patient)-[:LAST]->(:Encounter)"


class Next(BaseModel):
    start_node_Encounter_id: str
    end_node_Encounter_id: str
    amount: int

    start_node_label: ClassVar[str] = "Encounter"
    end_node_label: ClassVar[str] = "Encounter"
    pattern: ClassVar[str] = "(:Encounter)-[:NEXT]->(:Encounter)"


class HasProvider(BaseModel):
    start_node_Encounter_id: str
    end_node_Provider_id: str

    start_node_label: ClassVar[str] = "Encounter"
    end_node_label: ClassVar[str] = "Provider"
    pattern: ClassVar[str] = "(:Encounter)-[:HAS_PROVIDER]->(:Provider)"


class AtOrganization(BaseModel):
    start_node_Encounter_id: str
    end_node_Organization_id: str

    start_node_label: ClassVar[str] = "Encounter"
    end_node_label: ClassVar[str] = "Organization"
    pattern: ClassVar[str] = "(:Encounter)-[:AT_ORGANIZATION]->(:Organization)"


class BelongsTo(BaseModel):
    start_node_Provider_id: str
    end_node_Organization_id: str

    start_node_label: ClassVar[str] = "Provider"
    end_node_label: ClassVar[str] = "Organization"
    pattern: ClassVar[str] = "(:Provider)-[:BELONGS_TO]->(:Organization)"


class HasSpeciality(BaseModel):
    start_node_Provider_id: str
    end_node_Speciality_name: str

    start_node_label: ClassVar[str] = "Provider"
    end_node_label: ClassVar[str] = "Speciality"
    pattern: ClassVar[str] = "(:Provider)-[:HAS_SPECIALITY]->(:Speciality)"


class HasCondition(BaseModel):
    start_node_Encounter_id: str
    end_node_Condition_code: str

    start_node_label: ClassVar[str] = "Encounter"
    end_node_label: ClassVar[str] = "Condition"
    pattern: ClassVar[str] = "(:Encounter)-[:HAS_CONDITION]->(:Condition)"


class HasDrug(BaseModel):
    start_node_Encounter_id: str
    end_node_Drug_code: str

    start_node_label: ClassVar[str] = "Encounter"
    end_node_label: ClassVar[str] = "Drug"
    pattern: ClassVar[str] = "(:Encounter)-[:HAS_DRUG]->(:Drug)"


class HasProcedure(BaseModel):
    start_node_Encounter_id: str
    end_node_Procedure_code: str

    start_node_label: ClassVar[str] = "Encounter"
    end_node_label: ClassVar[str] = "Procedure"
    pattern: ClassVar[str] = "(:Encounter)-[:HAS_PROCEDURE]->(:Procedure)"


class HasObservation(BaseModel):
    start_node_Encounter_id: str
    end_node_Observation_code: str
    date: str = Field(..., description="Date when observation was recorded")
    value: str = Field(..., description="Observation value or result")
    unit: str = Field(..., description="Unit of measurement for the observation")

    start_node_label: ClassVar[str] = "Encounter"
    end_node_label: ClassVar[str] = "Observation"
    pattern: ClassVar[str] = "(:Encounter)-[:HAS_OBSERVATION]->(:Observation)"


class DeviceUsed(BaseModel):
    start_node_Encounter_id: str
    end_node_Device_code: str

    start_node_label: ClassVar[str] = "Encounter"
    end_node_label: ClassVar[str] = "Device"
    pattern: ClassVar[str] = "(:Encounter)-[:DEVICE_USED]->(:Device)"


class HasCarePlan(BaseModel):
    start_node_Encounter_id: str
    end_node_CarePlan_id: str

    start_node_label: ClassVar[str] = "Encounter"
    end_node_label: ClassVar[str] = "CarePlan"
    pattern: ClassVar[str] = "(:Encounter)-[:HAS_CARE_PLAN]->(:CarePlan)"


class HasAllergy(BaseModel):
    start_node_Patient_id: str
    end_node_Allergy_code: str

    start_node_label: ClassVar[str] = "Patient"
    end_node_label: ClassVar[str] = "Allergy"
    pattern: ClassVar[str] = "(:Patient)-[:HAS_ALLERGY]->(:Allergy)"


class AllergyDetected(BaseModel):
    start_node_Encounter_id: str
    end_node_Allergy_code: str
    start: str = Field(
        ..., description="Date when allergy was detected during encounter"
    )

    start_node_label: ClassVar[str] = "Encounter"
    end_node_label: ClassVar[str] = "Allergy"
    pattern: ClassVar[str] = "(:Encounter)-[:ALLERGY_DETECTED]->(:Allergy)"


class CausesReaction(BaseModel):
    start_node_Allergy_code: str
    end_node_Reaction_id: str

    start_node_label: ClassVar[str] = "Allergy"
    end_node_label: ClassVar[str] = "Reaction"
    pattern: ClassVar[str] = "(:Allergy)-[:CAUSES_REACTION]->(:Reaction)"


class HasReaction(BaseModel):
    start_node_Patient_id: str
    end_node_Reaction_id: str
    severity: str = Field(..., description="Severity level of the allergic reaction")

    start_node_label: ClassVar[str] = "Patient"
    end_node_label: ClassVar[str] = "Reaction"
    pattern: ClassVar[str] = "(:Patient)-[:HAS_REACTION]->(:Reaction)"


class HasPayer(BaseModel):
    start_node_Encounter_id: str
    end_node_Payer_id: str

    start_node_label: ClassVar[str] = "Encounter"
    end_node_label: ClassVar[str] = "Payer"
    pattern: ClassVar[str] = "(:Encounter)-[:HAS_PAYER]->(:Payer)"


class InsuranceStart(BaseModel):
    start_node_Patient_id: str
    end_node_Payer_id: str

    start_node_label: ClassVar[str] = "Patient"
    end_node_label: ClassVar[str] = "Payer"
    pattern: ClassVar[str] = "(:Patient)-[:INSURANCE_START]->(:Payer)"


class InsuranceEnd(BaseModel):
    start_node_Patient_id: str
    end_node_Payer_id: str

    start_node_label: ClassVar[str] = "Patient"
    end_node_label: ClassVar[str] = "Payer"
    pattern: ClassVar[str] = "(:Patient)-[:INSURANCE_END]->(:Payer)"
