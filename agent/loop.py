import json, re
from config import MODEL_ENDPOINT, TABLES as T
from db.client import w, sql
from agent.prompt import system_prompt
from agent.registry import TOOLS, BY_NAME

llm = w.serving_endpoints.get_open_ai_client()
SCHEMAS = [t.schema() for t in TOOLS]
SESSIONS: dict[str, list] = {}      # demo only: in-memory history per session
# Some models write the call as text: <function=name>{...}</function>. We catch that and run it.
FN = re.compile(r"<function=(\w+)>\s*(\{.*?\})\s*</function>", re.S)


def _tool(name, args, session_id):
    try:
        out = BY_NAME[name].run(**args)
        if name == "draft_order" and isinstance(out, dict) and out.get("order_id"):
            sql(f"UPDATE {T}.orders SET session_id = :s WHERE order_id = :o", s=session_id, o=out["order_id"])
    except Exception as e:
        out = {"error": str(e)}
    print(f"[tool] {name} {args} -> {out}", flush=True)
    return out


def run_agent(session_id, text, persona="warm"):
    msgs = SESSIONS.setdefault(session_id, [{"role": "system", "content": system_prompt(persona)}])
    msgs[0] = {"role": "system", "content": system_prompt(persona)}   # persona can change mid-chat
    msgs.append({"role": "user", "content": text})
    for _ in range(5):              # cap tool rounds
        m = llm.chat.completions.create(model=MODEL_ENDPOINT, messages=msgs, tools=SCHEMAS).choices[0].message
        msgs.append(m.model_dump(exclude_none=True))
        if m.tool_calls:
            for tc in m.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                out = _tool(tc.function.name, args, session_id)
                msgs.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(out, ensure_ascii=False)})
            continue
        fm = FN.search(m.content or "")
        if not fm:
            return m.content or ""
        try:
            args = json.loads(fm.group(2))
        except Exception:
            args = {}
        out = _tool(fm.group(1), args, session_id)
        msgs[-1] = {"role": "assistant", "content": f"(looked up {fm.group(1)})"}
        msgs.append({"role": "user", "content": f"[system: result of {fm.group(1)}: {json.dumps(out, ensure_ascii=False)}. "
                                                 "Now answer the caller in one or two short sentences. Do not output function syntax.]"})
    return "Sorry, I could not finish that."