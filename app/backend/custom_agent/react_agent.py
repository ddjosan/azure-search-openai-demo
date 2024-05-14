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

#from langchain_community.retrievers.azure_ai_search import AzureAISearchRetriever

from retreivers.azure_ai_search import AzureAISearchRetriever
from retreivers.azure_ai_search_prodoc import AzureAISearchRetriever as AzureAISearchProgress
from retreivers.azure_ai_search_progress import  AzureAISearchRetriever as AzureAISearchProdoc
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



# Initialize AzureChatOpenAI models
openai_model_000 = AzureChatOpenAI(
    openai_api_version=azure_openai_api_version,
    azure_deployment=azure_openai_deployment_name,
    temperature=0,
)

openai_model_025 = AzureChatOpenAI(
    openai_api_version=azure_openai_api_version,
    azure_deployment=azure_openai_deployment_name,
    temperature=0.25,
)

# Initialize Azure AI Search Retriever
retriever_indicator = AzureAISearchRetriever(
    content_key="content",
    service_name=azure_search_service,
    index_name="index-csv",
    api_key=azure_search_key,
    top_k=10
)

class SearchInput(BaseModel):
    query: str = Field(description="A query string to be enhanced and processed.")


def enhanced_search(query: str) -> str:
    """
    This function enhances the input query using a predefined prompt with Azure OpenAI.
    It returns the enhanced query for testing purposes or the search results when uncommented.
    """
    # Define the prompt template with the query
    prompt_template = f"""
        Enhance the following query to better match the pattern in the searched database.

        Instructions:
        1. Identify Keywords and Concepts:
           - Classify references into the following categories and their types:
             * "Key Activity Area": ["Policy Support", "Advocacy", "Digital Product Development and Design", "Infrastructure Development and Support", "Public Awareness Raising", "Capacity Building", "Skills Building", "Studies, Research and Analyses", "Experimentation, Testing and Piloting", "Investment Attraction and Facilitation", "Challenge Calls", "Technical Assistance and Advisory Services", "Partnership Building", "Networks and Platform Creation", "Fundraising and Resource Mobilization", "Other"]
             * "Supported Entities (Category)": ["Government Ministries and Departments", "Parliament and Legislative Bodies", "Central Government Agencies and Offices", "Judiciary System Entities", "Other Governmental Entities", "Local Self Governments (LSGs)", "Educational Institutions", "Research Institutions and Universities", "Healthcare Institutions and Services", "Civil Society Organizations (CSOs) and Non-Governmental Organizations (NGOs)", "Other"]
             * "Target Beneficiaries": ["Youth and Children", "Elderly and Vulnerable Adults", "Gender-Based Groups", "Occupational Groups", "Government and Public Service", "Mobility and Migration", "Economic Status Groups", "Geographical Communities", "Environmental and Volunteer Groups", "General Public"]

        2. Translate Keywords to Schema Patterns:
           - Map identified keywords and phrases to corresponding JSON schema patterns, ensuring:
             * "Key Activity Area", "Supported Entities (Names)", "Supported Entities (Category)", "Target Beneficiaries", "Activity Name", "Activity Description", "Output", "Impact" fields are correctly matched to the data.
           - If more than one schema pattern is appropriate, add them:

        3. Pattern Completion:
           - Ensure all relevant details from the original query are translated into the structured format according to the schema:
             * Include the appropriate categories.
             * Multiple categories can be added.
             * Maintain all pertinent information from the original query in the transformed response.
             * DO NOT INVENT ANY INFORMATION in your response, ONLY STICK TO WHAT IS PROVIDED IN THE ORIGNAL QUERY.

        Examples:

        User Query: 'Can you provide details on the strategy sessions with the envornoment Ministry for the Green Agenda in September 2022?'
        Your response:
        'Can you provide details on the strategy sessions with the envornoment Ministry for the Green Agenda in September 2022?, Key Activity Area: Policy Support, Supported Entities (Names): Ministry for Environmental Protection, Supported Entities (Category): Government Ministries and Departments, Activity Name: Development of the Green Agenda Strategy, Year: 2022'

        User Query: "What measures are being implemented for improving surveillance at Serbian Railways in 2023?"
        Your response:
        'What measures are being implemented for improving surveillance at Serbian Railways in 2023?, Key Activity Area: Digital Product Development and Design, Supported Entities (Names): Serbian Railways, Supported Entities (Category): Other Governmental Entities, Activity Name: Computer Vision detection of people in restricted areas, Year: 2023'

        User Query: "What capacity building efforts involved the Ministry of Interior in the firearms misuse prevention project?"
        Your response:
        "What capacity building efforts involved the Ministry of Interior in the firearms misuse prevention project?, Key Activity Area: Capacity Building, Supported Entities (Names): Ministry of Interior, Supported Entities (Category): Government Ministries and Departments"

        PROVIDE ONLY ONE RESPONSE.
        DO NOT ADD ANY INFORMATION NOT INCLUDED IN THE ORIGINAL QUERY.

        User Query: {query}
        Your response:
        """
    
    # Enhance the query using Azure OpenAI
    message = HumanMessage(content=prompt_template)
    response = openai_model_000.invoke([message])
    enhanced_query = response.content
    print(enhanced_query)
    # Uncomment the following line to call the retriever
    # search_results = retriever_inidicator.invoke(enhanced_query)
    
    # Comment/uncomment the appropriate line below depending on your use case
    # return search_results
    return enhanced_query

def processed_search(original_query: str, query_result: str) -> str:
    
    # Define the prompt template with the query
    prompt_result = f"""
        Below is a set of search results on the following user query: 
        
        # USER QUERY
        
        {original_query}
        
        Your task is to analyze these search results, select the relevant ones, and synthesize them into a response.

        # SEARCH RESULTS:

        {query_result}

        # INSTRUCTIONS:

        You are to analyze the user's query, and every search result listed above for relevance to it. Discard those results which do not answer the query. For the remaining results, the instructions are as follows: 

        1. Provide an overview of all impactsm, without skipping any of the results, focusing on measurable and quantifiable data. Use the title *Overview of actvities - [title of topic]*.

        2. Include a reference for each impact using the format: ["Report on Topic.pdf"], derived from the "Document Name" field in each result.

        3. If multiple search results share a common impact, aggregate them and provide separate references for each, e.g., [word_document.docx][Spread Sheet 2114.xlsx].

        4. Present the analysis in two sections:
           a. *Overview of actvities - [title of topic]*: Provide a detailed overview of all relevant activities, including references for each activity, ensuring proper attribution. Make sure that this list is as long as it needs to be to cover every relevant search result.
           b. *Overall impact*: Aggregate the impacts where possible, giving quantifiable and measurable insights, and include separate references for each source.

        5. Adhere strictly to the information provided in the search results. Avoid making assumptions or interpolating information. If there is insufficient data to answer fully, indicate this clearly.

        6. PROCESS ALL SEARCH RESULTS, ONLY CONSOLIDATE RELATED ONES. 
        
        7. CONSIDER THE ORIGINAL QUERY, IGNORE ALL RESULTS THAT DO NOT RELATE TO ANSWERING ORIGINAL QUERY:
        
        {original_query}

        Make sure every fact is supported by the reference, following the format [Report on Topic.pdf]. Do not use markdown, provide output in plain text.

        # OUTPUT:"""

    # Enhance the query using Azure OpenAI
    message = HumanMessage(content=prompt_result)
    response = openai_model_025.invoke([message])
    processed_response = response.content
    print(processed_response)
    return processed_response

def enhanced_and_processed_search(query: str) -> str:
    """
    Enhances the given query, retrieves results based on the enhanced query,
    and processes these results to provide a detailed analysis.
    """
    #enhanced_query = enhanced_search(query)
    search_results = retriever_indicator.invoke(query)
    processed_output = processed_search(query, search_results)
    return processed_output

undp_search_impact_indicator = StructuredTool.from_function(
    func=enhanced_and_processed_search,
    name="undp_serbia_actvity_and_impact_search",
    description="A tool for finding key activties and impacts and results of projects. Formulate your query to be as specific as possible, you can be elaborate. Returns fully referenced answers.",
    args_schema=SearchInput,
    return_direct=False
)


agent_tools = []

# Assuming undp_search_prodocs and undp_search_progress are defined as shown previously
agent_tools.append(undp_search_project_documents)
agent_tools.append(undp_search_progress_reports)
agent_tools.append(undp_search_impact_indicator)

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
    return agent_executor.invoke({"input": input_text, "chat_history": chat_history, "tools": agent_tools})["output"]


