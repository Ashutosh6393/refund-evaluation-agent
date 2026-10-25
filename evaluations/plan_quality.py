from uuid import uuid4

from deepeval.integrations.langchain import CallbackHandler
from deepeval.metrics import BaseMetric, PlanQualityMetric

from agents.agent import agent
from evaluations.dataset import dataset
from evaluations.model import eval_model

metrics: list[BaseMetric] = [PlanQualityMetric(threshold=0.8,model=eval_model,include_reason=True)]


for golden in dataset.evals_iterator(metrics=metrics):
    response = agent.invoke(
        {"messages": [{"role": "user", "content": golden.input}]},
        config={"configurable": {"thread_id": str(uuid4())},
        "callbacks": [CallbackHandler()]}
    )