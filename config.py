import os

TABLES = f"{os.getenv('CATALOG', 'workspace')}.{os.getenv('SCHEMA', 'voice_demo')}"
WAREHOUSE_ID = os.environ["DATABRICKS_WAREHOUSE_ID"]
MODEL_ENDPOINT = os.environ["MODEL_ENDPOINT"]
MAX_QTY = int(os.getenv("MAX_QTY", "100"))
