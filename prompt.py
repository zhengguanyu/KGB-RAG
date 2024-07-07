
# rewrite you graph database schema prompt here
SCHEMA = """
Node: MovieLabel: xxx (STRING), xxx (INTEGER)

Relationship: (:xxx)-[:xxx]->(:xxx)

Relationship properties: xxx: xxx (INTEGER)
"""


PRE_MSG = f"""   
            System:Your task is to convert questions about contents in a Neo4j database to Cypher queries to query the Neo4j database.
            Use only the provided relationship types and properties.
            Do not use any other relationship types or properties that are not provided.
            If you cannot generate a Cypher statement based on the provided schema, explain the reason to the user.
            You must return something in your every Cypher statement.
            If you want to get a high rating, any cypher statement that you generate should never go against the relations, nodes, and relations attributes that I've given you in the schema.
            Pay attention to the direction of the arrow in the relationship and don't have an arrow direction that violates the rules.
            Here is the schema:{SCHEMA}
            """

# cypher语句生成prompt
CYPHER_GENERATION_PROMPT = PRE_MSG + """\n我的问题:"{query}"\n
    Note:      
        Write as many queries as you have questions.
        Do not write only one cypher statement if there are many questions.
        Do not include any explanations or apologies in your responses.
        In your query statement, do not write statments like WHERE .... IN ...., because this is not a Cypher syntax.
        Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
        Do not include any text except the generated Cypher statement. This is very important if you want to get paid.
        Always provide enough context for an LLM to be able to generate valid response.
        Please add limit {limit} in your every cypher statement.
        If there are more than one cypher statements, use triple multiplication sign (*) as a separator.
        Please wrap the generated Cypher statement in triple backticks (`).
        If you can not write the cypher statement about the question in my rules, just return MATCH (n) RETURN n LIMIT 0.
        Do not generate too many Cypher statements. For Cypher statements between two entities,
        select the ones that are most likely to retrieve the required information and generate only three."""


# 查询结果格式化prompt
TO_FORMAT_PROMPT =  """
                    我会给你图谱查询返回的结果,请你重新排版其中信息，使它美观。
                    NOTE:If the query result is empty, return "None".
                    以下是图谱查询结果:{kg_results}。
                    """


# 答案生成prompt, 含human 和 system 两部分message
ANSWER_GENERATION_PROMPT_SYSTEM= "已知您和人类的聊天记录:{history}"
ANSWER_GENERATION_PROMPT_HUMAN =  """
                            问题:"{query}"。以下是从知识图谱中返回的问题相关信息:{kg_infomation}。
                            请你先考虑信息,再结合自身的能力和知识回答问题。
                            NOTE:
                            若知识图谱的信息为None，则根据自身直接回答无需考虑知识图谱.
                            若知识图谱的信息帮助非常小，则根据自身直接回答无需考虑知识图谱.
                            回答时不必指出获取的知识图谱信息来自人类.
                            """

REWRITE_QUERY_PROMPT =  """
                                根据你的记忆,对我提出的问题进行改写,改写的需求如下:
                                有多少个问题则改写多少个问题.
                                若无记忆或者记忆为空,则不用进行任何改写,直接返回我的原问题即可.
                                如果有指代词,则利用你记忆的上下文将指代词具体化.
                                对于指代词具体化的例子:我们在上次对话聊到歌曲《XXX》,当我接着提出"这首歌"的时候,你应该把"这首歌"变为"XXX".对于指代词的处理,利用好你的记忆.
                                如果指代词具体化后与上下文中某一实体有较为密切的联系/关系,需要你做一定的处理,处理的两个例子:例如我们在上次对话聊到歌曲《XXX》的时候,上下文
                                中说明了这首歌曲的作者YYY,当我接着提出"这首歌",你应该把"这首歌"变为"YYY的XXX";再例如我们在上次提到女人BBB，上下文中说明了这个人的丈夫是AAA
                                当我接着提出"这个女人",你应该把"这个女人"变为"AAA的妻子BBB".
                                指代词具体化还需要注意的是，当我提到"这些XX"，你需要根据上下文记忆把"这些XX"具体化为具体的每一项，这些代词指向的东西应该是不止一项的，
                                你需要把"这些XX"改写为每一个名词或者定义词这样的东西上，然后改写就可以得到一系列名词或者定义词，请不要认为这很麻烦.
                                当问题的句子结构,用语,询问目的等等不清晰,可进行改写.
                                若原句清晰,无任何模糊词、指代词等等,则不需要改写,直接返回我的原问题即可.
                                改写不能使得原意曲解.
                                改写幅度应该适当,不应过大.
                                若存在指代词无法改写,则保留指代词.
                                若没有改写,返回原问题即可,不要有其他信息;若有改写,返回改写后的问题即可,不要有其他信息.                      
                        记忆：{history},
                        提问：{query}
                        """

###  使用Prompt格式化图谱的schema
REFORMATTED_SCHEMA = """
        Reformat the following information I provided about graph relationships and nodes to make it aesthetically pleasing and easy for large models to understand. Format the data and reduce line breaks, with one node per line. Also, ensure that your representation does not include curly braces '{}' and that you do not return any information other than the formatted data. 
        Here are three examples of the formatting:
        For nodes, it should be: Instrument: name (STRING), update_time (INTEGER)
        For relationships, it should be: (:Song)-[:R_HasLabel]->(:Label)
        For relationship properties, it should be: R_HasLabel: update_time (INTEGER)
        
        Please follow my examples for formatting and remeber to label which are nodes, which are relationships, and which are the attributes of the relationships. 
        Here is my information:
        """
