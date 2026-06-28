# banner.py
import time, sys, os, subprocess, socket
from pyfiglet import figlet_format
from colorama import Fore, Style, init

init()

C  = Fore.CYAN
C2 = Fore.BLUE
Y  = Fore.YELLOW
G  = Fore.GREEN
AM = Fore.YELLOW
B  = Fore.BLUE
DM = Fore.BLACK + Style.BRIGHT
WH = Fore.WHITE
RE = Fore.RED
R  = Style.RESET_ALL
BR = Style.BRIGHT

def clear(): os.system('cls')
def p(text=""): print(text)
def t(s): time.sleep(s)
def separator(char="═", color=C2): print(color + "  " + char * 60 + R)

def progress_bar(label, width=28, delay=0.03, color=C):
    sys.stdout.write(f"    {WH}{label:<10}{R}  {DM}[{R}")
    sys.stdout.flush()
    for i in range(width):
        time.sleep(delay)
        sys.stdout.write(color + BR + "█" + R)
        sys.stdout.flush()
    sys.stdout.write(f"{DM}]{R}\n")
    sys.stdout.flush()

# ── REAL CHECKS ───────────────────────────────────────────────────
def check_port(host, port, timeout=2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except:
        return False

def check_docker():
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def run_docker_compose():
    try:
        result = subprocess.run(["docker-compose", "up", "-d"], capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except:
        return False

def status_line(name, ok, ok_msg="● RUNNING", fail_msg="● FAILED"):
    dots = "·" * 16
    color = G + BR if ok else RE + BR
    msg   = ok_msg if ok else fail_msg
    print(f"    {WH}{name:<10}{R}  {DM}{dots}{R}  {color}{msg}{R}")

# ── BOOT ──────────────────────────────────────────────────────────
clear()
t(0.1)

# Use 'big' font — clean block letters, renders perfectly in cmd
art = figlet_format("NEURAL", font="big")
for line in art.splitlines():
    print(C + BR + "  " + line + R)
    t(0.05)

p()
print(Y + BR + ("  ✦  N E S T   R A G   A P I   v 1 . 0  ✦").center(66) + R)
p()
separator()
p()
t(0.3)

# ── STEP 1: Docker ────────────────────────────────────────────────
sys.stdout.write(f"  {C2}›{R} {WH}Checking Docker daemon{R}")
sys.stdout.flush()
t(0.6)
docker_ok = check_docker()
print(f"  {G + BR}✓{R}" if docker_ok else f"  {RE + BR}✗  Docker not running!{R}")
t(0.2)

# ── STEP 2: docker-compose ────────────────────────────────────────
sys.stdout.write(f"  {C2}›{R} {WH}Starting Docker containers{R}")
sys.stdout.flush()
if docker_ok:
    compose_ok = run_docker_compose()
    print(f"  {G + BR}✓{R}" if compose_ok else f"  {RE + BR}✗  docker-compose failed{R}")
else:
    print(f"  {RE + BR}✗  Skipped{R}")
    compose_ok = False
t(0.3)

p()

# ── PROGRESS BARS ─────────────────────────────────────────────────
progress_bar("Redis",   delay=0.025, color=C)
redis_ok = check_port("localhost", 6379)
t(0.15)

progress_bar("Qdrant",  delay=0.03,  color=C)
qdrant_ok = check_port("localhost", 6333)
t(0.15)

progress_bar("FastAPI", delay=0.02,  color=G)
fastapi_ok = check_port("localhost", 8000)
t(0.4)

# ── STATUS PANEL ──────────────────────────────────────────────────
p()
separator()
all_ok = docker_ok and redis_ok and qdrant_ok
status_text  = "✦  SYSTEM STATUS : ONLINE  ✦"  if all_ok else "✦  SYSTEM STATUS : DEGRADED  ✦"
status_color = G + BR                           if all_ok else RE + BR
print(status_color + status_text.center(64) + R)
separator()
p()

status_line("Docker",  docker_ok)
t(0.1)
status_line("Redis",   redis_ok)
t(0.1)
status_line("Qdrant",  qdrant_ok)
t(0.1)
print(f"    {WH}{'Python':<10}{R}  {DM}{'·' * 16}{R}  {G + BR}● VENV ACTIVE{R}")
t(0.1)
status_line("FastAPI", fastapi_ok, ok_msg="● RUNNING", fail_msg="● STARTING")
t(0.1)

p()
separator("─")
p()
print(f"    {WH}API   {R}  {B}http://127.0.0.1:8000{R}")
print(f"    {WH}DOCS  {R}  {B}http://127.0.0.1:8000/docs{R}")
print(f"    {WH}REDOC {R}  {B}http://127.0.0.1:8000/redoc{R}")
p()

# ── WARNINGS ──────────────────────────────────────────────────────
if not docker_ok:
    print(RE + BR + "  ⚠  Docker Desktop is not running. Start it and retry." + R)
if not redis_ok:
    print(RE + BR + "  ⚠  Redis unreachable on port 6379. Check container logs." + R)
if not qdrant_ok:
    print(RE + BR + "  ⚠  Qdrant unreachable on port 6333. Check container logs." + R)

p()
separator("─")
p()
print(f"  {DM}Uvicorn logs appear below ↓{R}")
p()
separator()
p()