#!/usr/bin/env python3
"""
Запуск dev-окружения кроссплатформенно (Windows, macOS, Linux).

Из корня репозитория:
  pip install -r requirements.txt
  npm install --prefix frontend

Затем:
  python scripts/dev.py                 # бэкенд + фронтенд
  python scripts/dev.py --backend-only  # только API (uvicorn)
  python scripts/dev.py --frontend-only # только Vite
  python scripts/dev.py --frontend-only --install  # npm install в frontend/, затем Vite
  python scripts/dev.py --backend-only --port 8787  # если 8000 занят / WinError 10013

Порт API: переменная окружения BACKEND_PORT или флаг --port (по умолчанию 8000).
Перед первым запуском фронта: npm install в каталоге frontend/ (см. --install).

Интерпретатор: используйте тот же Python, куда ставили зависимости (часто `python3` на Linux/macOS).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def _npm() -> str | None:
    return shutil.which("npm") or shutil.which("npm.cmd")


def _frontend_deps_ready() -> bool:
    return (FRONTEND / "node_modules" / "vite" / "package.json").is_file()


def install_frontend_deps() -> int:
    npm = _npm()
    if not npm:
        print("[dev] npm не найден в PATH. Установите Node.js.", file=sys.stderr, flush=True)
        return 1
    cmd = [npm, "install"]
    print(f"[dev] frontend deps: {' '.join(cmd)} (cwd={FRONTEND})", flush=True)
    return subprocess.call(cmd, cwd=str(FRONTEND), env=os.environ.copy())


def resolve_backend_port(cli_port: int | None) -> str:
    if cli_port is not None:
        return str(cli_port)
    env_port = os.environ.get("BACKEND_PORT", "").strip()
    if env_port:
        return env_port
    return "8000"


def run_backend(port: str) -> int:
    env = os.environ.copy()
    env["BACKEND_PORT"] = port
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        port,
    ]
    print("[dev] backend:", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=str(ROOT), env=env)


def run_frontend() -> int:
    npm = _npm()
    if not npm:
        print("[dev] npm не найден в PATH. Установите Node.js.", file=sys.stderr, flush=True)
        return 1
    env = os.environ.copy()
    cmd = [npm, "run", "dev"]
    print(f"[dev] frontend: {' '.join(cmd)} (cwd={FRONTEND})", flush=True)
    return subprocess.call(cmd, cwd=str(FRONTEND), env=env)


def run_both(port: str) -> int:
    npm = _npm()
    if not npm:
        print("[dev] npm не найден в PATH. Установите Node.js или используйте --backend-only.", file=sys.stderr, flush=True)
        return 1

    env = os.environ.copy()
    env["BACKEND_PORT"] = port
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        port,
    ]
    frontend_cmd = [npm, "run", "dev"]

    print("[dev] backend:", " ".join(backend_cmd), flush=True)
    be = subprocess.Popen(backend_cmd, cwd=str(ROOT), env=env)
    print(f"[dev] frontend: {' '.join(frontend_cmd)} (cwd={FRONTEND})", flush=True)
    fe = subprocess.Popen(frontend_cmd, cwd=str(FRONTEND), env=env)

    def terminate_children() -> None:
        for p in (fe, be):
            if p.poll() is None:
                p.terminate()
        deadline = time.monotonic() + 8.0
        for p in (fe, be):
            while p.poll() is None and time.monotonic() < deadline:
                time.sleep(0.1)
            if p.poll() is None:
                p.kill()

    rc = 0
    try:
        while True:
            if be.poll() is not None:
                print("[dev] backend завершился", flush=True)
                rc = be.returncode or 0
                break
            if fe.poll() is not None:
                print("[dev] frontend завершился", flush=True)
                rc = fe.returncode or 0
                break
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\n[dev] остановка…", flush=True)
        rc = 0
    finally:
        terminate_children()
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="Dev-серверы проекта")
    ap.add_argument("--backend-only", action="store_true", help="только FastAPI (uvicorn)")
    ap.add_argument("--frontend-only", action="store_true", help="только Vite")
    ap.add_argument(
        "--port",
        type=int,
        default=None,
        metavar="N",
        help="порт бэкенда (иначе BACKEND_PORT из окружения или .env, по умолчанию 8000)",
    )
    ap.add_argument(
        "--install",
        action="store_true",
        help="перед фронтендом выполнить npm install в frontend/",
    )
    args = ap.parse_args()

    if args.backend_only and args.frontend_only:
        print("[dev] нельзя одновременно --backend-only и --frontend-only", file=sys.stderr)
        return 2

    port = resolve_backend_port(args.port)
    needs_frontend = not args.backend_only

    if needs_frontend:
        if args.install:
            rc = install_frontend_deps()
            if rc != 0:
                return rc
        if not _frontend_deps_ready():
            print(
                "[dev] Не найдены зависимости фронтенда (нет frontend/node_modules/vite).\n"
                "    Установите:  npm install --prefix frontend\n"
                "    или из корня: npm run install:frontend\n"
                "    или одной командой:  python scripts/dev.py --frontend-only --install",
                file=sys.stderr,
                flush=True,
            )
            return 1

    if args.backend_only:
        return run_backend(port)
    if args.frontend_only:
        return run_frontend()
    return run_both(port)


if __name__ == "__main__":
    raise SystemExit(main())
