# Refund evaluation agent

A customer-support agent that decides refunds against a small in-memory purchase list, and a [DeepEval](https://deepeval.com) suite that scores those decisions.

The agent is a LangChain agent (`langchain.agents.create_agent`) backed by Grok (`grok-4.3` through `langchain-xai`). Each reply is a structured `Answer`: the text shown to the customer, and a `conversation` flag that stays true until the refund decision is finished.

## Refund rules

The system prompt in `agents/prompts.py` tells the agent to:

1. Identify the customer. If the username is missing, ask for it.
2. Look up that customer's purchases with `get_user_purchase_history`.
3. Refund only the items the customer asked for, and only items they actually bought.
4. Treat a purchase as eligible when it is at most 30 days old and the purchase date is not in the future. The current date comes from `get_today_date`, not from the model's own sense of today's date.
5. Get the amount from `calculate_right_refund`, then call `issue_refund_ticket`.
6. For a question that is not a refund request, answer it and do not issue a ticket.

If the customer or the item cannot be found, or the purchase is outside the window, the agent should explain why and skip the ticket.

Purchase records live in `agents/data.py`. Prices are whole dollars. The evaluation cases use `user123` and `user126`. `user123` bought a book ($23, 2026-10-05) and a pen ($7, 2026-10-03). `user126` bought a backpack ($45, 2026-10-02) and a water bottle ($18, 2026-07-25). The water bottle is outside the 30-day window relative to late October 2026.

## Tools

| Tool | What it does |
| --- | --- |
| `get_user_purchase_history` | Returns that user's purchases, or a not-found status. |
| `get_today_date` | Returns today's date as `YYYY-MM-DD`. |
| `calculate_right_refund` | Sums the stored prices of the given item names. |
| `issue_refund_ticket` | Logs a ticket and returns a success string with the amount. It does not persist anything. |

## Evaluation

`evaluations/dataset.py` holds seven goldens. Each one has the user message, the conclusion the reply should reach, and the tool calls that should happen.

| Input | Expected conclusion |
| --- | --- |
| `user123` wants a refund for the book and the pen | Ticket for $30 |
| `user123` wants a refund for the book | Ticket for $23 |
| `user123` only wants to know what they bought | No ticket, list the purchases |
| `user999` wants a refund for the book | Username is not valid |
| `user126` wants a refund for the water bottle | No refund, outside 30 days |
| `user126` wants a refund for the backpack and the water bottle | Ticket for $45 (backpack only) |
| `user126` wants a refund for sneakers | No refund, item was not purchased |

`evaluations/eval_all.py` runs the agent once per golden and scores all seven metrics on that pass. A fresh `thread_id` is used for every case so checkpointed memory does not leak between them. DeepEval's result cache is turned off.

Four metrics read the agent trace. DeepEval's LangChain `CallbackHandler` is attached to `agent.invoke`, and the metrics are passed into `dataset.evals_iterator`:

- **Task completion** (threshold 0.8). The task text in `eval_all.py` is the refund policy above, written as pass/fail conditions.
- **Step efficiency** (0.8).
- **Plan quality** (0.8).
- **Plan adherence** (0.8).

Three metrics score a normal `LLMTestCase` built from the same response. `actual_output` is `structured_response.answer`. Tool calls are copied off the message list.

- **Argument correctness**. Whether the arguments passed to tools were right. The combined runner does not set a threshold.
- **Tool correctness** (0.9). Compares the calls that happened with `expected_tools`, including input parameters.
- **Answer correctness** (0.8). A `GEval` metric that checks the reply and `expected_output` reach the same conclusion. Wording can differ.

The judge is `XaiJudge` in `evaluations/model.py`, a `GrokModel` subclass that also uses `grok-4.3`. Stock `GrokModel` hands `xai_sdk.chat.user` an OpenAI-style list of content parts. That helper wants a string, and the list blows up inside the xAI protobuf message. `XaiJudge` returns the prompt string instead. DeepEval has no price row for `grok-4.3`, so judge cost is not printed. The request still goes to xAI.

The other files in `evaluations/` run one metric at a time. They call the agent the same way. `task_completion.py`, `plan_quality.py`, `plan_adherence.py`, and `step_effeciency.py` score inside the iterator. `argument_correctness.py`, `tool_correctness.py`, and `answer_correctness.py` build test cases and call `evaluate`. Thresholds in those scripts are 0.8, including tool correctness, and argument correctness uses 0.8 there. `eval_all.py` is the run that scores everything together.

`docs/errors.md` records the setup failures hit while wiring the judge (the content-list crash, DeepEval falling back to OpenAI, and the Windows lock warning).

## Setup

Python 3.13 or newer. Dependencies are installed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env
```

Put the xAI key in `.env`:

```
XAI_API_KEY=...
GROK_API_KEY=...
USE_GROK_MODEL=true
```

`XAI_API_KEY` is what the LangChain agent reads. `GROK_API_KEY` is what DeepEval's Grok client reads. Use the same key for both. `USE_GROK_MODEL=true` stops DeepEval from constructing an OpenAI model when it sees the model name.

## Run

From the repository root, so `agents` and `evaluations` import:

```bash
uv run python evaluations/eval_all.py
```

One metric:

```bash
uv run python evaluations/task_completion.py
uv run python evaluations/step_effeciency.py
uv run python evaluations/plan_quality.py
uv run python evaluations/plan_adherence.py
uv run python evaluations/argument_correctness.py
uv run python evaluations/tool_correctness.py
uv run python evaluations/answer_correctness.py
```

To talk to the agent in a loop, uncomment `run_conversation()` at the bottom of `agents/agent.py` and run:

```bash
uv run python -m agents.agent
```

The starter message is "I would like to request a refund". The loop keeps asking for a reply while `conversation` is true, then prints `the job is done!`.

## Layout

```
agents/
  agent.py      # create_agent and the optional REPL
  prompts.py    # refund policy
  tools.py      # the four tools
  data.py       # purchase records
  models.py     # grok-4.3
  objects.py    # Answer and PurchaseItem
evaluations/
  dataset.py    # seven goldens
  model.py      # XaiJudge
  eval_all.py   # all seven metrics
  *.py          # one metric each
docs/errors.md  # judge and import failures already hit
```
