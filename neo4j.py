from neo4j import GraphDatabase, RoutingControl

#  Without header
# LOAD CSV FROM ‘$path/artists-without-headers.csv' AS line
# CREATE (:Artist { name: line[1], year: toInteger(line[2])})
# • With header
# LOAD CSV WITH HEADERS FROM ‘$path/artists-with-headers.csv' AS line
# CREATE (:Artist { name: line.Name, year: toInteger(line.Year)})
# • With customer delimiter (how about tab?)
# LOAD CSV FROM ‘$path/artists-delimiter.csv' AS line FIELDTERMINATOR ‘;’
# CREATE (:Artist { name: line[1], year: toInteger(line[2])})
# • Large file
# USING PERIODIC COMMIT 500

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "password")

# function to get the id, name, and kind for the nodes
# Anatomy::UBERON:0000002	uterine cervix	Anatomy
def extract_nodes(file):
    nodes = []
    with open(file) as f:
        for line in f:
            # print(line)
            # print()
            parts = line.split()
            id = parts[0]
            name = "".join(parts[1:-1])
            kind = parts[-1]
            node = (id, name, kind)
            nodes.append(node)
            print(node)
    return nodes

def add_node(driver, id, name, kind):
    query = f"MERGE (a:{kind} {{id: $id, name: $name, kind: $kind}})"
    driver.execute_query(query, id=id, name=name, kind=kind)


with GraphDatabase.driver(URI, auth=AUTH) as driver:
    nodes = extract_nodes("nodes.tsv")
    for node in nodes:
        add_node(driver, node[0], node[1], node[2])
