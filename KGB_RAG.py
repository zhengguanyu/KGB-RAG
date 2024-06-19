import time

from graph_database import GraphData
from module import QueryRewriter, CypherGenerator, CypherQuerier, Formatter, AnswerGenerator


from config import neo4j_config

from langchain_openai.chat_models import ChatOpenAI
from config import openai_config

class KGB_RAG:

    
    def __init__(self):
        # 图数据库
        self.graph = GraphData(uri=neo4j_config.url,
                        user=neo4j_config.username,
                        password=neo4j_config.password)
        
        self.query_rewriter = QueryRewriter()
        self.cypher_generator = CypherGenerator()
        self.cypher_querier = CypherQuerier(graph = self.graph)
        self.formatter = Formatter()
        self.answer_generator = AnswerGenerator()
        
    def chat(self, query, stream='no'):
        """ 对话

        query: 问题
        stream: 是否使用流式输出, 
            'no'(default): 不使用流式输出,直接返回回答
            'stream': 同步流式输出,返回一个同步迭代器
            'astream': 异步流式输出,返回一个异步迭代器
        """
        start = time.time()

        # 改写提问
        print('memory:',self.answer_generator.get_memory())
        query = self.query_rewriter.rewrite_query(query=query, 
                                                  history=self.answer_generator.get_memory())
        end = time.time()
        print('query rewrite: ',end-start,'s')
        start = time.time()
        print('new query:',query)

        # 生成cyphers语句
        cyphers = self.cypher_generator.generate_cyphers(query)
        end = time.time()
        print('cypher generate: ',end-start,'s')
        start = time.time()
        print('cyphers:',cyphers)

        format_kg_results= ''
        
        if len(cyphers) != 0:

            # 搜索图谱
            end = time.time()
            kg_results = self.cypher_querier.kg_serach(cyphers)
            print('cypher query: ',time.time()-start,'s')
            start = time.time()
            print("kg_results:",kg_results)
    
            if len(kg_results) != 0:

                # 格式化图谱查询答案
                format_kg_results = self.formatter.kg_results_format(kg_results)
                end = time.time()
                print('format kg results: ',time.time()-start,'s')
                start = time.time()
                print("format_kg_results:",format_kg_results)

        # 结合图谱结果生成回答
        answer = self.answer_generator.generate(query=query, 
                                                kg_infomation=format_kg_results,
                                                stream=stream)
        print('answer:', answer)
        return answer
    
    def save_history(self, query, answer):
        """ 保存对话历史

        query: human的问题
        answer: ai的回答
        """
        self.answer_generator.save_memory(query=query, answer=answer)

    def refresh_history(self, k=5):
        """移除已有对话历史

        k:刷新后的历史保存轮数
        """
        self.answer_generator.refresh_memory(k=k)

    def change_model(self, llm, k=5):
        """切换模型
        
        对格式化和答案生成模块的llm模型进行更改

        llm: langchain格式的 chat 模型
        k: 希望保存的对话的轮数
        """
        self.answer_generator = AnswerGenerator(llm = llm, k=k)
        self.formatter.llm = Formatter(llm = llm)

    def change_limit(self, limit):
        """ 修改cypher语句的limit

        limit: 数量
        """
        self.cypher_generator.change_limit(limit=limit)

    
if __name__ == '__main__':

    kgb_rag = KGB_RAG()

    while True:
        query = input("input:")
        res = kgb_rag.chat(query)
        print('output:',res,'\n')