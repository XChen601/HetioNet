import os
from dotenv import load_dotenv

from pymongo import MongoClient


class MongoDB:
    def __init__(self):
        load_dotenv()
        uri = os.getenv("MONGODB_URI")
        client = MongoClient(uri)
        self.db = client['HetioNet']
        print("Connected to HetioNet with MongoDB")

    # function to get the id, name, and kind for the nodes
    # Anatomy::UBERON:0000002	uterine cervix	Anatomy
    def extract_nodes(self, file):
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

    def add_node(self, node_id, name, kind):
        collection = self.db[kind]
        document = {
            "_id": node_id,
            "name": name,
            "kind": kind
        }

        result = collection.insert_one(document)
        print(result)

    def add_all_nodes(self):
        nodes = self.extract_nodes('nodes.tsv')
        for node in nodes:
            self.add_node(node[0], node[1], node[2])

    def extract_edges(self, file):
        edges = []
        with open(file) as f:
            next(f)
            for line in f:
                parts = line.split()
                source = parts[0]
                metaedge = parts[1]
                target = parts[2]
                edge = (source, metaedge, target)
                # only add the edges that will be used bc too much data
                needed_metaedge = ["CtD", "CpD", "DaG", "DlA", "CdG", "CuG", "DdG", "CtD", "CdG", "DuG"]
                if metaedge in needed_metaedge:
                    edges.append(edge)
        return edges

    def add_edge(self, source, metaedge, target):
        collection = self.db[metaedge]
        document = {
            "source": source,
            "metaedge": metaedge,
            "target": target
        }
        result = collection.insert_one(document)
        print(result)

    def add_all_edges(self):
        edges = self.extract_edges('edges.tsv')
        for edge in edges:
            self.add_edge(edge[0], edge[1], edge[2])

    def create_database(self):
        self.add_all_nodes()
        self.add_all_edges()


# https://github.com/hetio/hetionet/blob/main/describe/edges/metaedges.tsv

# seperate the metaedges into seperate collections

# Run only once to create database
mongo = MongoDB()
mongo.create_database()