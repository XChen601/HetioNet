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

    def query_one(self, disease):
        """
        Given disease id:
        - Get the name
        - Treat disease:
            - Compound - treats - Disease (CtD)
        - Palliate disease:
            - Compound - palliates - Disease (CpD)
        - Gene names that cause this diseases: Disease - associates - Gene (DaG)
        - Where it occurs: Disease - localizes - Anatomy (DlA)
        :param disease:string
        :return:list of the mongodb query result
        """
        query = [
            {
                "$match": {"_id": disease}
            },
            {
                "$lookup": {
                    "from": "CtD",
                    "localField": "_id",
                    "foreignField": "target",
                    "as": "treatments_id"
                }
            },
            {
                "$lookup": {
                    "from": "CpD",
                    "localField": "_id",
                    "foreignField": "target",
                    "as": "palliates_id"
                }
            },
            {
                "$lookup": {
                    "from": "DaG",
                    "localField": "_id",
                    "foreignField": "source",
                    "as": "genes_id"
                }
            },
            {
                "$lookup": {
                    "from": "DlA",
                    "localField": "_id",
                    "foreignField": "source",
                    "as": "occurs_id"
                }
            },
            {
                "$lookup": {
                    "from": "Compound",
                    "localField": "treatments_id.source",
                    "foreignField": "_id",
                    "as": "treatments"
                }
            },
            {
                "$lookup": {
                    "from": "Compound",
                    "localField": "palliates_id.source",
                    "foreignField": "_id",
                    "as": "palliates"
                }
            },
            {
                "$lookup": {
                    "from": "Gene",
                    "localField": "genes_id.target",
                    "foreignField": "_id",
                    "as": "genes"
                }
            },
            {
                "$lookup": {
                    "from": "Anatomy",
                    "localField": "occurs_id.target",
                    "foreignField": "_id",
                    "as": "occurs"
                }
            },
            {
                "$project": {
                    "name": 1,
                    "treatments.name": 1,
                    "palliates.name": 1,
                    "genes.name": 1,
                    "occurs.name": 1,
                }
            }
        ]
        diseases = self.db["Disease"]
        result = list(diseases.aggregate(query))
        print(result)

        # Print the result
        self.printQueryOneResult(result)
        return result

    def printQueryOneResult(self, result):
        print(f"Disease ID: {result[0]['_id']}")
        print(f"Name: {result[0]['name']}")
        treatments = []
        for treatment in result[0]['treatments']:
            treatments.append(treatment["name"])

        print(f"Compounds that treat disease: {treatments}")

        palliates = []
        for palliate in result[0]['palliates']:
            palliates.append(palliate["name"])

        print(f"Compounds that palliates disease: {palliates}")

        genes = []
        for gene in result[0]['genes']:
            genes.append(gene["name"])

        print(f"Genes that causes the disease: {genes}")

        occurs_list = []
        for occurs in result[0]['occurs']:
            occurs_list.append(occurs["name"])
        print(f"Where it occurs: {occurs_list}")

    def query_two(self):
        """
        Find compound where:
        - Compound up-regulates a gene and (CuG)
        - disease down-regulates a gene but (DdG)
        - compound does not treat disease (CtD)

        or


        - Compound down-regulates a gene and (CdG)
        - disease up-regulates a gene but (DuG)
        - compound does not treat disease (CtD)
        :return:
        """
        # step 1: genes where gene in CuG == gene in DdG
        # step 2: compound where compound not in CtD
        query = [
            {
                "$lookup": {
                    "from": "DdG",
                    "localField": "target",
                    "foreignField": "target",
                    "as": "gene_matches"
                },
            },
            {
                "$match": {
                    "gene_matches": {"$ne": []}
                }
            },
            {
                "$lookup": {
                    "from": "CtD",
                    "localField": "source",
                    "foreignField": "source",
                    "as": "compound_matches"
                },
            },
            {
                "$match": {
                    "compound_matches": {"$size": 0} # where compound is not in CtD
                }
            },
            {
                "$lookup": {
                    "from": "Compound",
                    "localField": "source",
                    "foreignField": "_id",
                    "as": "compound_names"
                },
            },
            {
                "$project": {
                    "compound_names.name": 1,
                }
            }
        ]

        result = list(self.db["CuG"].aggregate(query))
        # Assuming `result` contains the output from the aggregate query
        print(result)


# https://github.com/hetio/hetionet/blob/main/describe/edges/metaedges.tsv

# seperate the metaedges into seperate collections

# Run only once to create database
mongo = MongoDB()
# mongo.create_database()
#mongo.query_one("Disease::DOID:1686")
mongo.query_two()