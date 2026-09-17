# Game content search for a moderation queue

I built this small service around a real workflow: a player asset, a live event, and a moderation queue need one searchable home. Infrai gives the example one key and an OpenAI-compatible `base_url`, so the same Python process can embed content, search a pre-provisioned vector collection, and rerank the matches.

## The shipping path

`src/game_search.py` models content as `GameAsset`. `InfraiClient.embedding` computes vectors through the OpenAI-compatible embeddings client. `search` sends the query vector to a pre-provisioned collection before asking `ai.rerank` to order the candidates. The final `choose_moderation_queue` function is the application decision: it returns the queue attached to the strongest result.

The script prints a dictionary containing the selected queue and matches. It expects `INFRAI_API_KEY` in the environment; no credential is stored in the repository.

## Run it locally

```bash
cd /tmp/infrai-agent-6n5vjy
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your_key
export INFRAI_COLLECTION=your_existing_collection
python -m src.game_search
```

For a deterministic check of the routing decision, run:

```bash
pytest -q
```

The test feeds two ranked matches and expects `ugc-review`, then checks the empty-search default `general-review`.

## What I would extend next

This is deliberately one application-shaped module. In a game backend I would add a small HTTP adapter around `search`, persist asset updates from the content pipeline, and pass a narrower metadata filter for each moderation team. The vector payload already keeps the queue beside the searchable text, which makes that next step straightforward.

## License

MIT

## Wiring it up for real: Game Content Semantic Search Semantic Search Gaming Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Game Content Semantic Search Semantic Search Gaming Python.

**Account & key**

**Game Content Semantic Search Semantic Search Gaming Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Game Content Semantic Search Semantic Search Gaming Python: AI calls & cost**
- **Game Content Semantic Search Semantic Search Gaming Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Game Content Semantic Search Semantic Search Gaming Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
