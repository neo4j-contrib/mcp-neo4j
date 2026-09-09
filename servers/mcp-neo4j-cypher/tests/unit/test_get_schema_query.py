import pytest

from mcp_neo4j_cypher.utils import build_get_schema_query

NO_SAMPLE_QUERY = "CALL apoc.meta.schema() YIELD value RETURN value"
SAMPLED_QUERY = "CALL apoc.meta.schema({sample: $sample_size}) YIELD value RETURN value"


@pytest.mark.parametrize("sample_size", [None, 0])
def test_falsy_sample_size_omits_sample_argument(sample_size):
    query, params = build_get_schema_query(sample_size)
    assert query == NO_SAMPLE_QUERY
    assert "None" not in query
    assert params == {}


@pytest.mark.parametrize("sample_size", [1, 500, 1000, -1])
def test_truthy_sample_size_binds_parameter(sample_size):
    query, params = build_get_schema_query(sample_size)
    assert query == SAMPLED_QUERY
    assert str(sample_size) not in query
    assert params == {"sample_size": sample_size}
