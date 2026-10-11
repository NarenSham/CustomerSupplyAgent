from config import TABLES as T
from db.client import sql, affected
from tools.base import Tool


class ConfirmOrder(Tool):
    name = "confirm_order"
    description = "Confirm a draft order. Only call after the caller explicitly said yes to your read-back."
    parameters = {"order_id": {"type": "string"}}

    def run(self, order_id):
        rows = sql(f"SELECT sku, qty FROM {T}.orders WHERE order_id = :o", o=order_id)
        if not rows:
            return {"error": "unknown order"}
        sku, qty = rows[0][0], int(rows[0][1])
        # Claim first (draft -> confirmed), then take stock. A repeated "yes" claims nothing.
        if not affected(sql(f"UPDATE {T}.orders SET status = 'confirmed' WHERE order_id = :o AND status = 'draft'", o=order_id)):
            return {"error": "order is not a draft (already confirmed?)"}
        if not affected(sql(f"UPDATE {T}.inventory SET on_hand = on_hand - :q WHERE sku = :s AND on_hand >= :q", q=qty, s=sku)):
            sql(f"UPDATE {T}.orders SET status = 'failed' WHERE order_id = :o", o=order_id)
            return {"error": "stock ran out"}
        return {"order_id": order_id, "status": "confirmed"}
