from kilee.compressor import _estimate_tokens


def test_estimate_tokens_empty():
    assert _estimate_tokens([]) == 0


def test_estimate_tokens():
    messages = [
        {"role": "user", "content": "hello world"},
        {"role": "assistant", "content": "hi there"},
    ]
    tokens = _estimate_tokens(messages)
    assert tokens > 0


def test_estimate_tokens_with_list_content():
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "hello"}]},
    ]
    tokens = _estimate_tokens(messages)
    assert tokens > 0


def test_below_threshold():
    messages = [
        {"role": "user", "content": "short"},
        {"role": "assistant", "content": "ok"},
    ]
    from kilee.compressor import maybe_compress
    result, did = maybe_compress(messages)
    assert did is False
    assert result == messages
