from langchain_openai import AzureChatOpenAI
import os
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage
from langchain.tools.retriever import create_retriever_tool
from langchain_community.retrievers.azure_ai_search import AzureAISearchRetriever


# Parse the environment variables
try:
    azure_openai_api_version = os.environ['AZURE_OPENAI_API_VERSION']
    azure_openai_endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
    azure_openai_api_key = os.environ['AZURE_OPENAI_API_KEY']
    azure_openai_deployment_name = "chat"

    azure_search_service = os.environ['AZURE_SEARCH_SERVICE']
    azure_search_index = os.environ['AZURE_SEARCH_INDEX']
    azure_search_key = os.environ['AZURE_SEARCH_KEY']
except KeyError:
    azure_openai_api_version = ""
    azure_openai_endpoint = ""
    azure_openai_api_key = ""
    azure_openai_deployment_name = ""

    azure_search_service = ""
    azure_search_index = ""
    azure_search_key = ""
    raise

llm = AzureChatOpenAI(deployment_name=azure_openai_deployment_name, 
                      openai_api_version=azure_openai_api_version,
                      azure_endpoint=azure_openai_endpoint,
                      openai_api_key=azure_openai_api_key)

retriever = AzureAISearchRetriever(content_key="content",
                                   service_name=azure_search_service,
                                   index_name=azure_search_index,
                                   api_key=azure_search_key,
                                   top_k=15)

# Tool name and tool description are what the AGENT is going to see.
# Based on this information the agent knows which tools to use for a given query
tool_name = "search_undp_project_docs"
tool_description = "Searches and returns excerpts from UNDP Serbia Country Office project documents (prodocs)"

# Create a retriever tool
undp_search_tool = create_retriever_tool(retriever,
                                         tool_name,
                                         tool_description)

agent_tools = [undp_search_tool]

# Memory key is used to allow the agent to preserve the chat history and understand questions based on context
MEMORY_KEY = "chat_history"

# System prompt is setting the agents role and what it can do
system_prompt = "You are very powerful assistant which helps users explore their documents."

# Agent scratchpad is used to store the intermediate steps of the agent
scratchpad = "agent_scratchpad"

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            system_prompt,
        ),
        MessagesPlaceholder(variable_name=MEMORY_KEY),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name=scratchpad),
    ]
)

llm_with_tools = llm.bind_tools(agent_tools)

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: x["chat_history"]
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=agent_tools, verbose=True)


def react_agent(input_text, chat_history):
    return agent_executor.invoke({"input": input_text, "chat_history": chat_history})["output"]


