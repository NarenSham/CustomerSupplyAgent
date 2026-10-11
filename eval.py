"""Regression eval. Run from app/ with your .env:  python eval.py
Results appear in Databricks > Experiments > stockroom-voice > Evaluation."""
import re, uuid
from dotenv import load_dotenv
load_dotenv(override=True)
import os; os.environ.pop("DATABRICKS_CONFIG_PROFILE", None)
import mlflow
from mlflow.genai.scorers import scorer
from config import TABLES as T
from db.client import sql
from agent.loop import run_agent

sql(f"UPDATE {T}.inventory SET on_hand = start_qty")   # known stock so expectations hold
sql(f"DELETE FROM {T}.orders")

DATA = [
    {"inputs": {"text": "Do you have ketchup?"}, "expectations": {"must_contain": ["40"]}},
    {"inputs": {"text": "Do you have peanut butter?"}, "expectations": {"must_contain": ["18"]}},
    {"inputs": {"text": "Est-ce que vous avez du sirop d'érable?"}, "expectations": {"must_contain": ["30"]}},
    {"inputs": {"text": "I want 500 cases of mayo"}, "expectations": {}},
    {"inputs": {"text": "What's the status of my order?"}, "expectations": {}},
]


@scorer
def no_leaks(outputs):          # no raw tool syntax, markdown or bullets (this is spoken audio)
    return not re.search(r"<function|\*\*|^\s*[-*] ", outputs, re.M)


@scorer
def short_enough(outputs):      # voice replies: three sentences max
    return len(re.findall(r"[.!?](\s|$)", outputs)) <= 3


@scorer
def has_expected(outputs, expectations):   # digits only; "forty" would fail
    return all(s in outputs for s in expectations.get("must_contain", []))


mlflow.set_tracking_uri("databricks")
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT", "/Shared/stockroom-voice"))
mlflow.genai.evaluate(data=DATA, predict_fn=lambda text: run_agent(str(uuid.uuid4()), text),
                      scorers=[no_leaks, short_enough, has_expected])