import os

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts import SystemMessagePromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, ChatMessage, SystemMessage, FunctionMessage, ToolMessage
from langchain.pydantic_v1 import BaseModel, Field
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor, load_tools
from retreivers.azure_ai_search_portfolio import AzureAISearchRetriever

from langchain.tools import StructuredTool
from langchain.tools.retriever import create_retriever_tool

import typing
from typing import Optional

from langchain import hub
from langchain.agents import AgentExecutor, create_structured_chat_agent, load_tools, create_react_agent
from langchain_openai import ChatOpenAI


# Parse the environment variables
try:
    azure_openai_api_version = os.environ['AZURE_OPENAI_API_VERSION']
    azure_openai_endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
    azure_openai_api_key = os.environ['AZURE_OPENAI_API_KEY']
    azure_openai_deployment_name = os.environ['AZURE_OPENAI_CHATGPT_DEPLOYMENT']

    azure_search_service = os.environ['AZURE_SEARCH_SERVICE']
    azure_search_index = os.environ['AZURE_SEARCH_INDEX']
    azure_search_key = os.environ['AZURE_SEARCH_KEY']

    openai_api_key = os.environ['OPENAI_API_KEY']
    openai_model = os.environ['OPENAI_MODEL']
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

llm = ChatOpenAI(
    temperature=0.5,
    model=openai_model,
    api_key= openai_api_key,
    openai_organization=openai_organization
)


# Retriever is the functionality to search and retrieve documents based on an input query
retriever_portfolio = AzureAISearchRetriever(content_key="content", 
                                   service_name=azure_search_service, 
                                   index_name=azure_search_index, 
                                   api_key=azure_search_key,
                                   top_k=35)


class SearchInput(BaseModel):
    query: str = Field(description="A query string to be enhanced and processed.")

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
    result = str(query_result) + "\n\nIf you use the above results in the Final Answer always include the accompanying source Document Name, or sourcepage, in square brackets immediately after. So if you for instance read 'Document Name: [reference_document.pdf#page=40]' or 'sourcepage': 'reference_document.pdf#page=40' it becomes [reference_document.pdf#page=40]. Always list each referenced document separately in its own square brackets, so two relevant references in a row will be [Report outline.docx][Financial Results Q3.pdf#page=21]. Always list sources next to their context, never seperately."
    return result

# Wrapping the first retriever (project documents) into a function
def search_undp_portfolio_apporoach(query: str) -> str:
    search_results = retriever_portfolio.invoke(query)
    processed_output = processed_search(query, search_results)  # Assuming `processed_search` is defined similarly
    return processed_output

# Creating the StructuredTool for project documents
undp_search_portfolio_approach_tool = StructuredTool.from_function(
    func=search_undp_portfolio_apporoach,
    name="search_undp_portfolio_approach_knowledge_base",
    description="Searches and returns excerpts from UNDP's Potfolio Approach knowledge base. Useful for answering questions about the Portfolio Approach and related methods.",
    args_schema=SearchInput,
    return_direct=False
)

prompt = hub.pull("hwchase17/structured-chat-agent")

# Assuming prompt is your ChatPromptTemplate object
existing_template = prompt.messages[0].prompt.template

# Additional string to add
additional_string = "\n\nNever return a JSON object as final answer, use markdown."

# Modify the template
new_template = existing_template + additional_string

# Update the template attribute with the new template
prompt.messages[0].prompt.template = new_template

# Load the tools and add them directly to the list
tools = load_tools(["llm-math"], llm=llm)
tools.append(undp_search_portfolio_approach_tool)

# Construct the JSON agent
agent = create_structured_chat_agent(llm, tools, prompt)

# Create an agent executor by passing in the agent and tools
agent_executor = AgentExecutor(
    agent=agent, tools=tools, verbose=True, handle_parsing_errors=True
)





def react_agent(input_text, chat_history):
    response = agent_executor.invoke({"input": input_text, "chat_history": chat_history})
    return response["output"]


