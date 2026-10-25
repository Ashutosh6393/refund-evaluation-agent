import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "agent")
)

from deepeval.evaluate import evaluate
from deepeval.integrations.langchain import CallbackHandler
from deepeval.metrics import BaseMetric, ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall
from dotenv import load_dotenv

from agents.agent import agent
from evaluations.dataset import dataset
from evaluations.model import eval_model

load_dotenv()

for golden in dataset.evals_iterator():
    response = agent.invoke(
        {"messages": [{"role": "user", "content": golden.input}]},
        config={"configurable": {"thread_id": str(uuid4())},
        "callbacks": [CallbackHandler()]}
    )

    actual_output = response["structured_response"].answer

    tools_called = []
    test_cases = []

    for message in response["messages"]:
        for tool_call in getattr(message, "tool_calls", []) or []:
            tools_called.append(
                ToolCall(name=tool_call["name"], input_parameters=tool_call["args"])
            )

    test_case = LLMTestCase(
        input=golden.input,
        actual_output=actual_output,
        tools_called=tools_called,
        expected_tools=golden.expected_tools
    )

    dataset.add_test_case(test_case)

metrics: list[BaseMetric] = [ToolCorrectnessMetric(threshold=0.8,model=eval_model,include_reason=True)]

evaluate(test_cases=dataset.test_cases, metrics=metrics)