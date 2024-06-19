from langchain.prompts import ChatPromptTemplate
from langchain.prompts import  ChatPromptTemplate, HumanMessagePromptTemplate,SystemMessagePromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain.memory import ConversationBufferWindowMemory
from langchain.llms.base import LLM
from graph_database import GraphData
from config import neo4j_config
from config import tongyi_config
from config import openai_config
from prompt import REWRITE_QUERY_PROMPT, CYPHER_GENERATION_PROMPT, TO_FORMAT_PROMPT, ANSWER_GENERATION_PROMPT_HUMAN, ANSWER_GENERATION_PROMPT_SYSTEM

class QueryRewriter:
    """ 问题改写器
    
    根据问题和记忆, 利用LLM生成一个新问题, 使得问题具体化和完整化
    """

    def __init__(self):
        self.__chain = self.__get_rewrite_query_chain()

    def rewrite_query(self, query: str, history: str):
        '''
        改写提问
        query: 原问题
        history: 记忆
        return: 改写后的问题 
        '''
        return self.__chain.invoke({'query':query, 'history':history}).content

    def __get_rewrite_query_chain(self):
        # prompt
        prompt = ChatPromptTemplate(        
            messages=[
                    HumanMessagePromptTemplate.from_template(REWRITE_QUERY_PROMPT)
            ],
            input_variables=['query','hitsory'] )

        llm = ChatOpenAI(api_key=openai_config.OPENAI_API_KEY,
                        model=openai_config.model,
                        base_url=openai_config.base_url)

        chain = prompt | llm    
        return chain
    
class CypherGenerator:
    """ Cyphers语句生成器

    根据提问, 生成对应的查询语句
    """
    def __init__(self, limit = 10):
       """初始化Cypher语句生成器

       limit: 语句查询结果限制数
       """
       self.__limit = limit
       self.__chain = self.__get_cypher_generation_chain()
       
       
    def generate_cyphers(self, query):
        """生成cypher语句 
        
        query: 问题
        limit: cyphers 查询语句的limit限制
        return: list[str] cypher语句 
        """
        
        res = self.__chain.invoke({'query':query, 'limit':self.__limit}).content

        if res.count('RETURN') == 0:# 0个cypher语句，直接返回空list
            return []
        
        res = res.replace('`','')#处理，变成正确的cypher语句
        res = res.split('***')# 分割成list
        return res
    
    def change_limit(self, limit: int):
        self.__limit = limit

    def __get_cypher_generation_chain(self):
        """获取cyper语句生成链

        """
        prompt = ChatPromptTemplate.from_template(CYPHER_GENERATION_PROMPT)
        llm = ChatOpenAI(api_key=openai_config.OPENAI_API_KEY,
                        model=openai_config.model,
                        base_url=openai_config.base_url)
        chain = prompt | llm
        return chain
      
class CypherQuerier:
    """Cypher语句查询器
    
    对图数据库执行查询
    """

    def __init__(self, graph :GraphData):
        """

        graph: 图数据库对象
        """
        self.__graph = graph
        
    def close(self):
        """ 关闭图数据库连接

        """
        self.__graph.close()

    def kg_serach(self, cyphers):
        """查询图数据库

        cyphers (list(str)): cyphers语句列表
        """
        count = len(cyphers)

        neo4jRes=[]
        #初始化图谱查询
        if count==0:#为空，查询结果为空
            neo4jRes = []
        elif count==1:#1个， 查询一次
                neo4jRes = self.__graph.execute_query(cyphers[0])
        else :#多个，循环处理
            for cypher in cyphers:
                    neo4jRes = neo4jRes + self.__graph.execute_query(cypher) 
        return neo4jRes
    
class Formatter:
    """结果格式化器


    """
    def __init__(self, llm =None):
        """
        llm: langchain llm 模型
        """
        self.llm = llm
        if self.llm is None:
            self.llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)
        self.__chain = self.__get_format_chain()


    def kg_results_format(self, kg_results):
        '''
        格式化图谱查询结果
        kg_results: neo4j库原始查询结果
        '''
        
        return self.__chain.invoke(kg_results).content

    def __get_format_chain(self):
        
        format_prompt = ChatPromptTemplate.from_template(TO_FORMAT_PROMPT)
 
        chain = format_prompt | self.llm

        return chain

class AnswerGenerator:

    """ 回答生成器
    """

    def __init__(self, llm=None, k=5): 
        """
        llm: langchain llm 模型
        k: 保存的对话轮数
        """
        if llm is None:
            self.llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)
        else:
            self.llm = llm
        
        self.__chain = self.__get_generation_chain()
        self.__memory = ConversationBufferWindowMemory(k=k)

    def generate(self, query, kg_infomation, stream ='no'):
        """生成回答
        :query 问题
        :kg_information 图谱信息
        :stream: 是否使用流式输出, 
                                'no':不使用流式输出, return 回答
                                'stream': 同步流式输出, return 同步stream迭代器
                                'astream': 异步流式输出, return 异步stream迭代器
        """

        if stream == 'no': # 不使用流式输出
            output = self.__chain.invoke({'query':query,
                                            'kg_infomation':kg_infomation,
                                            'history':self.__memory.load_memory_variables({})})
        elif stream == 'stream':# 同步流式输出
            output = self.__chain.stream({'query':query,
                                            'kg_infomation':kg_infomation,
                                            'history':self.__memory.load_memory_variables({})})
        elif stream == 'astream':# 异步流式输出
            output = self.__chain.astream({'query':query,
                                            'kg_infomation':kg_infomation,
                                            'history':self.__memory.load_memory_variables({})})
        else:
            output = self.__chain.invoke({'query':query,
                                            'kg_infomation':kg_infomation,
                                            'history':self.__memory.load_memory_variables({})})
        return output
    
    def get_memory(self):
        """获取记忆
        """
        return self.__memory.load_memory_variables({})
    
    def save_memory(self, query, answer):
        """ 保存记忆
        
        query: HUMAN问题
        answer: AI回答
        """
        # 添加记忆
        self.__memory.chat_memory.add_user_message(query)
        # self.__memory.chat_memory.add_ai_message(output.content)
        self.__memory.chat_memory.add_ai_message(answer)
        # return output.content

    def refresh_memory(self, k=5):
        self.__memory = ConversationBufferWindowMemory(k = k)

    def __get_generation_chain(self):

        '''
        获取回答生成链
        '''
        # prompt
        prompt = ChatPromptTemplate(        
            messages=[
                    SystemMessagePromptTemplate.from_template(ANSWER_GENERATION_PROMPT_SYSTEM),
                    HumanMessagePromptTemplate.from_template(ANSWER_GENERATION_PROMPT_HUMAN)
            ],
            # 对话记忆
            # partial_variables = {"history": memory.load_memory_variables({})['history']},
            # partial_variables = {"history": memory.load_memory_variables({})},
            input_variables=['query', 'kg_infomation', 'history'] )

        chain = prompt | self.llm

        return chain
    
class DefinedLLM(LLM):
    def __init__(self) -> None:
        pass #需要使用本地大模型的可以继承LangCahin的LLM重写