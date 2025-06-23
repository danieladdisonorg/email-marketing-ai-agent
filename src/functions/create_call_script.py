from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from helpers.utils import set_api_key_env

# Load environment variables and API keys
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
set_api_key_env("OPENAI_API_KEY", openai_api_key)

llm = ChatOpenAI(model="gpt-4o")

call_script_prompt_template = ChatPromptTemplate([
    ("system", "You are a professional sales assistant. Generate **only a short opening line** for a cold sales call that grabs the user's attention and sets a positive tone. Keep it to 3-4 lines max."),
    ("user", "Here is the email content: {email_content}. Generate a persuasive and concise call script for the sales representative.")
])

call_script_agent = call_script_prompt_template | llm

def generate_call_script(email_content: str) -> str:
    """
        - Parameters:
            - email_content: str
            
        - Returns:
            - str: call_script
            
        - Description:
            - Generates a call script based on the email content.
    """
    try:
        # Invoke the model and get the response
        response = call_script_agent.invoke({"email_content": email_content})
        return response.content
    except Exception as e:
        print(f"Error generating call script: {e}")
        return "An error occurred while generating the call script."
