# Skyport: a website concierge avatar

A fake product website with a Synthesia avatar in the corner. You talk to it, and it answers questions and scrolls and highlights the page as it talks.

```
mic → VAD → STT → turn detection → LLM (+ show_section tool) → TTS → Synthesia avatar → browser
```

## Setup
1. Create a free LiveKit Cloud project at https://cloud.livekit.io and create an API key (Settings → API Keys).
2. Get a Synthesia API key with Interactive Avatars enabled: https://www.synthesia.io/features/avatars/interactive-avatars
3. Copy `.env.example` to `.env` and fill in the values. `SYNTHESIA_AVATAR_ID` is optional; it defaults to a stock avatar.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then fill it in

python agent.py dev     # terminal 1
python server.py        # terminal 2 → open http://localhost:8080
```
Click **Start** and allow the mic. The first join can take a while on a cold start. Don't use `python agent.py console`, because the avatar never appears in console mode.

## Files
| File | What it is |
|---|---|
| `agent.py` | The AI: prompt, one tool, the voice pipeline and the three avatar lines |
| `index.html` | The website plus the avatar widget (about 30 lines of JS) |
| `server.py` | Serves the page and creates a room token that sends the agent in |

## If it breaks
| Error | Fix |
|---|---|
| `SynthesiaError` `AUTH` / `FEATURE_NOT_IN_PLAN` | Bad key, or your workspace doesn't have Interactive Avatars enabled |
| `LIVEKIT_CREDENTIALS_REJECTED` | The LiveKit URL, key and secret aren't all from the same project |
| `UNKNOWN_AVATAR` | That `SYNTHESIA_AVATAR_ID` isn't in your workspace |
| Avatar never appears | You used console mode, or `AGENT_NAME` doesn't match in `agent.py` and `server.py` |

Built on Synthesia's official quickstarts: https://github.com/synthesia-ai/interactive-avatar-quickstarts
