from mcp_neo4j_aura_manager.server import _validate_region
import pytest

def test_validate_region_aws_valid():
    # Test GCP regions
    assert _validate_region("aws", "us-east-1") is None
    assert _validate_region("aws", "eu-west-1") is None
    assert _validate_region("aws", "eu-east-1") is None

def test_validate_region_aws_invalid():
    # Test GCP regions
    with pytest.raises(ValueError):
        _validate_region("aws", "us-east1")
    with pytest.raises(ValueError):
        _validate_region("aws", "euwest")
    with pytest.raises(ValueError):
        _validate_region("aws", "eu-west-1-1-1")

def test_validate_region_gcp_valid():
    # Test GCP regions
    assert _validate_region("gcp", "us-central1") is None
    assert _validate_region("gcp", "europe-west1") is None
    assert _validate_region("gcp", "us-central2") is None

def test_validate_region_gcp_invalid():
    # Test GCP regions
    with pytest.raises(ValueError):
        _validate_region("gcp", "us-east-1")
    with pytest.raises(ValueError):
        _validate_region("gcp", "eu-west-1-1")
    with pytest.raises(ValueError):
        _validate_region("gcp", "euwest")

def test_validate_region_azure_valid():
    # Test Azure regions
    assert _validate_region("azure", "eastus") is None
    assert _validate_region("azure", "northeurope") is None

def test_validate_region_azure_invalid():
    # Test Azure regions
    with pytest.raises(ValueError):
        _validate_region("azure", "us-east-1")
    with pytest.raises(ValueError):
        _validate_region("azure", "eu-west1")