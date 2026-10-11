import random
from config import TABLES as T, MAX_QTY
from db.client import sql
from tools.base import Tool


class DraftOrder(Tool):
    name = "draft_order"
    description = "Create a DRAFT order. Does not change stock. Afterwards read the order back and ask the caller to confirm."
    parameters = {"sku": {"type": "string"}, "qty": {"type": "integer"}}

    def run(self, sku, qty):
        qty = int(qty)
        if not 1 <= qty <= MAX_QTY:
            return {"error": f"quantity must be between 1 and {MAX_QTY}"}
        rows = sql(f"SELECT on_hand FROM {T}.inventory WHERE sku = :s", s=sku)
        if not rows:
            return {"error": "unknown sku"}
        if int(rows[0][0]) < qty:
            return {"error": "not enough stock", "on_hand": int(rows[0][0])}
        oid = str(random.randint(1000, 9999))   # 4 digits: easy to say and hear
        while sql(f"SELECT 1 FROM {T}.orders WHERE order_id = :o", o=oid):
            oid = str(random.randint(1000, 9999))
        sql(f"INSERT INTO {T}.orders (order_id, sku, qty, status, created_at) VALUES (:o, :s, :q, 'draft', current_timestamp())", o=oid, s=sku, q=qty)
        return {"order_id": oid, "sku": sku, "qty": qty, "status": "draft"}