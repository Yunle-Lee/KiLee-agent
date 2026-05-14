from kilee import config
from kilee.approval import ApprovalMode, classify_risk


class TestApprovalMode:
    def setup_method(self):
        config.set_value("approval_mode", "suggest")

    def test_default_mode(self):
        assert ApprovalMode.from_config() == "suggest"

    def test_set_auto(self):
        ApprovalMode.set_mode("auto")
        assert config.get("approval_mode") == "auto"
        ApprovalMode.set_mode("suggest")

    def test_set_never(self):
        ApprovalMode.set_mode("never")
        assert config.get("approval_mode") == "never"
        ApprovalMode.set_mode("suggest")

    def test_invalid_mode_noop(self):
        ApprovalMode.set_mode("invalid")
        assert config.get("approval_mode") != "invalid"


class TestClassifyRisk:
    def test_fs_read_is_benign(self):
        assert classify_risk("fs_read") == "benign"

    def test_save_memory_is_benign(self):
        assert classify_risk("save_memory") == "benign"

    def test_web_search_is_benign(self):
        assert classify_risk("web_search") == "benign"

    def test_execute_bash_is_destructive(self):
        assert classify_risk("execute_bash") == "destructive"

    def test_fs_write_is_destructive(self):
        assert classify_risk("fs_write") == "destructive"

    def test_web_fetch_is_destructive(self):
        assert classify_risk("web_fetch") == "destructive"

    def test_unknown_is_destructive(self):
        assert classify_risk("unknown_tool") == "destructive"
