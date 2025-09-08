import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with consistent configuration."""
    return logging.getLogger(name)

def _validate_region(cloud_provider: str, region: str) -> None:
    """
    Validate the region exists for the given cloud provider.

    Args:
        cloud_provider: The cloud provider to validate the region for
        region: The region to validate

    Returns:
        None
    
    Raises:
        ValueError: If the region is not valid for the given cloud provider
    """

    if cloud_provider == "gcp" and region.count("-") != 1:
        raise ValueError(f"Invalid region for GCP: {region}. Must follow the format 'region-zonenumber'. Refer to https://neo4j.com/docs/aura/managing-instances/regions/ for valid regions.")
    elif cloud_provider == "aws" and region.count("-") != 2:
        raise ValueError(f"Invalid region for AWS: {region}. Must follow the format 'region-zone-number'. Refer to https://neo4j.com/docs/aura/managing-instances/regions/ for valid regions.")
    elif cloud_provider == "azure" and region.count("-") != 0:
        raise ValueError(f"Invalid region for Azure: {region}. Must follow the format 'regionzone'. Refer to https://neo4j.com/docs/aura/managing-instances/regions/ for valid regions.")