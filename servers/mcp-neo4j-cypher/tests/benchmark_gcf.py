"""
Benchmark: JSON vs GCF for Neo4j query results.
Tests encode_generic on raw results AND on restructured (flattened) graph data.
"""
import json
import random
import tiktoken
import gcf

enc = tiktoken.get_encoding("o200k_base")
def count_tokens(text: str) -> int:
    return len(enc.encode(text))

cities = ["San Francisco", "New York", "London", "Berlin", "Tokyo", "Sydney", "Toronto", "Austin"]
departments = ["Engineering", "Marketing", "Sales", "Support", "Product", "Design", "Finance", "Legal"]
labels = ["Person", "Company", "Project", "Team"]
rel_types = ["KNOWS", "WORKS_AT", "MANAGES", "MEMBER_OF", "REPORTS_TO"]

def make_node_rows(count):
    """MATCH (n:Person) RETURN n.name, n.age, n.email, n.city, n.department, n.salary"""
    return [
        {"name": f"Person_{i}", "age": random.randint(22, 65), "email": f"person_{i}@company.com",
         "city": random.choice(cities), "department": random.choice(departments),
         "salary": random.randint(50000, 250000), "active": random.choice([True, False]),
         "hire_date": f"202{random.randint(0,5)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"}
        for i in range(count)
    ]

def make_rel_rows(count):
    """MATCH (a)-[r:KNOWS]->(b) RETURN a.name, r.since, r.weight, r.type, b.name"""
    return [
        {"a_name": f"Person_{i}", "since": f"202{random.randint(0,5)}-{random.randint(1,12):02d}",
         "weight": round(random.uniform(0.1, 1.0), 2),
         "rel_type": random.choice(["colleague", "friend", "manager", "mentor"]),
         "b_name": f"Person_{random.randint(0, count-1)}"}
        for i in range(count)
    ]

def make_graph_results(node_count, edge_count):
    """
    Simulate a graph query that returns nodes and relationships.
    Raw format: {"nodes": [{id, labels, properties}, ...], "relationships": [{startNode, endNode, type, properties}, ...]}
    Restructured: separate the nodes and relationships into flat tables.
    """
    nodes = [
        {"id": i, "label": random.choice(labels), "name": f"{random.choice(labels)}_{i}",
         "age": random.randint(22, 65) if random.random() > 0.3 else None,
         "city": random.choice(cities) if random.random() > 0.4 else None,
         "department": random.choice(departments) if random.random() > 0.5 else None}
        for i in range(node_count)
    ]
    rels = [
        {"source": random.randint(0, node_count-1), "target": random.randint(0, node_count-1),
         "type": random.choice(rel_types), "since": 2020 + random.randint(0, 5),
         "weight": round(random.uniform(0.1, 1.0), 2)}
        for _ in range(edge_count)
    ]

    # Raw: nested structure (how Neo4j returns it via driver.data())
    raw = {"nodes": nodes, "relationships": rels}

    # Restructured: separate tables (what we'd convert to before encoding)
    restructured = {"nodes": nodes, "relationships": rels}

    return raw, restructured

def make_movie_cast(count):
    """MATCH (m:Movie)<-[:ACTED_IN]-(a:Actor) RETURN m.title, m.year, m.genre, m.rating, collect(a.name)"""
    genres = ["Action", "Drama", "Comedy", "Thriller", "Sci-Fi"]
    return [
        {"title": f"Movie_{i}", "year": random.randint(1990, 2026), "genre": random.choice(genres),
         "rating": round(random.uniform(1.0, 10.0), 1), "votes": random.randint(100, 500000),
         "actors": [f"Actor_{random.randint(1, 200)}" for _ in range(random.randint(2, 6))],
         "director": f"Director_{random.randint(1, 50)}"}
        for i in range(count)
    ]

def benchmark(name, data, sizes_label=""):
    json_str = json.dumps(data, default=str)
    gcf_str = gcf.encode_generic(data)
    json_tok = count_tokens(json_str)
    gcf_tok = count_tokens(gcf_str)
    saved = json_tok - gcf_tok
    pct = (saved / json_tok * 100) if json_tok > 0 else 0
    print(f"  {name:<35} JSON: {json_tok:>8,}  GCF: {gcf_tok:>8,}  saved: {saved:>7,} ({pct:>5.1f}%)")
    return json_tok, gcf_tok

print("=" * 95)
print("Neo4j MCP Server: JSON vs GCF Token Benchmark")
print("Tokenizer: o200k_base (GPT-4o / Claude)")
print("=" * 95)

total_j, total_g = 0, 0

print("\n1. TABULAR NODE QUERIES (MATCH (n:Person) RETURN n.*)")
print("-" * 95)
for size in [10, 50, 100, 500, 1000]:
    j, g = benchmark(f"{size} rows", make_node_rows(size))
    total_j += j; total_g += g

print("\n2. RELATIONSHIP QUERIES (MATCH (a)-[r]->(b) RETURN ...)")
print("-" * 95)
for size in [10, 50, 100, 500, 1000]:
    j, g = benchmark(f"{size} rows", make_rel_rows(size))
    total_j += j; total_g += g

print("\n3. GRAPH RESULTS (nodes + relationships)")
print("-" * 95)
for nodes, edges in [(20, 15), (50, 40), (100, 80), (500, 400), (1000, 800)]:
    raw, _ = make_graph_results(nodes, edges)
    j, g = benchmark(f"{nodes} nodes, {edges} edges", raw)
    total_j += j; total_g += g

print("\n4. MOVIE DATABASE (nested arrays)")
print("-" * 95)
for size in [10, 50, 100, 500]:
    j, g = benchmark(f"{size} movies", make_movie_cast(size))
    total_j += j; total_g += g

print()
print("=" * 95)
overall_pct = ((total_j - total_g) / total_j * 100) if total_j > 0 else 0
print(f"OVERALL: JSON {total_j:,} tokens -> GCF {total_g:,} tokens ({overall_pct:.1f}% fewer tokens)")
print("=" * 95)
