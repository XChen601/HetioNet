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
        nodes = {} # {id: {"name": name, "kind": kind}}
        with open(file) as f:
            next(f)
            for line in f:
                parts = line.split()
                node_id = parts[0]
                name = " ".join(parts[1:-1])
                kind = parts[-1]
                nodes[node_id] = {"name": name, "kind": kind}
        return nodes

    def add_node(self, node_id, name, kind):
        collection = self.db[kind]
        document = {
            "_id": node_id,
            "name": name,
        }

        result = collection.insert_one(document)
        print(result)

    def add_all_nodes(self, nodes):
        for id in nodes:
            self.add_node(id, nodes[id]["name"], nodes[id]["kind"])

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
                needed_metaedge = ["CtD", "CpD", "DaG", "DlA"]
                if metaedge in needed_metaedge:
                    edges.append(edge)
        return edges

    def add_edge(self, source, metaedge, target, nodes):
        # add to the disease document
        collection = self.db['Disease']
        # add the source to the corresponding list
        if metaedge == "CtD" or metaedge == "CpD":
            result = collection.update_one(
                {"_id": target},
                # adds the name of the compound by retrieving from nodes dict
                {"$addToSet": {metaedge: nodes[source]["name"]}}
            )
        else:
            result = collection.update_one(
                {"_id": source},
                {"$addToSet": {metaedge: nodes[target]["name"]}}
            )
        print(result)

    def add_all_edges(self, edges, nodes):
        for edge in edges:
            self.add_edge(edge[0], edge[1], edge[2], nodes)

    def create_database(self):
        # add all the nodes
        nodes = self.extract_nodes('nodes.tsv')
        self.add_all_nodes(nodes)
        # add the edges related to diseases (CtD, CpD, DaG, DlA)
        edges = self.extract_edges('edges.tsv')
        self.add_all_edges(edges, nodes)

    def query_one(self, disease_id):

        disease_info = self.db['Disease'].find_one({"_id": disease_id})
        print(disease_info)
        return disease_info



    # def query_two(self):
    #     """
    #     Find compound where:
    #     - Compound up-regulates a gene and (CuG)
    #     - disease down-regulates a gene but (DdG)
    #     - compound does not treat disease (CtD)
    #
    #     or
    #
    #
    #     - Compound down-regulates a gene and (CdG)
    #     - disease up-regulates a gene but (DuG)
    #     - compound does not treat disease (CtD)
    #     :return:
    #     """
    #     # step 1: genes where gene in CuG == gene in DdG
    #     # step 2: compound where compound not in CtD
    #     query = [
    #         {
    #             "$lookup": {
    #                 "from": "DdG",
    #                 "localField": "target",
    #                 "foreignField": "target",
    #                 "as": "gene_matches"
    #             },
    #         },
    #         {
    #             "$match": {
    #                 "gene_matches": {"$ne": []}
    #             }
    #         },
    #         {
    #             "$lookup": {
    #                 "from": "CtD",
    #                 "localField": "source",
    #                 "foreignField": "source",
    #                 "as": "compound_matches"
    #             },
    #         },
    #         {
    #             "$match": {
    #                 "compound_matches": {"$size": 0} # where compound is not in CtD
    #             }
    #         },
    #         {
    #             "$lookup": {
    #                 "from": "Compound",
    #                 "localField": "source",
    #                 "foreignField": "_id",
    #                 "as": "compound_names"
    #             },
    #         },
    #         {
    #             "$project": {
    #                 "compound_names.name": 1,
    #             }
    #         }
    #     ]
    #
    #     result = list(self.db["CuG"].aggregate(query))
    #     # Assuming `result` contains the output from the aggregate query
    #     print(result)
    #     return result


# https://github.com/hetio/hetionet/blob/main/describe/edges/metaedges.tsv


# Run only once to create database
#mongo = MongoDB()
#mongo.create_database()
#mongo.query_one("Disease::DOID:1686")
# mongo.query_two()