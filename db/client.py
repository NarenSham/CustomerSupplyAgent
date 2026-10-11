"""All data access goes through sql(). Swap this file for Postgres/Lakebase later."""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem as P
from config import WAREHOUSE_ID

w = WorkspaceClient()   # Apps: service principal. Local: DATABRICKS_HOST / DATABRICKS_TOKEN.


def sql(stmt, **params):
    r = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID, statement=stmt, wait_timeout="30s",
        parameters=[P(name=k, value=str(v), type="INT" if isinstance(v, int) else "STRING")
                    for k, v in params.items()])
    if r.status.state.value != "SUCCEEDED":
        raise RuntimeError(r.status.error.message if r.status.error else "SQL failed")
    return r.result.data_array if r.result and r.result.data_array else []


def affected(rows):
    """DML statements return [[rows_affected]]."""
    return int(rows[0][0]) if rows else 0
