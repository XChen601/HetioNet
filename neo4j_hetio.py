from neo4j import GraphDatabase


class Neo4JQuery:
    def __init__(self):
        self.uri = "bolt://localhost:7687"
        self.auth = ("neo4j", "password")
        self.driver = GraphDatabase.driver(self.uri, auth=self.auth)
        self.session = self.driver.session()

    def extract_nodes(self, file):
        nodes = {}  # {id: {"name": name, "kind": kind}}
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
        query = f"""
        MERGE (n: {kind} {{name: $name, id: $node_id}})
        """
        result = self.session.run(query, name=name, node_id=node_id)

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
                needed_metaedge = ["CuG", "AdG", "DlA", "CtD", "CdG", "AuG"]
                if metaedge in needed_metaedge:
                    edges.append(edge)
        return edges

    def add_edge(self, source, metaedge, target):
        # source_id --metaedge--> target_id
        relations_dict = {"u":"upregulates", "d":"downregulates", "t":"treats", "l":"localizes"}
        source_label = source.split("::")[0]
        target_label = target.split("::")[0]
        relation = relations_dict[metaedge[1]] # ex: gets "u" then gets "upregulates"
        query = f"""
        MATCH (a:{source_label} {{id: "{source}"}}),(b:{target_label} {{id: "{target}"}})
        MERGE (a)-[r:{relation}]->(b)
        RETURN a, b, r 
        """

        result = self.session.run(query)

    def add_all_edges(self, edges):
        for edge in edges:
            self.add_edge(edge[0], edge[1], edge[2])

    def create_database(self):
        # add all the nodes
        nodes = self.extract_nodes('nodes.tsv')
        self.add_all_nodes(nodes)

        # add the edges for CuG, DdG, CtD, CdG, DuG, CtD
        edges = self.extract_edges("edges.tsv")
        self.add_all_edges(edges)

    def query_two(self):
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
        query = """
        MATCH (compound:Compound)-[:upregulates]->(gene:Gene),
              (anatomy:Anatomy)-[:downregulates]->(gene),
              (disease:Disease)-[:localizes]->(anatomy)
        WHERE NOT (compound)-[:treats]->(disease)
        RETURN DISTINCT compound.name
        
        UNION
        
        MATCH (compound:Compound)-[:downregulates]->(gene:Gene),
              (anatomy:Anatomy)-[:upregulates]->(gene),
              (disease:Disease)-[:localizes]->(anatomy)
        WHERE NOT (compound)-[:treats]->(disease)
        RETURN DISTINCT compound.name

        """
        result = self.session.run(query)
        compound_names = [record["compound.name"] for record in result]
        print(compound_names)
        print("total names:", len(compound_names))
        return compound_names

# neo4j = Neo4JQuery()
# neo4j.create_database()
# neo4j.query_two()
