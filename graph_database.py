from neo4j import GraphDatabase
from config import neo4j_config
class GraphData:
    """
    图数据库类
    """

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """关闭数据库连接
        """
        self.driver.close()

    def execute_query(self,query) ->list:
        ''' 执行数据库查询
        
        query: 查询语句
        return: node list
        '''
        with self.driver.session() as session:
            nodes = session.read_transaction(self.get_node,query)
        return nodes
    
    @staticmethod
    def get_node(tx,query):
        result = tx.run(query)
        return result.data()
    

     #获取图schema，该项目实际不跑该代码，需要用户自己根据readme.md中的说明生成schema
    def schema_text(self,node_props, rel_props, rels) -> str:
        return f"""
                This is the schema representation of the Neo4j database.
                Node properties are the following:
                {node_props}
                Relationship properties are the following:
                {rel_props}
                The relationships are the following
                {rels}
                """

    def get_schema(
        self,
    ) -> str:
        """获取图schema
        """
        #获取图schema，该项目实际不跑该代码，需要用户自己根据readme.md中的说明生成schema
        print("loading graph schema")

        node_props = [el["output"] for el in self.execute_query(node_properties_query)]
        rel_props = [el["output"] for el in self.execute_query(rel_properties_query)]
        rels = [el["output"] for el in self.execute_query(rel_query)]
        schema = self.schema_text(node_props, rel_props, rels)
        schema = schema.replace("{","<").replace("}",">")

        print("finished")
        return schema 

node_properties_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "node"
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {labels: nodeLabels, properties: properties} AS output

"""

rel_properties_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "relationship"
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {type: nodeLabels, properties: properties} AS output
"""

rel_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE type = "RELATIONSHIP" AND elementType = "node"
RETURN "(:" + label + ")-[:" + property + "]->(:" + toString(other[0]) + ")" AS output
"""

if __name__ == '__main__':
    '''
    运行以生成图谱schema
    '''
    graph = GraphData(uri=neo4j_config.url,
                      user=neo4j_config.username,
                      password=neo4j_config.password)
    
    print(graph.get_schema())

    graph.close()


 

