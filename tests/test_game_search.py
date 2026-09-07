from src.game_search import choose_moderation_queue


def test_routes_best_match_to_its_moderation_queue():
    results = [{"metadata": {"queue": "ugc-review"}, "score": 0.92}, {"metadata": {"queue": "live-events"}, "score": 0.61}]
    assert choose_moderation_queue(results) == "ugc-review"
    assert choose_moderation_queue([]) == "general-review"
