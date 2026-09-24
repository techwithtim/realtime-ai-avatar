"""An AI concierge with a face, living on a website.

The pipeline:
    mic -> VAD -> STT -> turn detection -> LLM (+ tool) -> TTS -> Synthesia avatar -> browser

Run:  python agent.py dev      (terminal 1)
      python server.py         (terminal 2, then open http://localhost:8080)
"""

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli, function_tool, inference
from livekit.plugins import silero, synthesia

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

AGENT_NAME = "avatar-demo"  # must match server.py
AVATAR_ID = os.getenv("SYNTHESIA_AVATAR_ID") or "8788bef1-8020-46e0-a8f4-510ea9989b25"  # Jenny
VOICE_ID = "db6b0ed5-d5d3-463d-ae85-518a07d3c2b4"  # Cartesia "Skylar"

# The avatar's knowledge: just a prompt. No database, no RAG.
INSTRUCTIONS = """\
You are Ava, the concierge on the website of Skyport, a made-up app hosting product.
You are a real-time avatar in a spoken conversation, so answer in one to three
short sentences and never use markdown, lists, or URLs.

What you know about Skyport:
- Skyport deploys any web app from a GitHub repo in one click, with free SSL and preview links.
- Plans: Hobby is free (1 app, sleeps when idle). Pro is $12 a month (unlimited apps, custom domains).
  Team is $39 a month (everything in Pro plus 5 seats and shared logs).
- Every plan includes a 14 day money back guarantee.

When you talk about a part of the page, call show_section so the visitor sees it.
Help visitors pick a plan by asking what they are building."""


class Concierge(Agent):
    def __init__(self, room) -> None:
        super().__init__(instructions=INSTRUCTIONS)
        self.room = room

    @function_tool
    async def show_section(self, section: str) -> str:
        """Scroll the website to a section and highlight it.

        Args:
            section: One of: features, pricing, hobby, pro, team, faq.
        """
        # Send a tiny message to the browser. index.html does the scrolling.
        await self.room.local_participant.publish_data(
            json.dumps({"section": section}), topic="ui"
        )
        return "Shown."


def prewarm(proc) -> None:
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    # The brain: each line is one piece of the pipeline.
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],                                   # is someone talking?
        stt=inference.STT(model="cartesia/ink-2"),                      # speech -> text
        llm=inference.LLM(model="openai/gpt-4.1-mini"),                 # text -> reply (swap in any LLM)
        tts=inference.TTS(model="cartesia/sonic-3.6", voice=VOICE_ID),  # reply -> speech
        turn_handling={
            "turn_detection": "stt",                        # have they finished their thought?
            "preemptive_generation": {"enabled": False},    # keep off when using tools
        },
    )

    # The face: this is the whole Synthesia integration. Start it BEFORE session.start().
    avatar = synthesia.AvatarSession(
        synthesia.AvatarConfig(avatar_ids=[AVATAR_ID]),
        join_timeout=60.0,
    )
    for attempt in range(3):  # cold starts occasionally time out, so retry
        try:
            await avatar.start(session, room=ctx.room)
            break
        except synthesia.SynthesiaError as e:
            if not e.retryable or attempt == 2:
                raise
            await asyncio.sleep(2)

    await session.start(agent=Concierge(ctx.room), room=ctx.room)
    session.generate_reply(instructions="Greet the visitor in one short sentence.")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm, agent_name=AGENT_NAME, port=8081))
