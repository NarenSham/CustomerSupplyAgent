from config import TABLES as T
from db.client import sql
from tools.base import Tool


class CheckInventory(Tool):
    name = "check_inventory"
    description = "Look up stock by product name in English or French. Pass only the product name, like 'ketchup'."
    parameters = {"query": {"type": "string"}}

    def run(self, query):
        q = f"%{query.lower().strip()}%"
        rows = sql(f"""SELECT p.sku, p.name_en, p.name_fr, i.on_hand
                       FROM {T}.products p JOIN {T}.inventory i ON p.sku = i.sku
                       WHERE lower(p.name_en) LIKE :q OR lower(p.name_fr) LIKE :q OR lower(p.aliases) LIKE :q""", q=q)
        return [dict(sku=r[0], name_en=r[1], name_fr=r[2], on_hand=int(r[3])) for r in rows] or {"error": "no match"}
