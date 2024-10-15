from neo4j import GraphDatabase

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "password")


class Neo4jDB:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=AUTH)
        self.session = self.driver.session()
        print("Connected to Neo4j")

    def close(self):
        self.driver.close()

    def extract_nodes(self, file):
        nodes = []
        with open(file) as f:
            next(f)  # Skip header line
            for line in f:
                parts = line.split()
                id = parts[0]
                name = " ".join(parts[1:-1])
                kind = parts[-1]
                node = (id, name, kind)
                nodes.append(node)
        return nodes

    def add_node(self, node_id, name, kind):
        query = """
        MERGE (n:{kind} {{id: $id, name: $name}})
        """.format(kind=kind)
        self.session.run(query, id=node_id, name=name)
        print(f"Node {node_id} added")

    def add_all_nodes(self, nodes):
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
                needed_metaedge = ["CdG", "CuG", "CtD", "DlA", "AuG", "AdG"]
                if metaedge in needed_metaedge:
                    edges.append(edge)
        return edges

    def add_edge(self, source, metaedge, target, nodes):
        if metaedge in ["CdG", "CuG", "AuG", "AdG", "CtD", "DlA"]:
            name = next(node[1] for node in nodes if node[0] == source)
        else:
            name = next(node[1] for node in nodes if node[0] == target)
        relations_dict = {"u": "upregulates", "d": "downregulates", "t": "treats", "l": "localizes"}
        relation = relations_dict[metaedge[1]]
        query = """
        MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
        MERGE (a)-[r:{relation}]->(b)
        SET r.name = $name
        """.format(relation=relation)
        self.session.run(query, source_id=source, target_id=target, name=name)
        print(f"Edge {source} -[{relation}]-> {target} added")

    def add_all_edges(self, edges, nodes):
        for edge in edges:
            self.add_edge(edge[0], edge[1], edge[2], nodes)

    def create_database(self):
        nodes = self.extract_nodes('nodes.tsv')
        self.add_all_nodes(nodes)
        edges = self.extract_edges('edges.tsv')
        self.add_all_edges(edges, nodes)

    def query_two(self, disease_id):
        """
        Find compound where:
        - Compound upregulates a gene and (CuG)
        - Anatomy downregulates a gene (AdG)
        - Disease localizes in anatomy (DlA)
        - compound does not treat disease (CtD)

        or

        - Compound downregulates a gene and (CdG)
        - Anatomy upregulates a gene (AuG)
        - Disease localizes in anatomy (DlA)
        - compound does not treat disease (CtD)

        """
        parts = disease_id.split("::")
        disease_id = f"{parts[0].capitalize()}::{parts[1].upper()}"


        query = f"""
        MATCH (compound:Compound)-[:upregulates]->(gene:Gene),
                (disease:Disease {{id: '{disease_id}'}})-[:localizes]->(location:Anatomy)-[:downregulates]->(gene)
        WHERE NOT (compound)-[:treats]->(disease)
        RETURN DISTINCT compound.name
        
        UNION
        
        MATCH (compound:Compound)-[:downregulates]->(gene:Gene),
                (disease:Disease {{id: '{disease_id}'}})-[:localizes]->(location:Anatomy)-[:upregulates]->(gene)
        WHERE NOT (compound)-[:treats]->(disease)
        RETURN DISTINCT compound.name

        """
        result = self.session.run(query)
        compound_names = [record["compound.name"] for record in result]
        print(compound_names)
        print("total names:", len(compound_names))
        return compound_names
# db = Neo4jDB()
# db.create_database()
# nodes, name_to_id = db.extract_nodes('nodes.tsv')
# db.add_all_nodes(nodes)
# edges = db.extract_edges('edges.tsv')
# db.add_all_edges(edges, nodes)
# db.close()

