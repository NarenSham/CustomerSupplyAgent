import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from livekit import api as lk
from config import TABLES as T
from db.client import sql
from agent.loop import run_agent, SESSIONS

app = FastAPI()


class Chat(BaseModel):
    session_id: str
    text: str
    persona: str = "warm"


@app.post("/api/chat")
def chat(c: Chat):
    return {"reply": run_agent(c.session_id, c.text, c.persona)}


@app.get("/api/token")
def token(session_id: str, persona: str = "warm", lang: str = "en"):
    try:
        t = (lk.AccessToken(os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"])
             .with_identity(f"cust-{session_id[:8]}")
             .with_attributes({"persona": persona, "lang": lang, "session_id": session_id})
             .with_grants(lk.VideoGrants(room_join=True, room=f"stockroom-{session_id}")))
        return {"token": t.to_jwt(), "url": os.environ["LIVEKIT_URL"]}
    except Exception as e:
        raise HTTPException(500, f"token error: {type(e).__name__}: {e}")


@app.get("/api/inventory")
def inventory():
    items = sql(f"""SELECT p.sku, p.name_en, p.name_fr, i.on_hand, i.start_qty, i.reorder_pt
                    FROM {T}.products p JOIN {T}.inventory i ON p.sku = i.sku ORDER BY p.sku""")
    return {"items": [dict(sku=r[0], en=r[1], fr=r[2], on_hand=int(r[3]), start=int(r[4]), reorder=int(r[5])) for r in items]}


@app.get("/api/orders")
def orders(session_id: str):
    rows = sql(f"SELECT order_id, sku, qty, status FROM {T}.orders WHERE session_id = :s ORDER BY created_at DESC LIMIT 8",
               s=session_id)
    return {"orders": [dict(id=r[0], sku=r[1], qty=int(r[2]), status=r[3]) for r in rows]}


@app.post("/api/reset")
def reset():
    sql(f"UPDATE {T}.inventory SET on_hand = start_qty")
    sql(f"DELETE FROM {T}.orders")
    SESSIONS.clear()
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")