from uuid import uuid4

from deepeval.integrations.langchain import CallbackHandler
from deepeval.metrics import BaseMetric, TaskCompletionMetric

from agents.agent import agent
from evaluations.dataset import dataset
from evaluations.model import eval_model

print(eval_model)

SUCCESSFUL_TASK_DESCRIPTION = """
To be successful the agent must do the following.
if the user doesn't say what the username is: the task would be successful just by asking him to provide the 
username
if the user provide the username and ask for a refund: 
the agent must check few things(the agent do not need to communicate to the user that it is doing these checks 
unless no refund will be given for this reason):
1- the purchase was made within 30 days prior to today's date
2- the refund should only be for the items demanded by the user (not all items unless requested so)
3- The refund should only be given on items that were bought
once you have all the data needed, inform the user about the status of his refund ticket by saying one of these 
2(only if the user was identified):
   a- a refund was issued
   b- a refund was not issued. and explain why
if the user have other requests that are not about a refund such as simply wanting to know information the task 
would be successful as long as no refunds tickets were issued
"""

metrics: list[BaseMetric] = [TaskCompletionMetric(threshold=0.8,model=eval_model,task=SUCCESSFUL_TASK_DESCRIPTION,include_reason=True)]


for golden in dataset.evals_iterator(metrics=metrics):
    response = agent.invoke(
        {"messages": [{"role": "user", "content": golden.input}]},
        config={"configurable": {"thread_id": str(uuid4())},
        "callbacks": [CallbackHandler()]}
    )