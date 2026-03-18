from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv()

@tool
def calculator(a: float, b: float) -> str:
    """Userful for performing basic arithmetic operations. """
    print("The calculator tool is being used.")
    return f"The result of {a} + {b} is {a + b}. The result of {a} - {b} is {a - b}. The result of {a} * {b} is {a * b}. The result of {a} / {b} is {a / b if b != 0 else 'undefined (division by zero)'}."

def main():
    model = ChatOpenAI(temperature=0)
    tools = [calculator]
    agent_executor = create_react_agent(model=model, tools=tools)

    print("Welcome! I'm you AI Assistant. Type 'quit' to exit.")
    print("You can ask me to perform calculations, fetch information, or assist with various tasks.")

    while True:
        user_input = input("\n You: ").strip()
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break

        result = agent_executor.invoke({"messages": [HumanMessage(content=user_input)]})
        assistant_message = result["messages"][-1]
        print(f"\n AI Assistant: {assistant_message.content}")
                            
if __name__ == "__main__":    
     main()


        