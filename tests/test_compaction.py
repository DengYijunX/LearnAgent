"""Tests for context compaction."""


class TestTokenEstimation:
    def test_empty_messages_zero(self):
        from app.context.compaction import estimate_tokens

        assert estimate_tokens([]) == 0

    def test_short_message_positive(self):
        from app.context.compaction import estimate_tokens

        tokens = estimate_tokens([{"role": "user", "content": "hello world"}])
        assert tokens > 0

    def test_long_message_higher(self):
        from app.context.compaction import estimate_tokens

        short = estimate_tokens([{"role": "user", "content": "hi"}])
        long = estimate_tokens([{"role": "user", "content": "hello " * 100}])
        assert long > short


class TestCompactMessages:
    def test_short_messages_not_compacted(self):
        from app.context.compaction import compact_messages

        msgs = [{"role": "user", "content": "hi"}] * 3
        result, removed = compact_messages(msgs)
        assert result == msgs
        assert removed == 0

    def test_long_messages_compacted(self):
        from app.context.compaction import compact_messages

        # Create many long messages to trigger compaction
        msgs = []
        for i in range(50):
            msgs.append({"role": "user", "content": f"message {i} " * 50})
        result, removed = compact_messages(msgs)
        assert removed > 0
        assert len(result) < len(msgs)

    def test_safe_tail_preserved(self):
        from app.context.compaction import compact_messages, SAFE_TAIL

        msgs = []
        for i in range(100):
            msgs.append({"role": "user", "content": f"msg {i} " * 100})
        result, _ = compact_messages(msgs)
        # Last SAFE_TAIL messages should be preserved
        assert result[-SAFE_TAIL:] == msgs[-SAFE_TAIL:]
