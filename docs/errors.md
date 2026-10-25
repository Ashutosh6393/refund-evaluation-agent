# Errors and fixes

## Judge call crashes with `got list` instead of `Content`

**Error**

```
TypeError: Parameter to initialize message field must be dict or instance of same class:
expected <class 'xai.api.v1.chat_pb2.Content'> got <class 'list'>.
```

Raised from `deepeval/models/llms/grok_model.py` in `a_generate`, at `chat.append(user(content))`, after the agent calls have already finished. The metric then fails while scoring the traces.

**Cause**

`GrokModel._prompt_content` builds an OpenAI-style list, for example `[{"type": "text", "text": "..."}]`. `xai_sdk.chat.user` treats each argument as one content part. Passing the whole list as one argument stores that list in the message, and the xAI protobuf field rejects it.

**Fix**

`evaluations/model.py` uses `XaiJudge`, a `GrokModel` subclass. Its `_prompt_content` returns the prompt string, which `user()` accepts. `TaskCompletionMetric` is given that instance instead of the model name string.

`grok-2-mini` is in DeepEval's price table, but xAI returns `NOT_FOUND` for it. The judge uses `grok-4.3`, the same model as the agent. DeepEval has no price row for `grok-4.3`, so judge cost is not reported. The request still goes to xAI.

## Judge tries to use OpenAI

**Error**

```
DeepEvalError: OpenAI API key is not configured. Set OPENAI_API_KEY in your environment
or pass `api_key` to OpenAIModel(...).
```

Raised while constructing `TaskCompletionMetric`.

**Cause**

`eval_model` was the string `"grok-4.3"`. DeepEval does not pick a provider from the model name. With no provider flag set, a string becomes `OpenAIModel`.

**Fix**

Set `USE_GROK_MODEL=true` and `GROK_API_KEY` (the same key the agent uses as `XAI_API_KEY`). `GROK_API_KEY` is what DeepEval's Grok client reads. `XAI_API_KEY` is only for the LangChain agent. Install `xai-sdk`, which `GrokModel` imports when it generates.

## `list[TaskCompletionMetric]` is not assignable to `list[BaseMetric]`

**Error**

Pyrefly rejected `dataset.evals_iterator(metrics=metrics)` because `metrics` was inferred as `list[TaskCompletionMetric]` and the parameter type is `list[BaseMetric] | None`.

**Cause**

Lists are invariant. A list of a subclass is not treated as a list of the base class.

**Fix**

In `evaluations/task_completion.py`, annotate `metrics: list[BaseMetric]`.

## `python src/agent/tools.py` says `agent` is not a package

**Error**

```
ModuleNotFoundError: No module named 'agent.data'; 'agent' is not a package
```

**Cause**

Running the file directly puts `src/agent` on `sys.path`. Python then loads `agent.py` as the module `agent`, which shadows the package, and that file imports `tools` again.

**Fix**

`tools.py` inserts the `src` directory at the front of `sys.path` before `from agent.data` and `from agent.objects`.

## `Cannot find module objects`

**Error**

Pyrefly could not resolve `from objects import PurchaseItem`. Its import root is `src`, and `objects.py` lives in the `agent` package.

**Fix**

Import `agent.objects` and `agent.data`. Ruff keeps those in a first-party group after third-party imports.

## `BaseTool.invoke` missing `input`

**Error**

```
TypeError: BaseTool.invoke() missing 1 required positional argument: 'input'
```

**Cause**

`invoke` takes one positional input. Keyword arguments such as `username=` and `items=` are not that argument.

**Fix**

Call `calculate_right_refund.invoke({"username": "user123", "items": [book, pen]})`.

## `error()` call on root logger

**Error**

Ruff warning: use your own logger instead of `logging.error` / `logging.info`.

**Fix**

`tools.py` uses `logger = logging.getLogger(__name__)`. Purchase records are typed with `PurchaseRecord` so the refund total and the history return type check.

## Non-fatal warning during evals

```
Warning: Could not load test run from disk: Shared locks on Windows require the win32 extra (pywin32)
```

This does not stop the run. It only means DeepEval could not take a shared file lock for a saved test run. The crash above is separate.
