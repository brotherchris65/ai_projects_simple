import os

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from openai import AuthenticationError, RateLimitError

load_dotenv()

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Add it to your .env file and try again.")
        return

    model = ChatOpenAI(temperature=0)
    tools = []
    agent_executor = create_react_agent(model=model, tools=tools)

    print("Welcome! I'm your AI Assistant. Type 'quit' to exit.")
    print("You can ask me to perform calculations, fetch information, or assist with various tasks.")

    while True:
        user_input = input("\n You: ").strip()
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break

        try:
            result = agent_executor.invoke({"messages": [HumanMessage(content=user_input)]})
            assistant_message = result["messages"][-1]
            print(f"\n AI Assistant: {assistant_message.content}")
        except RateLimitError as err:
            error_text = str(err)
            if "insufficient_quota" in error_text:
                print("\nOpenAI quota exceeded (insufficient_quota).")
                print("Go to https://platform.openai.com/usage and https://platform.openai.com/settings/organization/billing to add credits or update billing.")
                print("If you recently changed billing, wait a minute and run again.")
                break
            print("\nRate limit reached. Please wait a moment and try again.")
        except AuthenticationError:
            print("\nAuthentication failed. Check that OPENAI_API_KEY in .env is correct and active.")
            break
        except Exception as err:
            print(f"\nUnexpected error: {err}")
                            
if __name__ == "__main__":    
     main()


        