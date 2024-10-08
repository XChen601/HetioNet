import os
from dotenv import load_dotenv

from pymongo import MongoClient

load_dotenv()
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)

# Access a specific database
db = client['HetioNet']


# function to get the id, name, and kind for the nodes
# Anatomy::UBERON:0000002	uterine cervix	Anatomy
def extract_nodes(file):
    nodes = []
    with open(file) as f:
        next(f)
        for line in f:
            parts = line.split()
            node_id = parts[0]
            name = " ".join(parts[1:-1])
            kind = parts[-1]
            node = (node_id, name, kind)
            nodes.append(node)
            print(node)
    return nodes

def add_node(node_id, name, kind):
    collection = db[kind]
    document = {
        "_id": node_id,
        "name": name,
        "kind": kind
    }

    collection.insert_one(document)

def add_all_nodes():
    nodes = extract_nodes('nodes.tsv')
    for node in nodes:
        add_node(node[0], node[1], node[2])

def extract_edges(file):
    edges = []
    with open(file) as f:
        next(f)
        for line in f:
            parts = line.split()
            source = parts[0]
            metaedge = parts[1]
            target = parts[2]
            edge = (source, metaedge, target)
            edges.append(edge)
    return edges

def add_edge(source, metaedge, target):
    collection = db[metaedge]
    document = {
        "source": source,
        "metaedge": metaedge,
        "target": target
    }
    collection.insert_one(document)

def add_all_edges():
    edges = extract_edges('edges.tsv')
    for edge in edges:
        add_edge(edge[0], edge[1], edge[2])

def create_database():
    add_all_nodes()
    add_all_edges()

def main():
    create_database()

main()
# https://github.com/hetio/hetionet/blob/main/describe/edges/metaedges.tsv

# seperate the metaedges into seperate collections