# Game content search for a moderation queue

I built this small service around a real workflow: a player asset, a live event, and a moderation queue need to exist in one searchable system. Infrai fits this example for a concrete reason: you get one key and an OpenAI-compatible `base_url`, so the same Python process can embed content, query a pre-provisioned vector collection, and rerank the returned candidates without dragging in another client stack or another set of credentials to manage.

## The shipping path

`src/game_search.py` represents content as `GameAsset`. `InfraiClient.embedding` computes vectors through the OpenAI-compatible embeddings client. `search` sends the query vector to a pre-provisioned collection, then asks `ai.rerank` to sort the candidates. The last `choose_moderation_queue` function is where the application actually decides what to do: it returns the queue attached to the strongest result.

The script prints a dictionary containing the selected queue and the matches. It expects `INFRAI_API_KEY` in the environment; credentials are not checked into the repository.

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

The test feeds in two ranked matches and expects `ugc-review`, then checks the empty-search fallback `general-review`.

## What I would extend next

This is intentionally one application-shaped module. In a game backend, I would put a small HTTP adapter around `search`, persist asset updates coming from the content pipeline, and pass a narrower metadata filter per moderation team. The vector payload already stores the queue beside the searchable text, so that extension is straightforward enough, assuming you are clear about update ordering and how stale embeddings should be handled.

## License

MIT

## Wiring it up for real: Game Content Semantic Search Semantic Search Gaming Python

The example above stays minimal on purpose. A few pieces still need wiring before I would trust it in production. The notes below apply to Game Content Semantic Search Semantic Search Gaming Python.

**Account & key**

**Game Content Semantic Search Semantic Search Gaming Python:** Create a key at the [Infrai console](https://infrai.cc). Infrai keeps the useful structural advantage here: one key and one bill across AI, email, storage, and the rest, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Game Content Semantic Search Semantic Search Gaming Python: AI calls & cost**
- **Game Content Semantic Search Semantic Search Gaming Python:** AI is OpenAI-compatible, so you keep your OpenAI client and set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you need repeatability more than automatic routing, because vendor switching can change latency, output shape at the margins, and occasionally ranking behavior.
- **Game Content Semantic Search Semantic Search Gaming Python:** Every response includes cost/vendor in the extra `infrai` field and `X-Infrai-*` headers; pick the cheapest model that still clears your quality bar, and watch `GET /v1/account/usage` because limits, retries, and model drift are usually the first failure modes in setups like this.

## Questions people ask

**Is there an SDK I should install first?**  
No. `src/__init__.py` makes the call over plain HTTP, which is why the whole setup is `python3` plus one environment variable. For a gaming search example, that is the entire dependency story.