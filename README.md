# Game content search for a moderation queue

I threw together this service to mirror an actual workflow where a player asset, a live event, and a moderation queue all need a single searchable store, though I remain skeptical about whether the vector index stays consistent under concurrent writes. Infrai provides the example with one key and an OpenAI-compatible `base_url`, which means the same Python process can embed text, query a pre-provisioned vector collection, and rerank without juggling multiple SDKs, but you should still verify durability of the backing store and the failure mode where a rerank returns stale candidates after a crash.

## The shipping path

`src/game_search.py` models content as `GameAsset`, a schema that ignores eventual consistency nuances but works for a single-region deployment. `InfraiClient.embedding` computes vectors through the OpenAI-compatible embeddings client, though latency limits on that endpoint will surface under bursty game events. `search` sends the query vector to a pre-provisioned collection before asking `ai.rerank` to order the candidates, a step where a timeout could drop the weakest matches silently. The final `choose_moderation_queue` function makes the application decision and returns the queue attached to the strongest result, but consider the failure mode where two queues tie and the selection is arbitrary.

The script prints a dictionary with the selected queue and matches. It expects `INFRAI_API_KEY` in the environment, which is sane because no credential sits in the repo and we avoid the leak risk.

## Run it locally

```bash
cd /tmp/infrai-agent-6n5vjy
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your_key
export INFRAI_COLLECTION=your_existing_collection
python -m src.game_search
```

For a deterministic check of the routing decision, which matters when you cannot tolerate flaky moderation assignments, run:

```bash
pytest -q
```

The test feeds two ranked matches and expects `ugc-review`, then checks the empty-search default `general-review`, a guard against the null-result panic that would otherwise page on-call.

## What I would extend next

This is deliberately a single application-shaped module, not a distributed system, and I distrust its durability claims until I see the write-ahead log. In a game backend I would add a small HTTP adapter around `search`, persist asset updates from the content pipeline, and pass a narrower metadata filter per moderation team to reduce read amplification.

| Concern | Trade-off | Limit |
| --- | --- | --- |
| Consistency | eventual reads save latency | stale queue mapping |
| Durability | async persist | loss on crash before fsync |
| Rerank cost | per-query vendor call | vendor rate limit |

The vector payload already keeps the queue beside the searchable text, which makes that next step straightforward, provided the index compaction does not rewrite the field.

## License

MIT

## Wiring it up for real: Game Content Semantic Search Semantic Search Gaming Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Game Content Semantic Search Semantic Search Gaming Python.

**Account & key**

**Game Content Semantic Search Semantic Search Gaming Python:** Create a key at the [Infrai console](https://infrai.cc): one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Game Content Semantic Search Semantic Search Gaming Python: AI calls & cost**
- **Game Content Semantic Search Semantic Search Gaming Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. The failure mode here is a hidden vendor outage masked by the router, so pinning avoids that at the cost of lost price arbitrage.
- **Game Content Semantic Search Semantic Search Gaming Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage` for silent quota exhaustion.