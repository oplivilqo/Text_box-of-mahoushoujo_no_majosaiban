# filename: should_handle_win.py
import os
import win32gui
import win32process
import psutil

# 白名单配置文件名（和当前 py 在同一目录）
WHITELIST_FILENAME = "process_whitelist.txt"

# 只加载一次的缓存
_WHITELIST: set[str] | None = None          # 小写后的进程名，用来匹配
_WHITELIST_RAW: list[str] = []              # 保留原始写法，用来打印


def _get_config_path() -> str:
    """获取白名单 txt 的绝对路径"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, WHITELIST_FILENAME)


def _ensure_file_exists(path: str) -> None:
    """
    如果白名单文件不存在，就创建一个带注释的模板文件，
    方便你手动填进程名。
    """
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(
                "# 一行一个进程名（区分大小写与否都无所谓，这里会统一转小写）\n"
                "# 比如：\n"
                "# WeChat.exe\n"
                "# QQ.exe\n"
                "# Discord.exe\n"
            )


def init_whitelist(verbose: bool = True) -> set[str]:
    """
    主程序启动时手动调用：
      - 只加载一次白名单
      - 可选：打印当前加载了哪些进程
    之后不再自动重新加载（如果改了 txt，需要重启程序生效）
    """
    global _WHITELIST, _WHITELIST_RAW

    if _WHITELIST is not None:
        # 已经初始化过了，再调用就当 no-op，
        # 但如果 verbose=True 可以顺便再打印一次
        if verbose:
            if _WHITELIST_RAW:
                print(
                    f"[should_handle_win] 白名单已初始化："
                    f" {', '.join(_WHITELIST_RAW)}"
                )
            else:
                print(
                    "[should_handle_win] 白名单已初始化，但列表为空，"
                    "所有程序都不会被拦截。"
                )
        return _WHITELIST

    path = _get_config_path()
    _ensure_file_exists(path)

    names: set[str] = set()
    raw: list[str] = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                raw.append(line)
                names.add(line.lower())
    except OSError:
        names = set()
        raw = []

    _WHITELIST = names
    _WHITELIST_RAW = raw

    if verbose:
        if raw:
            print(
                f"[should_handle_win] 已从 {os.path.basename(path)} 加载白名单进程："
                f" {', '.join(raw)}"
            )
        else:
            print(
                f"[should_handle_win] 已从 {os.path.basename(path)} 加载白名单，"
                "但当前没有任何进程名；所有程序都不会被拦截。"
            )

    return _WHITELIST


def get_foreground_process_name() -> str | None:
    """
    获取当前前台窗口的进程名，比如 WeChat.exe / QQ.exe
    失败时返回 None
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return None

        p = psutil.Process(pid)
        return p.name()
    except Exception:
        return None


def should_handle() -> bool:
    """
    核心判断：
    - 取当前前台进程名
    - 看是否在白名单
    """
    # 确保至少初始化过一次（如果主程序忘记调用 init_whitelist，这里兜底）
    global _WHITELIST
    if _WHITELIST is None:
        init_whitelist(verbose=False)

    wl = _WHITELIST or set()
    name = get_foreground_process_name()
    if not name:
        return False

    return name.lower() in wl
