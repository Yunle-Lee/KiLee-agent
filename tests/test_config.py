from kilee import config


class TestConfig:
    def test_defaults(self):
        cfg = config.load()
        assert cfg["model"] == "deepseek-chat"
        assert cfg["max_tokens"] == 8192
        assert cfg["api_key"] == ""

    def test_set_and_get(self):
        config.set_value("model", "deepseek-reasoner")
        assert config.get("model") == "deepseek-reasoner"
        config.set_value("model", "deepseek-chat")

    def test_unknown_key(self):
        assert config.get("nonexistent_key") is None
