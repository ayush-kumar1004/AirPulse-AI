# TODO: Person C — Government Action Recommendation agent.
# Input: forecast (Person B) + source breakdown (Person B) + ward context.
# Output: specific, PRIORITISED actions (not generic alerts). MUST match schemas.RecommendationResponse.


def recommend_actions(ward_id: str) -> dict:
    """Return {'ward_id', 'actions': [...]} — prioritised, targeted, time-boxed government actions."""
    raise NotImplementedError("Person C: implement recommendation agent (Claude)")
