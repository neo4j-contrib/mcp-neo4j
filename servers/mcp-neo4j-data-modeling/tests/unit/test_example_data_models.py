"""
Test that the example data models adhere to the DataModel structure.
"""

from mcp_neo4j_data_modeling.data_model import DataModel
from mcp_neo4j_data_modeling.static import (
    CUSTOMER_360_MODEL,
    FRAUD_AML_MODEL,
    HEALTH_INSURANCE_FRAUD_MODEL,
    OIL_GAS_MONITORING_MODEL,
    PATIENT_JOURNEY_MODEL,
    SOFTWARE_DEPENDENCY_MODEL,
    SUPPLY_CHAIN_MODEL,
)


def test_patient_journey_model() -> None:
    DataModel.model_validate(PATIENT_JOURNEY_MODEL)


def test_supply_chain_model() -> None:
    DataModel.model_validate(SUPPLY_CHAIN_MODEL)


def test_software_dependency_model() -> None:
    DataModel.model_validate(SOFTWARE_DEPENDENCY_MODEL)


def test_oil_gas_monitoring_model() -> None:
    DataModel.model_validate(OIL_GAS_MONITORING_MODEL)


def test_customer_360_model() -> None:
    DataModel.model_validate(CUSTOMER_360_MODEL)


def test_fraud_aml_model() -> None:
    DataModel.model_validate(FRAUD_AML_MODEL)


def test_health_insurance_fraud_model() -> None:
    DataModel.model_validate(HEALTH_INSURANCE_FRAUD_MODEL)
