from config import TABLES as T
from db.client import sql
from tools.base import Tool


class OrderStatus(Tool):
    name = "order_status"
    description = "Check order status. Pass the order_id if the caller gave one, otherwise an empty string for recent orders."
    parameters = {"order_id": {"type": "string"}}

    def run(self, order_id=""):
        base = f"SELECT order_id, sku, qty, status FROM {T}.orders "
        rows = sql(base + "WHERE order_id = :o", o=order_id) if order_id else sql(base + "ORDER BY created_at DESC LIMIT 3")
        return [dict(order_id=r[0], sku=r[1], qty=int(r[2]), status=r[3]) for r in rows] or {"error": "no orders found"}
