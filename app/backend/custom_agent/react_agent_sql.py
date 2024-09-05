import os

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts import SystemMessagePromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, ChatMessage, SystemMessage, FunctionMessage, ToolMessage
from langchain.pydantic_v1 import BaseModel, Field
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor, load_tools
from retreivers.azure_ai_search_progress import AzureAISearchRetriever as AzureAISearchProgress
from retreivers.azure_ai_search_prodoc import AzureAISearchRetriever as AzureAISearchProdoc
from langchain_community.retrievers import AzureAISearchRetriever
from langchain.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey
from langchain_community.utilities import SQLDatabase

import typing
from typing import Optional
from langchain_core.messages import SystemMessage
from langchain_community.agent_toolkits import SQLDatabaseToolkit

from langchain_community.vectorstores import FAISS
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain_openai import OpenAIEmbeddings
import ast
import re

from langgraph.checkpoint import MemorySaver

try:
    azure_openai_api_version = os.environ['AZURE_OPENAI_API_VERSION']
    azure_openai_endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
    azure_openai_api_key = os.environ['AZURE_OPENAI_API_KEY']
    azure_openai_deployment_name = os.environ['AZURE_OPENAI_CHATGPT_DEPLOYMENT']

    azure_search_service = os.environ['AZURE_SEARCH_SERVICE']
    azure_search_index = os.environ['AZURE_SEARCH_INDEX']
    azure_search_key = os.environ['AZURE_SEARCH_KEY']

    openai_model = os.environ['OPENAI_MODEL']
    openai_key = os.environ['OPENAI_API_KEY']
    openai_organization = os.environ['OPENAI_ORGANIZATION']

except KeyError:
    azure_openai_api_version = ""
    azure_openai_endpoint = ""
    azure_openai_api_key = ""
    azure_openai_deployment_name = ""

    azure_search_service = ""
    azure_search_index = ""
    azure_search_key = ""
    raise

# Create the SQLite database
engine = create_engine('sqlite:///datasource/undp_serbia_companion_new5.db')

db = SQLDatabase(engine)


# Basic LLM which will do the thinking and talking
llm = ChatOpenAI(
    temperature=1,
    model=openai_model,
    api_key= openai_key,
    openai_organization=openai_organization
)


# SQL_PREFIX = """
# You are an agent designed to interact with a SQL database.
# Given an input question, create a syntactically correct SQLite query to run, then look at the results and return the answer.
# Order the results by a relevant column to highlight the most interesting examples.
# Never query for all columns from a table; only request relevant columns based on the question.
# Always return all results of the query.
# Avoid returning IDs.
# You have tools to interact with the database; use only these tools and the information they return to construct your answer.
# Double-check your query before execution. If an error occurs, rewrite the query and try again.

# DO NOT perform any DML statements (INSERT, UPDATE, DELETE, DROP, etc.).

# If you need to filter on a proper noun, you must ALWAYS first look up the filter value using the "search_proper_nouns" tool, but proper noun use ONLY for database search!
# To answer a user query, ALWAYS first try finding the answer using SQL database tool, 
# and only after use tools: [undp_search_project_documents, undp_serbia_project_activity_and_result_search] for additional information.

# In case that there are no data in SQL Database, use tools : [search_undp_project_documents, undp_serbia_project_activity_and_result_search] to generate answer.

# If you need to answer some question about some location in Serbia use tools: [search_undp_project_documents, undp_serbia_project_activity_and_result_search] to generate answer.

# To answer a user query:
# 1. ALWAYS start by examining the database tables to understand what you can query.
# 2. Query the schema of the most relevant tables.

# Here are some examples of user inputs and their corresponding SQL queries:


# User input: Can you list me all projects?
# SQL query: SELECT projectName FROM projectDocuments;

# User input: Describe cpd output 2.2 results achieved in 2023
# SQL Query: SELECT * from resultsData r where r.qunatumID in (select quantumID from countryProgrammeDocument where cpdOutputNumber='CPD Output 2.2.' or cpdOutput like '%output 2.2%') and r.progressReportID in ( select progressReportID from progressReports where year='2023')

# User input: Can you give me results achieved in 2023
# SQL Query: Select * from resultsData where progresReportID in ( select progressReportID from progressReports where year='2023')
# """

SQL_PREFIX = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct SQLite query to run, then look at the results and return the answer.
Order the results by a relevant column to highlight the most interesting examples.
Never query for all columns from a table; only request relevant columns based on the question.
Always return all results of the query.
Avoid returning IDs.
You have tools to interact with the database; use only these tools and the information they return to construct your answer.
Double-check your query before execution. If an error occurs, rewrite the query and try again.

DO NOT perform any DML statements (INSERT, UPDATE, DELETE, DROP, etc.).

To answer a user query, ALWAYS first try finding the answer using SQL database tool sql_db_query,
and only after use tools: [search_undp_project_documents, undp_serbia_project_activity_and_result_search] for additional information.

In case that there are no relavant data in SQL Database, ALWAYS use tools : [search_undp_project_documents, undp_serbia_project_activity_and_result_search] to generate answer.

If you need to answer some question about some location in Serbia use tools: [undp_serbia_project_activity_and_result_search] to generate answer.

To answer a user query:
1. ALWAYS start by examining the database tables to understand what you can query.
2. Query the schema of the most relevant tables.


Here are some examples of user inputs and their corresponding SQL queries:


User input: Can you list me all projects?
SQL query: SELECT projectName FROM projectsData;

User input: Describe cpd output 2.2 results achieved in 2023
SQL Query: SELECT * from resultsData r where r.projectID in (select projectID from cpdData where cpdOutputNumber='CPD Output 2.2' or cpdOutputNumber like '%2.2%') and r.year='2023'

User input: Describe output 2.2 results achieved in 2023
SQL Query: SELECT * from resultsData r where r.projectID in (select projectID from cpdData where cpdOutputNumber='CPD Output 2.2' or cpdOutputNumber like '%2.2%') and r.year='2023'

User input: Describe cpd output 2.2 results achieved in 2023
SQL Query: SELECT * from resultsData r where r.projectID in (select projectID from cpdData where cpdOutputNumber='CPD Output 2.2' or cpdOutputNumber like '%2.2%') and r.year='2023'

User input: Describe suboutput 2.2.1 results achieved in 2023
SQL Query: SELECT * from resultsData r where r.projectID in (select projectID from cpdData where cpdSubOutputNumber='CPD Sub Output 2.2.1' or cpdSubOutputNumber like '%2.2.1%') and r.year='2023'


User input: Can you give me results achieved in 2023
SQL Query: Select * from resultsData where year='2023'

User input: Can you list me all the UNDP partners?
SQL Query: Select distinct(nationalPartner) from projectsData

User input: Can you list me all donors?
SQL Query: Select distinct(donor) from projectsData

User input: Can you list me all grants?
SQL Query: Select * from programmaticAgreementsData where programmaticAgreementType='Grant'

User input: Can you list me all performance based payments?
SQL Query: Select * from programmaticAgreementsData where programmaticAgreementType='Performance Based Payment'

User input: Can you list me all innovation award agreements?
SQL Query: Select * from programmaticAgreementsData where programmaticAgreementType='Innovation Award Agreement'

User input: Can you list me all responsible party agreements?
SQL Query: Select * from programmaticAgreementsData where programmaticAgreementType='Responsible Party Agreement'

"""

system_message = SystemMessage(content=SQL_PREFIX)




#def query_as_list(db, query):
#    res = db.run(query)
#    res = [el for sub in ast.literal_eval(res) for el in sub if el]
#    res = [re.sub(r"\b\d+\b", "", string).strip() for string in res]
#    return list(set(res))

#projects = query_as_list(db, "SELECT projectName FROM projectIdentifier")
#cpd_output = query_as_list(db, "SELECT cpdOutput FROM countryProgrammeDocument")
#cpd_suboutput = query_as_list(db, "SELECT cpdSubOutput FROM countryProgrammeDocument")
#cpd_outcome = query_as_list(db, "SELECT cpdOutcome FROM countryProgrammeDocument")
#cpd_outputnumber = query_as_list(db, "SELECT cpdOutputNumber FROM countryProgrammeDocument")
#cpd_outcomenumber = query_as_list(db, "SELECT cpdOutcomeNumber FROM countryProgrammeDocument")
#cpd_suboutputnumber = query_as_list(db, "SELECT cpdSubOutputNumber FROM countryProgrammeDocument")

#vector_db = FAISS.from_texts(projects+cpd_output+cpd_suboutput+cpd_outcome+cpd_outputnumber+cpd_outcomenumber+cpd_suboutputnumber, OpenAIEmbeddings(api_key= openai_key,
#    openai_organization=openai_organization))
#retriever = vector_db.as_retriever(search_kwargs={"k": 5})
# description = """Use to look up values to filter on. Input is an approximate spelling of the proper noun, output is \
# valid proper nouns. Use the noun most similar to the search."""
# noun_retriever_tool = create_retriever_tool(
#     retriever,
#     name="search_proper_nouns",
#     description=description,
# )

# Load UNDP Serbia Country Office project documents retriever tool

# Retriever is the functionality to search and retrieve documents based on an input query
retriever_prodoc = AzureAISearchProdoc(content_key="content", 
                                   service_name=azure_search_service, 
                                   index_name=azure_search_index, 
                                   api_key=azure_search_key,
                                   top_k=20)

# Retriever is the functionality to search and retrieve documents based on an input query
retriever_progress = AzureAISearchProgress(content_key="content", 
                                   service_name=azure_search_service, 
                                   index_name=azure_search_index, 
                                   api_key=azure_search_key,
                                   top_k=20)

# Load UNDP Serbia Country Office resutls and activites retriever tool
retriever_indicator = AzureAISearchRetriever(
    content_key="content",
    service_name=azure_search_service,
    index_name="index-csv",
    api_key=azure_search_key,
    top_k=20
)

class SearchInput(BaseModel):
    query: str = Field(description="A query string to be enhanced and processed.")

def processed_search(original_query: str, query_result: list) -> str:
    result = str(query_result) + "\n\nIf you use the above results in the Final Answer always include the accompanying source Document Name, or sourcefile, in square brackets immediately after. So if you for instance read 'Document Name: [reference_document.docx]' or 'sourcefile': 'reference_document.docx' it becomes [reference_document.docx]. Always list each referenced document separately in its own square brackets, so two relevant references in a row will be [Report outline.docx][Financial Results Q3.xlsx]. Always list sources next to their context, never seperately."
    return result


def enhanced_and_processed_search(query: str) -> str:
    search_results = retriever_indicator.invoke(query)
    processed_output = processed_search(query, search_results)
    return processed_output

undp_search_impact_indicator = StructuredTool.from_function(
    func=enhanced_and_processed_search,
    name="undp_serbia_project_activity_and_result_search",
    description="A tool for finding key project activties, impacts, and results, categorized by area of focus, beneficiaries, responsible project mangers, and other organziational metadata.",
    args_schema=SearchInput,
    return_direct=False
)

# Wrapping the first retriever (project documents) into a function
def search_undp_project_documents(query: str) -> str:
    search_results = retriever_prodoc.invoke(query)
    processed_output = processed_search(query, search_results)  # Assuming `processed_search` is defined similarly
    return processed_output

# Creating the StructuredTool for project documents
undp_search_project_documents_tool = StructuredTool.from_function(
    func=search_undp_project_documents,
    name="search_undp_project_documents",
    description="Searches and returns excerpts from UNDP Serbia Country Office project documents. Consult this database when looking for planned project outputs and intervention background. Contains no information on impacts, results, or managers.",
    args_schema=SearchInput,
    return_direct=False
)

# Wrapping the second retriever (progress reports) into a function
def search_undp_progress_reports(query: str) -> str:
    search_results = retriever_progress.invoke(query)
    processed_output = processed_search(query, search_results)  # Assuming `processed_search` is defined similarly
    return processed_output

# Creating the StructuredTool for progress reports
undp_search_progress_reports_tool = StructuredTool.from_function(
    func=search_undp_progress_reports,
    name="search_undp_progress_reports",
    description="Searches and returns excerpts from UNDP Serbia Country Office progress reports. Consult this if more in depth information is required on project progress.",
    args_schema=SearchInput,
    return_direct=False
)


toolkits = SQLDatabaseToolkit(db=db, llm=llm)

tools_extended = toolkits.get_tools()

#tools_extended.append(noun_retriever_tool)
tools_extended.append(undp_search_project_documents_tool)
#tools_extended.append(undp_search_progress_reports_tool)
tools_extended.append(undp_search_impact_indicator)


memory = MemorySaver()
#config = {"configurable": {"thread_id": "thread-1"}}

#print(memory)

# Construct the JSON agent
agent_executor_mixed = create_react_agent(llm, tools_extended, state_modifier=system_message, checkpointer=MemorySaver())

def react_agent(input_text, chat_history, chat_id):

    config = {"recursion_limit": 50, "configurable": {"thread_id": chat_id}}
    #config = {"configurable": {"thread_id": "1"}}

    for s in agent_executor_mixed.stream(
        {"messages": input_text}, config
    ):
        print(s)
        print("----")
    return s['agent']['messages'][0].content