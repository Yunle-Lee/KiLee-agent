from pathlib import Path
from kilee.tools import execute_bash, fs_read, fs_write, memory


class TestExecuteBash:
    def test_echo(self):
        result = execute_bash.run("echo hello")
        assert result == "hello"

    def test_dangerous_blocked(self):
        result = execute_bash.run("rm -rf /")
        assert result.startswith("[BLOCKED]")

    def test_with_working_dir(self, tmp_path):
        result = execute_bash.run("pwd", working_dir=str(tmp_path))
        assert str(tmp_path) in result

    def test_empty_output(self):
        result = execute_bash.run("echo -n ''")
        assert result == "(无输出)"


class TestFsRead:
    def test_read_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\n")
        result = fs_read.run(mode="Line", path=str(f))
        assert "line1" in result
        assert "line2" in result

    def test_directory(self, tmp_path):
        (tmp_path / "dir_a").mkdir()
        (tmp_path / "file_a.txt").write_text("")
        result = fs_read.run(mode="Directory", path=str(tmp_path))
        assert "dir_a" in result
        assert "file_a.txt" in result

    def test_search(self, tmp_path):
        f = tmp_path / "search.txt"
        f.write_text("hello world\nfoo bar\n")
        result = fs_read.run(mode="Search", pattern="hello", path=str(tmp_path))
        assert "hello" in result

    def test_file_not_found(self):
        result = fs_read.run(mode="Line", path="/nonexistent/path")
        assert result.startswith("[ERROR]")


class TestFsWrite:
    def test_create(self, tmp_path):
        p = str(tmp_path / "new.txt")
        result = fs_write.run(command="create", path=p, file_text="hello")
        assert result.startswith("已创建")
        assert Path(p).read_text() == "hello"

    def test_append(self, tmp_path):
        p = tmp_path / "append.txt"
        p.write_text("line1\n")
        result = fs_write.run(command="append", path=str(p), new_str="line2")
        assert result.startswith("已追加")
        assert p.read_text() == "line1\nline2\n"

    def test_str_replace(self, tmp_path):
        p = tmp_path / "replace.txt"
        p.write_text("hello world")
        result = fs_write.run(
            command="str_replace", path=str(p),
            old_str="hello", new_str="hi"
        )
        assert result.startswith("已替换")
        assert p.read_text() == "hi world"

    def test_insert(self, tmp_path):
        p = tmp_path / "insert.txt"
        p.write_text("a\nc\n")
        result = fs_write.run(
            command="insert", path=str(p),
            new_str="b", insert_line=1
        )
        assert result.startswith("已插入")
        assert p.read_text() == "a\nb\nc\n"


class TestMemory:
    def setup_method(self):
        memory.clear()

    def test_save_and_list(self):
        memory.run("user likes python")
        facts = memory.list_facts()
        assert "user likes python" in facts

    def test_clear(self):
        memory.run("some fact")
        memory.clear()
        assert memory.list_facts() == []

    def test_duplicate(self):
        memory.run("fact")
        memory.run("fact")
        assert memory.list_facts().count("fact") == 1

    def test_get_context(self):
        assert memory.get_context() == ""
        memory.run("test memory")
        ctx = memory.get_context()
        assert "test memory" in ctx
