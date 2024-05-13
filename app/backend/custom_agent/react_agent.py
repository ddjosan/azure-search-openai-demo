from langchain_openai import AzureChatOpenAI
import os
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor, load_tools
from langchain_core.messages import AIMessage, HumanMessage, ChatMessage, SystemMessage, FunctionMessage, ToolMessage
from langchain.tools.retriever import create_retriever_tool

#from langchain_community.retrievers.azure_ai_search import AzureAISearchRetriever

from retreivers.azure_ai_search import AzureAISearchRetriever
from retreivers.azure_ai_search_prodoc import AzureAISearchRetriever as AzureAISearchProgress
from retreivers.azure_ai_search_progress import  AzureAISearchRetriever as AzureAISearchProdoc
from langchain_core.prompts import SystemMessagePromptTemplate, PromptTemplate, HumanMessagePromptTemplate
import typing


# Parse the environment variables
try:
    azure_openai_api_version = os.environ['AZURE_OPENAI_API_VERSION']
    azure_openai_endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
    azure_openai_api_key = os.environ['AZURE_OPENAI_API_KEY']
    azure_openai_deployment_name = os.environ['AZURE_OPENAI_CHATGPT_DEPLOYMENT']

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

retriever_prodoc = AzureAISearchProdoc(content_key="content", 
                                   service_name=azure_search_service, 
                                   index_name=azure_search_index, 
                                   api_key=azure_search_key,
                                   top_k=15)

# Tool name and tool description are what the AGENT is going to see.
# Based on this information the agent knows which tools to use for a given query
tool_name_prodoc = "search_undp_project_documents"
tool_description_prodoc = "Searches and returns excerpts from UNDP Serbia Country Office project documents. Consult this database when looking for project plans and background."

# Create a retriever tool
undp_search_project_documents = create_retriever_tool(retriever_prodoc, 
                                         tool_name_prodoc, 
                                         tool_description_prodoc)


# Retriever is the functionality to search and retrieve documents based on an input query
retriever_progress = AzureAISearchProgress(content_key="content", 
                                   service_name=azure_search_service, 
                                   index_name=azure_search_index, 
                                   api_key=azure_search_key,
                                   top_k=15)

# Tool name and tool description are what the AGENT is going to see. 
# Based on this information the agent knows which tools to use for a given query
tool_name_progress = "search_undp_progress_reports"
tool_description_progress = "Searches and returns excerpts from UNDP Serbia Country Office progress reports. Consult this database when interested in project results and impact."

# Create a retriever tool
undp_search_progress_reports = create_retriever_tool(retriever_progress, 
                                         tool_name_progress, 
                                         tool_description_progress)



agent_tools = []

# Assuming undp_search_prodocs and undp_search_progress are defined as shown previously
agent_tools.append(undp_search_project_documents)
agent_tools.append(undp_search_progress_reports)

# # Initialize Azure AI Search Retriever
# retriever_indicator = AzureAISearchRetriever(
#     content_key="content",
#     service_name=azure_search_service,
#     index_name="index-csv",
#     api_key=azure_search_key,
#     top_k=5
# )


# Memory key is used to allow the agent to preserve the chat history and understand questions based on context
MEMORY_KEY = "chat_history"

# System prompt is setting the agents role and what it can do
system_prompt = "You are very powerful assistant which helps users explore their documents."


react_prompt = """
Respond to the human as helpfully and accurately as possible. You have access to the following tools:

{tools}

Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).

Valid "action" values: "Final Answer" or {tool_names}

Provide only ONE action per $JSON_BLOB, as shown:

```
{{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}}
```

Follow this format:

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
Begin! Reminder to ALWAYS respond with a valid $JSON_BLOB of a single action. Use tools if necessary.
"""

input_variables=['agent_scratchpad', 'input', 'tool_names', 'tools'] 
input_types={'chat_history': typing.List[typing.Union[
    AIMessage, 
    HumanMessage, 
    ChatMessage, 
    SystemMessage, 
    FunctionMessage, 
    ToolMessage]]}


messages=[
    SystemMessagePromptTemplate(prompt=PromptTemplate(input_variables=['tool_names', 'tools'], template=react_prompt)), 
    MessagesPlaceholder(variable_name='chat_history', optional=True), 
    HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['agent_scratchpad', 'input'], 
                                                     template='{input}\n\n{agent_scratchpad}\n (reminder to respond in a JSON blob no matter what)'))]
agent_template = ChatPromptTemplate(messages=messages, input_variables=input_variables, input_types=input_types)





# Agent scratchpad is used to store the intermediate steps of the agent
scratchpad = "agent_scratchpad"

llm_with_tools = llm.bind_tools(agent_tools)

# Create an agent with its LLM and overall structure
agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: x["chat_history"], 
        "tools": lambda x: agent_tools, 
        "tool_names": lambda x: [tool.name for tool in agent_tools],
    }
    | agent_template
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=agent_tools, verbose=True, handle_parsing_errors=True)


def react_agent(input_text, chat_history):
    return agent_executor.invoke({"input": input_text, "chat_history": chat_history})["output"]


