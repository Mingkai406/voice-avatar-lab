#!/usr/bin/env python3
"""Install a pinned, repository-local runtime. Run sample mode without ML packages."""

import argparse, json, os, platform, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "models.lock.json").read_text())


def run(*args):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)


def fetch_source(name):
    entry = MANIFEST["sources"][name]
    dest = ROOT / entry["path"]
    if dest.exists():
        check = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True, capture_output=True)
        if check.returncode == 0:
            if check.stdout.strip() != entry["revision"]:
                raise RuntimeError(
                    f"{dest.name} exists at a different revision. Move it aside before setup; it was not reset."
                )
            print(f"{name}: pinned source present")
            return
        if not (dest / ".git").exists():
            raise RuntimeError(f"{dest.name} exists but is not a source checkout; move it aside before setup.")
        print(f"{name}: resuming an incomplete checkout")
    else:
        dest.mkdir(parents=True)
        run("git", "-C", dest, "init", "-q")
        run("git", "-C", dest, "remote", "add", "origin", entry["url"])
    if entry.get("sparse"):
        run("git", "-C", dest, "config", "core.sparseCheckout", "true")
        (dest / ".git/info/sparse-checkout").write_text("\n".join("/" + p for p in entry["sparse"]) + "\n")
    run("git", "-C", dest, "fetch", "--depth", "1", "--filter=blob:none", "origin", entry["revision"])
    run("git", "-C", dest, "checkout", "--detach", "FETCH_HEAD")


def get_uv():
    found = shutil.which("uv")
    if found:
        return found
    bootstrap = ROOT / ".bootstrap"
    if not bootstrap.exists():
        run(sys.executable, "-m", "venv", bootstrap)
    python = bootstrap / "bin/python"
    run(python, "-m", "pip", "install", "uv==0.8.22")
    return bootstrap / "bin/uv"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["sample", "full"], default="sample")
    parser.add_argument(
        "--skip-models", action="store_true", help="Install environments/source only; download models later"
    )
    args = parser.parse_args()
    if not shutil.which("git"):
        raise SystemExit("Install Git first, then rerun setup.")
    if args.profile == "full" and (platform.system() != "Darwin" or platform.machine() != "arm64"):
        raise SystemExit("Full mode currently requires Apple Silicon macOS. Use --profile sample on other systems.")
    fetch_source("DH_live")
    if args.profile == "sample":
        print("\nReady: python3 run.py --sample\nOpen http://127.0.0.1:8765")
        return
    uv = get_uv()
    for env, lock in [(".venv", "macos.lock.txt"), (".venv-tts", "neural.lock.txt")]:
        if not (ROOT / env).exists():
            run(uv, "venv", "--python", "3.12", ROOT / env)
        run(uv, "pip", "install", "--python", ROOT / env / "bin/python", "-r", ROOT / "requirements" / lock)
    fetch_source("LivePortrait")
    if not args.skip_models:
        run(ROOT / ".venv/bin/python", ROOT / "scripts/download_models.py")
    run(ROOT / ".venv/bin/python", ROOT / "scripts/prepare_portrait.py")
    if args.skip_models:
        print(
            "\nEnvironments ready. Download weights with .venv/bin/python scripts/download_models.py before full inference."
        )
    else:
        print("\nReady: .venv/bin/python run.py\nOptional provider configuration: copy .env.example to .env")


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, RuntimeError) as e:
        raise SystemExit(f"Setup stopped: {e}. Fix the reported step and rerun; no working checkout is reset.")
