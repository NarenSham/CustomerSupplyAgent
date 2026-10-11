"""LiveKit voice worker (ears + mouth). The brain is agent.loop.run_agent, shared with the typed chat.
Put in app/ next to config.py. Run from app/:  python voice_worker.py dev
Env: LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, DEEPGRAM_API_KEY, CARTESIA_API_KEY,
     VOICE_ID (Cartesia voice id), optional VOICE_ID_FR,
     DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID, MODEL_ENDPOINT"""
import asyncio, os, random
from dotenv import load_dotenv
load_dotenv(override=True)   # .env beats shell vars; must run before importing config
os.environ.pop("DATABRICKS_CONFIG_PROFILE", None)   # force token auth, not the CLI profile
from livekit import agents
from livekit.agents import Agent, AgentSession
from livekit.plugins import cartesia, deepgram, openai, silero
from agent.prompt import system_prompt
from agent.loop import run_agent

NAMES = {"warm": "Emma", "pro": "Claire", "upbeat": "Zoe"}
SPEED = {"warm": 1.02, "pro": 0.95, "upbeat": 1.08}   # a touch faster sounds happier
EMO = {"warm": {"emotion": ["positivity:high"]},       # Cartesia emotion controls; delete if your plugin version rejects them
       "upbeat": {"emotion": ["positivity:highest", "curiosity"]}}


FILLERS = {"en": ["Hmm, let me check.", "Mm-hm, one sec.", "Okay, just a moment.", "Sure, let me take a look."],
           "fr": ["Hum, un instant.", "Voyons voir.", "D'accord, une seconde."]}
FILLER_AFTER = 1.1   # seconds of silence before a filler is spoken; tune to taste


class Stockroom(Agent):
    def __init__(self, sid, persona, lang="en"):
        super().__init__(instructions=system_prompt(persona))
        self.sid, self.persona, self.lang = sid, persona, lang

    async def llm_node(self, chat_ctx, tools, model_settings):
        user = next((m for m in reversed(chat_ctx.items)
                     if getattr(m, "role", None) == "user" and m.text_content), None)
        text = user.text_content if user else "Hello"
        task = asyncio.create_task(asyncio.to_thread(run_agent, self.sid, text, self.persona))
        done, _ = await asyncio.wait({task}, timeout=FILLER_AFTER)
        if not done:   # slow turn: fill the silence while the model and tools work
            yield random.choice(FILLERS.get(self.lang, FILLERS["en"])) + " "
        yield await task


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    p = await ctx.wait_for_participant()
    persona = p.attributes.get("persona", "warm")
    lang = p.attributes.get("lang", "en")
    sid = p.attributes.get("session_id", "")
    voice = (os.getenv("VOICE_ID_FR") if lang == "fr" else None) or os.environ["VOICE_ID"]
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3", language=lang),
        llm=openai.LLM(model=os.environ["MODEL_ENDPOINT"], base_url=os.environ["DATABRICKS_HOST"].rstrip("/") + "/serving-endpoints",
                       api_key=os.environ["DATABRICKS_TOKEN"]),   # unused: llm_node above does the thinking
        tts=cartesia.TTS(model="sonic-2", voice=voice, language=lang, speed=SPEED.get(persona, 1.0), **EMO.get(persona, {})),
    )
    await session.start(room=ctx.room, agent=Stockroom(sid, persona, lang))
    name = NAMES.get(persona, "Emma")
    await session.say(f"Hi, I'm {name}. How can I help you with your order today?" if lang == "en"
                      else f"Bonjour, ici {name}. Comment puis-je vous aider avec votre commande?")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))