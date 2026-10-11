# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %pip install -q openai

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# # Does the model call tools, in English and French? Use the endpoint name from the Serving page,
# # not the system.ai.* catalog path.
# dbutils.widgets.text("endpoint", "")
# from databricks.sdk import WorkspaceClient

# client = WorkspaceClient().serving_endpoints.get_open_ai_client()
# tools = [{"type": "function", "function": {
#     "name": "check_inventory", "description": "Look up stock by product name. Pass only the product name.",
#     "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}]
# for q in ["Do you have ketchup in stock?", "Est-ce que vous avez du sirop d'érable?"]:
#     m = client.chat.completions.create(model=dbutils.widgets.get("endpoint"),
#                                        messages=[{"role": "user", "content": q}], tools=tools).choices[0].message
#     print(q, "->", m.tool_calls or m.content)

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
names = [e.name for e in w.serving_endpoints.list()]
print("endpoints:", names)

client = w.serving_endpoints.get_open_ai_client()
candidates = ["deepseek-v4-flash-0731", "system.ai.deepseek-v4-flash-0731"]
candidates += [n for n in names if "deepseek" in n.lower()]


# COMMAND ----------

for name in candidates:
    try:
        r = client.chat.completions.create(
            model=name, messages=[{"role": "user", "content": "Say hi"}], max_tokens=10)
        print("WORKS:", name, "->", r.choices[0].message.content)
    except Exception as e:
        print("no:", name, str(e)[:100])

# COMMAND ----------

from databricks.sdk import WorkspaceClient

client = WorkspaceClient().serving_endpoints.get_open_ai_client()
EP = "databricks-deepseek-v4-flash-0731"
msgs = [{"role": "user", "content": "Say hi"}]

for label, kwargs in [
    ("no token limit", {}),
    ("max_completion_tokens", {"max_completion_tokens": 20}),
    ("max_tokens", {"max_tokens": 20}),
]:
    try:
        r = client.chat.completions.create(model=EP, messages=msgs, **kwargs)
        print("WORKS:", label, "->", r.choices[0].message.content)
    except Exception as e:
        print("FAIL:", label, "->", str(e))

# COMMAND ----------

import time
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
available = {e.name for e in w.serving_endpoints.list()}
print("databricks-* endpoints:", sorted(n for n in available if n.startswith("databricks-")))

client = w.serving_endpoints.get_open_ai_client()
tools = [{"type": "function", "function": {
    "name": "check_inventory", "description": "Look up stock by product name. Pass only the product name.",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}]
questions = ["Do you have ketchup in stock?", "Est-ce que vous avez du sirop d'érable?"]
candidates = ["databricks-deepseek-v4-1-flash", "databricks-meta-llama-3-3-70b-instruct", "databricks-gpt-oss-120b"]

for ep in candidates:
    if ep not in available:
        print("not in workspace:", ep)
        continue
    for q in questions:
        t = time.time()
        try:
            m = client.chat.completions.create(model=ep, messages=[{"role": "user", "content": q}], tools=tools).choices[0].message
            calls = [(c.function.name, c.function.arguments) for c in (m.tool_calls or [])]
            print(f"{ep} | {q} -> {calls or m.content} ({time.time() - t:.1f}s)")
        except Exception as e:
            print(f"{ep} | FAIL: {str(e)[:300]}")