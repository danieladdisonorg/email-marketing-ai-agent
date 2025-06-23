from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from utils import set_api_key_env, get_text_from_file
from dotenv import load_dotenv
import os
from langchain_openai import OpenAIEmbeddings
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain_astradb import AstraDBVectorStore
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnablePassthrough
from typing import Dict
from send_email import send_emails

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
set_api_key_env("OPENAI_API_KEY", openai_api_key)
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_KEYSPACE = "default_keyspace"

embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=openai_api_key)

llm = ChatOpenAI(model="gpt-4o")

prompt = get_text_from_file("prompt.md")

prompt_template = ChatPromptTemplate([
    ("system", prompt),
    ("user", "Write an email with provided instructions and to the following people based on the instructions provided. You will also recieve context, however, at times the context will be empty. Here is the context: {context}"),
])



embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
email_agent = prompt_template | llm



def parse_retriever_input(params: Dict):
    return params["messages"][-1].content

vector_store = AstraDBVectorStore(
    collection_name="astra_vector_langchain",
    embedding=embeddings,
    api_endpoint=ASTRA_DB_API_ENDPOINT,
    token=ASTRA_DB_APPLICATION_TOKEN,
    namespace=ASTRA_DB_KEYSPACE,
)
# k is the number of chunks to retrieve
retriever = vector_store.as_retriever(k=4)

docs = retriever.invoke("Hashim, Nadeem, hashim@cosmosys.co, CDO, Cosmosys \n Existing customers: Yahya, Qureshi, yahya@ok.co, CEO, ok")
document_chain = create_stuff_documents_chain(llm, prompt_template)

print("Documents retrieved: ",docs)
"""
print(document_chain.invoke(
    {
        "context": docs,
        "messages": [
            HumanMessage(content="FIRST NAME: Hashim\n,SEOND NAME: Nadeem\n, EMAIL: hashim@cosmosys.co \n, TITLE: CDO\n, COMPANY: Cosmosys \n Existing customers: FIRST NAME: Yahya\n, SECOND NAME: Qureshi \n, EMAIL: yahya@ok.co\n, TITLE: CEO\n, COMAPNY NAME: ok\n")
        ],
    }
))
"""

"""
retrieval_chain = RunnablePassthrough.assign(
    context=parse_retriever_input | retriever,
).assign(
    answer=document_chain,
)

retrieval_chain.invoke(
    {
        "messages": [
            HumanMessage(content="FIRST NAME: Hashim\n,SEOND NAME: Nadeem\n, EMAIL: hashim@cosmosys.co \n, TITLE: CDO\n, COMPANY: Cosmosys \n Existing customers: FIRST NAME: Yahya\n, SECOND NAME: Qureshi \n, EMAIL: yahya@ok.co\n, TITLE: CEO\n, COMAPNY NAME: ok\n")
        ],
    }
)
"""
# convert docs list to string
context = "\n".join(docs)
#email = retriever.query("Hashim, Nadeem, hashim@cosmosys.co, CDO, Cosmosys \n Existing customers: Yahya, Qureshi, yahya@ok.co, CEO, ok", llm=email_agent).strip()
email = email_agent.invoke("context: {context} \n FIRST NAME: Hashim\n,SEOND NAME: Nadeem\n, EMAIL: hashim@cosmosys.co \n, TITLE: CDO\n, COMPANY: Cosmosys \n Existing customers: FIRST NAME: Yahya\n, SECOND NAME: Qureshi \n, EMAIL: yahya@ok.co\n, TITLE: CEO\n, COMAPNY NAME: ok\n")
# print(email)
print(email.content)

send_emails(0,5)