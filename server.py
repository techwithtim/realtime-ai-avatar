"""Serves the web page and hands the browser a token to join a LiveKit room.

Run: python server.py, then open http://localhost:8080
"""

import os
import uuid
from datetime import timedelta
from pathlib import Path

from aiohttp import web
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

AGENT_NAME = "avatar-demo"  # must match agent.py


async def token(request: web.Request) -> web.Response:
    # Demo only: no auth. Put this behind your app's login in anything real.
    room = f"avatar-demo-{uuid.uuid4().hex[:8]}"  # fresh room per visit
    jwt = (
        api.AccessToken()  # reads LIVEKIT_API_KEY / LIVEKIT_API_SECRET
        .with_identity(f"user-{uuid.uuid4().hex[:8]}")
        .with_ttl(timedelta(minutes=15))
        .with_grants(api.VideoGrants(room_join=True, room=room))
        .with_room_config(
            api.RoomConfiguration(
                sync_streams=True,  # keeps the avatar's lips in sync with its audio
                agents=[api.RoomAgentDispatch(agent_name=AGENT_NAME)],  # sends our agent in
            )
        )
        .to_jwt()
    )
    return web.json_response({"url": os.environ["LIVEKIT_URL"], "token": jwt})


async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(
        Path(__file__).parent / "index.html", headers={"Cache-Control": "no-store"}
    )


app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/token", token)

if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8080)
