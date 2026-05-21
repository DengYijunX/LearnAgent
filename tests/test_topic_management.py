"""Tests for topic normalization and auto-management."""


class TestTopicNormalization:
    def test_same_topic_different_writing(self):
        from app.core.router import normalize_topic

        assert normalize_topic("Rust") == "rust"
        assert normalize_topic("rust") == "rust"
        assert normalize_topic("RUST") == "rust"

    def test_strips_learn_prefixes(self):
        from app.core.router import normalize_topic

        assert normalize_topic("学习Rust") == "rust"
        assert normalize_topic("继续学习Rust") == "rust"
        assert normalize_topic("Rust学习") == "rust"

    def test_strips_question_words(self):
        from app.core.router import normalize_topic

        assert normalize_topic("Rust怎么用") == "rust"
        assert normalize_topic("怎么理解Rust") == "rust"
        assert normalize_topic("讲讲Rust") == "rust"

    def test_preserves_compound_topics(self):
        from app.core.router import normalize_topic

        assert normalize_topic("Rust async/await") == "rust-async-await"
        assert normalize_topic("Python 协程") == "python-协程"

    def test_empty_returns_none(self):
        from app.core.router import normalize_topic

        assert normalize_topic("") is None
        assert normalize_topic(" ") is None


class TestTopicDrift:
    def test_exact_match_same_topic(self):
        from app.core.router import topic_distance

        assert topic_distance("rust", "rust") == "same"

    def test_related_topics_drift(self):
        from app.core.router import topic_distance

        # shared word "rust"
        assert topic_distance("rust", "rust-tokio") == "drift"

    def test_containment_is_drift(self):
        from app.core.router import topic_distance

        # "rust-async" is a sub-topic of "rust"
        assert topic_distance("rust", "rust-async-await") == "drift"
        assert topic_distance("python", "python-asyncio") == "drift"

    def test_unrelated_topics_switch(self):
        from app.core.router import topic_distance

        assert topic_distance("rust", "langgraph") == "switch"
        assert topic_distance("python", "react") == "switch"

    def test_none_current_is_switch(self):
        from app.core.router import topic_distance

        assert topic_distance(None, "rust") == "switch"
