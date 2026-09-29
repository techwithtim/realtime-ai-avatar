# Nocturne: a restaurant website with a maître d' you can talk to

A fictional tasting-menu restaurant with a Synthesia avatar in the corner. You talk to Ava and she answers, and while she talks she drives the page: scrolling to a course, filtering the whole menu down to what you can eat, opening a dish with its wine pairing, and adding things to a running order.

```
mic → VAD → STT → turn detection → LLM (+ 4 tools) → TTS → Synthesia avatar → browser
```

## Setup
1. Create a free LiveKit Cloud project at https://cloud.livekit.io and create an API key (Settings → API Keys).
2. Get a Synthesia API key with Interactive Avatars enabled: https://www.synthesia.io/features/avatars/interactive-avatars
3. Copy `.env.example` to `.env` and fill in the values. `SYNTHESIA_AVATAR_ID` is optional; it defaults to a stock avatar.

```bash
cp .env.example .env    # then fill it in

python agent.py dev     # terminal 1
python server.py        # terminal 2 → open http://localhost:8080
```
Click **Start** and allow the mic. The first join can take a while on a cold start. Don't use `python agent.py console`, because the avatar never appears in console mode.

Try: *"I'm vegetarian, what should I have?"* · *"Tell me about the duck."* · *"What goes with the halibut?"* · *"Add the short rib."*

## Files
| File | What it is |
|---|---|
| `agent.py` | The AI: prompt, four small tools, the voice pipeline and the three avatar lines |
| `index.html` | The page shell plus the avatar widget (about 30 lines of JS) |
| `server.py` | Serves the page and creates a room token that sends the agent in |
| `static/site.js` | The restaurant site itself: menu data, rendering, and the `SITE` API |
| `static/site.css` | Styling |

The restaurant and the avatar are kept apart on purpose. `static/site.js` knows nothing about LiveKit or Synthesia; it just exposes one `SITE` method per tool. `index.html` forwards every tool call into it in one line:

```js
const { action, ...args } = JSON.parse(new TextDecoder().decode(payload));
SITE[action]?.(args);
```

So you can make the website as elaborate as you like without touching the avatar code, and the site still works with the agent switched off.

## Adding a tool
1. Add a `@function_tool` to `agent.py` that calls `self._ui(action="your_tool", ...)`.
2. Add a matching `your_tool({ ... })` method to `SITE` in `static/site.js`.
3. Mention it in `INSTRUCTIONS` so the model knows when to use it.

## If it breaks
| Error | Fix |
|---|---|
| `SynthesiaError` `AUTH` / `FEATURE_NOT_IN_PLAN` | Bad key, or your workspace doesn't have Interactive Avatars enabled |
| `LIVEKIT_CREDENTIALS_REJECTED` | The LiveKit URL, key and secret aren't all from the same project |
| `UNKNOWN_AVATAR` | That `SYNTHESIA_AVATAR_ID` isn't in your workspace |
| Avatar never appears | You used console mode, or `AGENT_NAME` doesn't match in `agent.py` and `server.py` |
| Page loads unstyled | `static/` isn't next to `server.py` |
| Ava never hears you | Watch the dot next to the status text. Green while you talk means LiveKit is getting your mic, so the problem is downstream in the agent: check its terminal for STT errors. Never green means the browser is capturing the wrong input; pick the right mic in Chrome's site settings (the camera icon in the address bar) and reload. |

Built on Synthesia's official quickstarts: https://github.com/synthesia-ai/interactive-avatar-quickstarts
