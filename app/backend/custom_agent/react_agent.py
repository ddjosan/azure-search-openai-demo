from langchain.pydantic_v1 import BaseModel, Field
from langchain_openai import AzureChatOpenAI
import os
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor, load_tools
from langchain_core.messages import AIMessage, HumanMessage, ChatMessage, SystemMessage, FunctionMessage, ToolMessage
from langchain.tools.retriever import create_retriever_tool

from langchain_community.retrievers.azure_ai_search import AzureAISearchRetriever

from langchain_core.prompts import SystemMessagePromptTemplate, PromptTemplate, HumanMessagePromptTemplate
import typing
from typing import Optional
from langchain.tools import StructuredTool


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




# Retriever is the functionality to search and retrieve documents based on an input query
retriever_portfolio = AzureAISearchRetriever(content_key="content", 
                                   service_name=azure_search_service, 
                                   index_name=azure_search_index, 
                                   api_key=azure_search_key,
                                   top_k=15)

# Tool name and tool description are what the AGENT is going to see. 
# Based on this information the agent knows which tools to use for a given query
tool_name_portfolio = "search_undp_portfolio_approach"
tool_description_prortfolio = "Searches and returns excerpts from UNDP Innovation team portfolio approach document. Consult this database when interested in portfolio approach."

# Create a retriever tool
undp_search_portfolio_approach = create_retriever_tool(retriever_portfolio, 
                                         tool_name_portfolio, 
                                         tool_description_prortfolio)



# Initialize AzureChatOpenAI models
# openai_model_000 = AzureChatOpenAI(
#     openai_api_version=azure_openai_api_version,
#     azure_deployment=azure_openai_deployment_name,
#     temperature=0,
# )

# openai_model_025 = AzureChatOpenAI(
#     openai_api_version=azure_openai_api_version,
#     azure_deployment=azure_openai_deployment_name,
#     temperature=0.25,
# )



agent_tools = []

# Assuming undp_search_prodocs and undp_search_progress are defined as shown previously
agent_tools.append(undp_search_portfolio_approach)

# # Initialize Azure AI Search Retriever
# retriever_indicator = AzureAISearchRetriever(
#     content_key="content",
#     service_name=azure_search_service,
#     index_name="index-csv",
#     api_key=azure_search_key,
#     top_k=5
# )

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
Maintain original references to documents in Final Answer [reference_document_name.docx], and provide separate references for each, e.g., [word_document.docx][Spread Sheet 2114.xlsx].
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


llm_with_tools = llm.bind_tools(agent_tools)

# Create an agent with its LLM and overall structure
agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: x["chat_history"], 
        "tools": lambda x: x["tools"],
        "tool_names": lambda x: [tool.name for tool in x["tools"]],
    }
    | agent_template
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=agent_tools, verbose=True, handle_parsing_errors=True)


def react_agent(input_text, chat_history):
    response = agent_executor.invoke({"input": input_text, "chat_history": chat_history, "tools": agent_tools})
    print("-----RESPONSE----")
    print(response)
    return response["output"]


