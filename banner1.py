"""
banner.py — NEURAL RAG API  v2.0
Premium boot screen for the NEURAL RAG stack (Redis · Qdrant · FastAPI)
"""

import time, sys, os, subprocess, socket, shutil
from datetime import datetime

# ── Optional rich dependency ──────────────────────────────────────
try:
    from rich.console import Console
    from rich.text import Text
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.align import Align
    from rich.rule import Rule
    from rich.table import Table
    from rich.live import Live
    from rich.progress import (
        Progress, SpinnerColumn, BarColumn,
        TextColumn, TimeElapsedColumn
    )
    from rich.style import Style
    from rich.padding import Padding
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ── Colorama fallback ─────────────────────────────────────────────
try:
    from colorama import Fore, Style as CStyle, init as cinit
    cinit()
    C_VIOLET  = "\033[38;5;135m"
    C_INDIGO  = "\033[38;5;105m"
    C_CYAN    = Fore.CYAN
    C_GREEN   = Fore.GREEN
    C_RED     = Fore.RED
    C_YELLOW  = Fore.YELLOW
    C_WHITE   = Fore.WHITE
    C_GREY    = "\033[38;5;243m"
    C_RESET   = CStyle.RESET_ALL
    C_BRIGHT  = CStyle.BRIGHT
    C_DIM     = CStyle.DIM
except ImportError:
    C_VIOLET = C_INDIGO = C_CYAN = C_GREEN = C_RED = C_YELLOW = ""
    C_WHITE = C_GREY = C_RESET = C_BRIGHT = C_DIM = ""

# ── Constants ─────────────────────────────────────────────────────
VERSION   = "v2.0.0"
BUILD     = datetime.now().strftime("%Y%m%d")
API_HOST  = "http://127.0.0.1:8000"

SERVICES = [
    ("Redis",   "localhost", 6379,  "Cache layer"),
    ("Qdrant",  "localhost", 6333,  "Vector store"),
    ("FastAPI", "localhost", 8000,  "API gateway"),
]

# ── Utilities ─────────────────────────────────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def sleep(s):
    time.sleep(s)

def terminal_width():
    return shutil.get_terminal_size((80, 24)).columns

# ── Real checks ───────────────────────────────────────────────────
def check_port(host, port, timeout=2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def check_docker():
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False

def run_docker_compose():
    try:
        r = subprocess.run(
            ["docker-compose", "up", "-d"],
            capture_output=True, text=True, timeout=30
        )
        return r.returncode == 0
    except Exception:
        return False

# ══════════════════════════════════════════════════════════════════
#  RICH RENDERER  (preferred)
# ══════════════════════════════════════════════════════════════════

VIOLET  = "bright_magenta"
INDIGO  = "medium_purple1"
SLATE   = "grey50"
EMERALD = "green3"
SCARLET = "red3"
AMBER   = "yellow3"
ICE     = "bright_cyan"

LOGO_LINES = [
    "  ███╗   ██╗███████╗██╗   ██╗██████╗  █████╗ ██╗     ",
    "  ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔══██╗██║     ",
    "  ██╔██╗ ██║█████╗  ██║   ██║██████╔╝███████║██║     ",
    "  ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██╔══██║██║     ",
    "  ██║ ╚████║███████╗╚██████╔╝██║  ██║██║  ██║███████╗",
    "  ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝",
]

TAGLINE = "Retrieval-Augmented Generation · Production Stack"

def render_rich():
    con = Console(highlight=False)
    clear()
    sleep(0.05)

    # ── Logo ──────────────────────────────────────────────────────
    for i, line in enumerate(LOGO_LINES):
        shade = VIOLET if i < 3 else INDIGO
        con.print(Align.center(Text(line, style=f"bold {shade}")))
        sleep(0.055)

    con.print()
    con.print(Align.center(Text(TAGLINE, style=f"bold {ICE}")))
    con.print(Align.center(Text(f"  {VERSION}  ·  build {BUILD}", style=SLATE)))
    con.print()
    con.rule(style=INDIGO)
    con.print()
    sleep(0.25)

    # ── Docker ────────────────────────────────────────────────────
    with con.status(
        Text("  Initialising Docker daemon …", style=SLATE),
        spinner="dots", spinner_style=VIOLET
    ):
        sleep(0.6)
        docker_ok = check_docker()

    icon = "✓" if docker_ok else "✗"
    col  = EMERALD if docker_ok else SCARLET
    msg  = "Docker daemon ready" if docker_ok else "Docker not running — start Docker Desktop"
    con.print(f"  [{col}]{icon}[/{col}]  [dim]{msg}[/dim]")
    sleep(0.15)

    # ── docker-compose ────────────────────────────────────────────
    with con.status(
        Text("  Bringing up containers …", style=SLATE),
        spinner="dots12", spinner_style=VIOLET
    ):
        if docker_ok:
            compose_ok = run_docker_compose()
            sleep(0.3)
        else:
            compose_ok = False

    icon = "✓" if compose_ok else "✗"
    col  = EMERALD if compose_ok else SCARLET
    msg  = "Containers started" if compose_ok else ("Skipped — Docker offline" if not docker_ok else "docker-compose failed")
    con.print(f"  [{col}]{icon}[/{col}]  [dim]{msg}[/dim]")
    con.print()
    sleep(0.2)

    # ── Service probes ────────────────────────────────────────────
    results = {}
    with Progress(
        TextColumn("  [bold dim]{task.description:<10}"),
        BarColumn(bar_width=32, style=INDIGO, complete_style=VIOLET, finished_style=EMERALD),
        TextColumn("[dim]{task.percentage:>3.0f}%[/dim]"),
        console=con, transient=False
    ) as prog:
        for name, host, port, label in SERVICES:
            task = prog.add_task(name, total=100)
            for step in range(100):
                sleep(0.004 + (0.002 if name == "Qdrant" else 0))
                prog.update(task, advance=1)
            results[name] = check_port(host, port)

    con.print()
    sleep(0.2)

    # ── Status panel ──────────────────────────────────────────────
    all_ok = docker_ok and all(results.get(n, False) for n, *_ in SERVICES[:2])

    status_text  = "●  SYSTEM ONLINE" if all_ok else "⚠  SYSTEM DEGRADED"
    status_style = f"bold {EMERALD}" if all_ok else f"bold {SCARLET}"

    status_table = Table.grid(padding=(0, 3))
    status_table.add_column(justify="right", min_width=10)
    status_table.add_column(justify="left",  min_width=30)

    rows = [("Docker", docker_ok, "daemon")] + [
        (name, results[name], label)
        for name, _h, _p, label in SERVICES
    ]

    for svc_name, ok, label in rows:
        dot   = "●" if ok else "○"
        color = EMERALD if ok else SCARLET
        state = "running" if ok else ("starting" if svc_name == "FastAPI" else "offline")
        status_table.add_row(
            Text(svc_name, style="bold white"),
            Text(f"{dot}  {label}  ·  {state}", style=color if ok else SCARLET)
        )

    panel = Panel(
        Align.center(status_table),
        title=Text(status_text, style=status_style),
        border_style=VIOLET if all_ok else SCARLET,
        padding=(1, 4),
        box=box.DOUBLE_EDGE,
    )
    con.print(panel)
    con.print()

    # ── Endpoint table ────────────────────────────────────────────
    ep_table = Table(
        show_header=False, box=None, padding=(0, 2), expand=False
    )
    ep_table.add_column(style="dim", justify="right")
    ep_table.add_column(style=ICE)
    ep_table.add_column(style=SLATE)

    endpoints = [
        ("API",    f"{API_HOST}",       "REST gateway"),
        ("DOCS",   f"{API_HOST}/docs",  "Swagger UI"),
        ("REDOC",  f"{API_HOST}/redoc", "ReDoc reference"),
        ("HEALTH", f"{API_HOST}/health","Health probe"),
    ]
    for label, url, desc in endpoints:
        ep_table.add_row(label, url, f"·  {desc}")

    con.print(Align.center(ep_table))
    con.print()

    # ── Warnings ──────────────────────────────────────────────────
    if not docker_ok:
        con.print(f"  [{SCARLET}]⚠[/{SCARLET}]  [dim]Docker Desktop is not running. Start it and retry.[/dim]")
    if not results.get("Redis"):
        con.print(f"  [{AMBER}]⚠[/{AMBER}]  [dim]Redis unreachable on :6379 — check container logs.[/dim]")
    if not results.get("Qdrant"):
        con.print(f"  [{AMBER}]⚠[/{AMBER}]  [dim]Qdrant unreachable on :6333 — check container logs.[/dim]")

    con.print()
    con.rule(style=SLATE)
    con.print(f"  [dim]Uvicorn output ↓[/dim]")
    con.print()


# ══════════════════════════════════════════════════════════════════
#  FALLBACK RENDERER  (colorama / plain)
# ══════════════════════════════════════════════════════════════════

def _c(color, text, reset=True):
    return color + text + (C_RESET if reset else "")

def render_plain():
    W = terminal_width()
    clear()
    sleep(0.05)

    # ── Logo ──────────────────────────────────────────────────────
    for i, line in enumerate(LOGO_LINES):
        shade = C_VIOLET if i < 3 else C_INDIGO
        print(_c(shade + C_BRIGHT, line.center(W)))
        sleep(0.055)

    print()
    print(_c(C_CYAN + C_BRIGHT, TAGLINE.center(W)))
    print(_c(C_GREY, f"{VERSION}  ·  build {BUILD}".center(W)))
    print()
    print(_c(C_INDIGO, "  " + "═" * (W - 4)))
    print()
    sleep(0.25)

    # ── Docker ────────────────────────────────────────────────────
    sys.stdout.write(f"  {_c(C_GREY, '›')}  Checking Docker daemon … ")
    sys.stdout.flush()
    sleep(0.6)
    docker_ok = check_docker()
    icon = _c(C_GREEN + C_BRIGHT, "✓") if docker_ok else _c(C_RED + C_BRIGHT, "✗")
    msg  = "ready" if docker_ok else "not running"
    print(f"{icon}  {_c(C_GREY, msg)}")
    sleep(0.15)

    sys.stdout.write(f"  {_c(C_GREY, '›')}  Starting containers … ")
    sys.stdout.flush()
    if docker_ok:
        compose_ok = run_docker_compose()
        sleep(0.2)
    else:
        compose_ok = False
    icon = _c(C_GREEN + C_BRIGHT, "✓") if compose_ok else _c(C_RED + C_BRIGHT, "✗")
    msg  = "up" if compose_ok else ("skipped" if not docker_ok else "failed")
    print(f"{icon}  {_c(C_GREY, msg)}")
    print()
    sleep(0.2)

    # ── Progress bars ─────────────────────────────────────────────
    BAR_W = 32
    results = {}
    for name, host, port, label in SERVICES:
        sys.stdout.write(f"  {_c(C_WHITE + C_BRIGHT, f'{name:<10}')}")
        sys.stdout.write(f"  {_c(C_GREY, '[')}")
        sys.stdout.flush()
        steps = BAR_W
        delay = 0.006
        for _ in range(steps):
            sleep(delay)
            sys.stdout.write(_c(C_VIOLET + C_BRIGHT, "█"))
            sys.stdout.flush()
        print(_c(C_GREY, "]"))
        results[name] = check_port(host, port)
        sleep(0.1)

    print()
    sleep(0.2)

    # ── Status ────────────────────────────────────────────────────
    all_ok = docker_ok and all(results.get(n, False) for n, *_ in SERVICES[:2])
    verdict = "✦  SYSTEM ONLINE  ✦" if all_ok else "⚠  SYSTEM DEGRADED  ⚠"
    vcolor  = C_GREEN + C_BRIGHT if all_ok else C_RED + C_BRIGHT
    border_char = "═"
    print(_c(C_INDIGO, "  " + border_char * (W - 4)))
    print(_c(vcolor, verdict.center(W)))
    print(_c(C_INDIGO, "  " + border_char * (W - 4)))
    print()

    all_rows = [("Docker", docker_ok, "daemon")] + [
        (name, results[name], label) for name, _h, _p, label in SERVICES
    ]
    for svc_name, ok, label in all_rows:
        dot   = "●" if ok else "○"
        color = C_GREEN + C_BRIGHT if ok else C_RED + C_BRIGHT
        state = "running" if ok else ("starting" if svc_name == "FastAPI" else "offline")
        dots  = "·" * 14
        print(f"    {_c(C_WHITE + C_BRIGHT, f'{svc_name:<10}')}  {_c(C_GREY, dots)}  {_c(color, f'{dot}  {state}')}")
        sleep(0.08)

    print()

    # ── Endpoints ─────────────────────────────────────────────────
    print(_c(C_GREY, "  " + "─" * (W - 4)))
    endpoints = [
        ("API",    f"{API_HOST}"),
        ("DOCS",   f"{API_HOST}/docs"),
        ("REDOC",  f"{API_HOST}/redoc"),
        ("HEALTH", f"{API_HOST}/health"),
    ]
    for label, url in endpoints:
        print(f"    {_c(C_GREY, f'{label:<8}')}  {_c(C_CYAN, url)}")
    print()

    # ── Warnings ──────────────────────────────────────────────────
    if not docker_ok:
        print(f"  {_c(C_RED + C_BRIGHT, '⚠')}  {_c(C_GREY, 'Docker Desktop is not running. Start it and retry.')}")
    if not results.get("Redis"):
        print(f"  {_c(C_YELLOW + C_BRIGHT, '⚠')}  {_c(C_GREY, 'Redis unreachable on :6379 — check container logs.')}")
    if not results.get("Qdrant"):
        print(f"  {_c(C_YELLOW + C_BRIGHT, '⚠')}  {_c(C_GREY, 'Qdrant unreachable on :6333 — check container logs.')}")

    print()
    print(_c(C_GREY, "  " + "─" * (W - 4)))
    print(f"  {_c(C_GREY + C_DIM, 'Uvicorn output ↓')}")
    print()


# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if HAS_RICH:
        render_rich()
    else:
        render_plain()