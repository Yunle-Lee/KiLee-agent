from kilee.tools import execute_bash, fs_read, fs_write, memory, web_search, web_fetch

TOOLS = [
    execute_bash.SCHEMA,
    fs_read.SCHEMA,
    fs_write.SCHEMA,
    memory.SCHEMA,
    web_search.SCHEMA,
    web_fetch.SCHEMA,
]

def dispatch(name: str, args: dict) -> str:
    if name == "execute_bash":
        return execute_bash.run(**args)
    elif name == "fs_read":
        return fs_read.run(**args)
    elif name == "fs_write":
        return fs_write.run(**args)
    elif name == "save_memory":
        return memory.run(**args)
    elif name == "web_search":
        return web_search.run(**args)
    elif name == "web_fetch":
        return web_fetch.run(**args)
    return f"[ERROR] 未知工具: {name}"
