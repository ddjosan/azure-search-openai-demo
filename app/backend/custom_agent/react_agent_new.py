from langchain_openai import AzureChatOpenAI
import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor, load_tools
from langchain_core.messages import AIMessage, HumanMessage, ChatMessage, SystemMessage, FunctionMessage, ToolMessage
from langchain.tools.retriever import create_retriever_tool
from retreivers.azure_ai_search_progress import AzureAISearchRetriever as AzureAISearchProgress
from retreivers.azure_ai_search_prodoc import AzureAISearchRetriever as AzureAISearchProdoc
import typing
from langchain_core.prompts import SystemMessagePromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

import os
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import StructuredTool
from langchain_community.retrievers import AzureAISearchRetriever
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from typing import Optional

from langchain import hub

from langchain.agents import AgentExecutor, create_structured_chat_agent, load_tools

try:
    azure_openai_api_version = os.environ['AZURE_OPENAI_API_VERSION']
    azure_openai_endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
    azure_openai_api_key = os.environ['AZURE_OPENAI_API_KEY']
    azure_openai_deployment_name = os.environ['AZURE_OPENAI_CHATGPT_DEPLOYMENT']

    azure_search_service = os.environ['AZURE_SEARCH_SERVICE']
    azure_search_index = os.environ['AZURE_SEARCH_INDEX']
    azure_search_key = os.environ['AZURE_SEARCH_KEY']

    openai_model = os.environ['OPENAI_MODEL']
    openai_key = os.environ['OPENAI_KEY']
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

# Basic LLM which will do the thinking and talking
llm = ChatOpenAI(
    temperature=1,
    model=openai_model,
    api_key=openai_key,
    openai_organization=openai_organization
)

# Load UNDP Serbia Country Office project documents retriever tool

# Retriever is the functionality to search and retrieve documents based on an input query
retriever_prodoc = AzureAISearchProdoc(content_key="content", 
                                   service_name=azure_search_service, 
                                   index_name=azure_search_index, 
                                   api_key=azure_search_key,
                                   top_k=30)

# Tool name and tool description are what the AGENT is going to see. 
# Based on this information the agent knows which tools to use for a given query
# tool_name_prodoc = "search_undp_project_documents"
# tool_description_prodoc = "Searches and returns excerpts from UNDP Serbia Country Office project documents. Consult this database when looking for planned project outputs and intervention background. Contains no information on impacts, results, or managers."

# Create a retriever tool
# undp_search_project_documents = create_retriever_tool(retriever_prodoc, 
#                                          tool_name_prodoc, 
#                                          tool_description_prodoc)

# Load UNDP Serbia Country Office project documents retriever tool

# Retriever is the functionality to search and retrieve documents based on an input query
retriever_progress = AzureAISearchProgress(content_key="content", 
                                   service_name=azure_search_service, 
                                   index_name=azure_search_index, 
                                   api_key=azure_search_key,
                                   top_k=30)

# Tool name and tool description are what the AGENT is going to see. 
# Based on this information the agent knows which tools to use for a given query
# tool_name_progress = "search_undp_progress_reports"
# tool_description_progress = "Searches and returns excerpts from UNDP Serbia Country Office progress reports. Consult this if more in depth information is required on project progress."

# Create a retriever tool
# undp_search_progress_reports = create_retriever_tool(retriever_progress, 
#                                          tool_name_progress, 
#                                          tool_description_progress)


# Initialize Azure AI Search Retriever
retriever_indicator = AzureAISearchRetriever(
    content_key="content",
    service_name=azure_search_service,
    index_name="index-csv",
    api_key=azure_search_key,
    top_k=50
)

class SearchInput(BaseModel):
    query: str = Field(description="A query string to be enhanced and processed.")

# def enhanced_search(query: str) -> str:
#     """
#     This function enhances the input query using a predefined prompt with Azure OpenAI.
#     It returns the enhanced query for testing purposes or the search results when uncommented.
#     """
#     # Define the prompt template with the query
#     prompt_template = f"""
#         Enhance the following query to better match the pattern in the searched database.

#         Instructions:
#         1. Identify Keywords and Concepts:
#            - Classify references into the following categories and their types:
#              * "Key Activity Area": ["Policy Support", "Advocacy", "Digital Product Development and Design", "Infrastructure Development and Support", "Public Awareness Raising", "Capacity Building", "Skills Building", "Studies, Research and Analyses", "Experimentation, Testing and Piloting", "Investment Attraction and Facilitation", "Challenge Calls", "Technical Assistance and Advisory Services", "Partnership Building", "Networks and Platform Creation", "Fundraising and Resource Mobilization", "Other"]
#              * "Supported Entities (Category)": ["Government Ministries and Departments", "Parliament and Legislative Bodies", "Central Government Agencies and Offices", "Judiciary System Entities", "Other Governmental Entities", "Local Self Governments (LSGs)", "Educational Institutions", "Research Institutions and Universities", "Healthcare Institutions and Services", "Civil Society Organizations (CSOs) and Non-Governmental Organizations (NGOs)", "Other"]
#              * "Target Beneficiaries": ["Youth and Children", "Elderly and Vulnerable Adults", "Gender-Based Groups", "Occupational Groups", "Government and Public Service", "Mobility and Migration", "Economic Status Groups", "Geographical Communities", "Environmental and Volunteer Groups", "General Public"]

#         2. Translate Keywords to Schema Patterns:
#            - Map identified keywords and phrases to corresponding JSON schema patterns, ensuring:
#              * "Key Activity Area", "Supported Entities (Names)", "Supported Entities (Category)", "Target Beneficiaries", "Activity Name", "Activity Description", "Output", "Impact" fields are correctly matched to the data.
#            - If more than one schema pattern is appropriate, add them:

#         3. Pattern Completion:
#            - Ensure all relevant details from the original query are translated into the structured format according to the schema:
#              * Include the appropriate categories.
#              * Multiple categories can be added.
#              * Maintain all pertinent information from the original query in the transformed response.
#              * DO NOT INVENT ANY INFORMATION in your response, ONLY STICK TO WHAT IS PROVIDED IN THE ORIGNAL QUERY.

#         Examples:

#         User Query: 'Can you provide details on the strategy sessions with the envornoment Ministry for the Green Agenda in September 2022?'
#         Your response:
#         'Can you provide details on the strategy sessions with the envornoment Ministry for the Green Agenda in September 2022?, Key Activity Area: Policy Support, Supported Entities (Names): Ministry for Environmental Protection, Supported Entities (Category): Government Ministries and Departments, Activity Name: Development of the Green Agenda Strategy, Year: 2022'

#         User Query: "What measures are being implemented for improving surveillance at Serbian Railways in 2023?"
#         Your response:
#         'What measures are being implemented for improving surveillance at Serbian Railways in 2023?, Key Activity Area: Digital Product Development and Design, Supported Entities (Names): Serbian Railways, Supported Entities (Category): Other Governmental Entities, Activity Name: Computer Vision detection of people in restricted areas, Year: 2023'

#         User Query: "What capacity building efforts involved the Ministry of Interior in the firearms misuse prevention project?"
#         Your response:
#         "What capacity building efforts involved the Ministry of Interior in the firearms misuse prevention project?, Key Activity Area: Capacity Building, Supported Entities (Names): Ministry of Interior, Supported Entities (Category): Government Ministries and Departments"

#         PROVIDE ONLY ONE RESPONSE.
#         DO NOT ADD ANY INFORMATION NOT INCLUDED IN THE ORIGINAL QUERY.

#         User Query: {query}
#         Your response:
#         """
    
#     # Enhance the query using Azure OpenAI
#     message = HumanMessage(content=prompt_template)
#     response = openai_model_000.invoke([message])
#     enhanced_query = response.content
#     print(enhanced_query)
#     # Uncomment the following line to call the retriever
#     # search_results = retriever_inidicator.invoke(enhanced_query)
    
#     # Comment/uncomment the appropriate line below depending on your use case
#     # return search_results
#     return enhanced_query

def processed_search(original_query: str, query_result: list) -> str:
    # Define the prompt template with the query
#     prompt_result = f"""
#         Take the following query Results:\n\m
        
#         {query_result}\n\m
        
#         Each Result is followed by the reference document, indicated by the following pattern: 'Document Name: [Reference Document.docx]'.\n\n 
        
#         Now go over each of the Results, and keep those Results that are relevant to the following query.\n\n 

#         {original_query}\n\n 
        
#         Output Processing Instructions:\n 
#         - Retain ALL information from each of the retained Results in your output.\n 
#         - Present the retained Results in a systematic and organized manner.\n 
#         - Present the results in plain text, do not use markdown.\n 
#         - Always reference the Document Name of each retained result in brackets, for instance [Report_Cited.docx].\n 
#         - List each reference separately [document_reference.docx][resultworkbook.xlsx].\n 
#         """
#     message = HumanMessage(content=prompt_result)
#     response = llm.invoke([message])
#     processed_response = response.content
    result = str(query_result) + "\n\nIf you use the above results in the Final Answer always include the accompanying source Document Name, or sourcefile, in square brackets immediately after. So if you for instance read 'Document Name: [reference_document.docx]' or 'sourcefile': 'reference_document.docx' it becomes [reference_document.docx]. Always list each referenced document separately in its own square brackets, so two relevant references in a row will be [Report outline.docx][Financial Results Q3.xlsx]. Do not use markdown in Final Answer, just plain text."
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
tools = []



prompt = hub.pull("hwchase17/structured-chat-agent")

tools = load_tools(["llm-math"], llm=llm)
tools.append(undp_search_project_documents_tool)
tools.append(undp_search_progress_reports_tool)
tools.append(undp_search_impact_indicator)


# Construct the JSON agent
agent = create_structured_chat_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent, tools=tools, verbose=True, handle_parsing_errors=True
)

def react_agent(input_text, chat_history):
    response = agent_executor.invoke({"input": input_text, "chat_history": chat_history})
    return response["output"]