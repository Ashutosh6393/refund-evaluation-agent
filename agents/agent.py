from uuid import uuid4

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from agents.models import model
from agents.objects import Answer
from agents.prompts import agent_system_prompt
from agents.tools import (
    calculate_right_refund,
    get_today_date,
    get_user_purchase_history,
    issue_refund_ticket,
)

load_dotenv()

agent = create_agent(
    model=model,
    system_prompt=agent_system_prompt,
    tools=[calculate_right_refund,get_user_purchase_history,issue_refund_ticket,get_today_date],
    response_format=Answer,
    checkpointer=InMemorySaver()
)

def run_conversation():
    config = {"configurable": {"thread_id": str(uuid4())}}

    text = "I would like to request a refund"
    print(text)
    
    question = HumanMessage(content=text)
    conversation = True

    while conversation:

        response = agent.invoke({"messages":question}, config=config)
        structured_response = response["structured_response"]

        print(structured_response.answer)

        conversation = structured_response.conversation

        if conversation:
            user_input = input("reply: \n")
            question = HumanMessage(content=user_input)

    print("the job is done!")

# run_conversation()