"""Tests for consumer utility functions.

Covers: map_action_to_db_feedback — mapping ConsumerAction enum
values to database feedback strings (like/dislike/None).
"""

from consumer.agent import map_action_to_db_feedback
from consumer.schemas import ConsumerAction


class TestMapActionToDbFeedback:
    def test_like_maps_to_like(self):
        assert map_action_to_db_feedback(ConsumerAction.LIKE) == "like"

    def test_dislike_maps_to_dislike(self):
        assert map_action_to_db_feedback(ConsumerAction.DISLIKE) == "dislike"

    def test_ignore_maps_to_none(self):
        assert map_action_to_db_feedback(ConsumerAction.IGNORE) is None
