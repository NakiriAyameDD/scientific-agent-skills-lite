#!/usr/bin/env python3
"""
Deploy local repository skills to the Antigravity plugin installation directory:
~/.gemini/config/plugins/scientific-agent-skills/
"""

import os
import shutil
import urllib.request
import json
from pathlib import Path

def deploy():
    repo_root = Path(__file__).resolve().parents[1]
    home_dir = Path.home()
    target_dir = home_dir / ".gemini" / "config" / "plugins" / "scientific-agent-skills"

    print(f"[*] Deploying from {repo_root} -> {target_dir}...")
    target_dir.mkdir(parents=True, exist_ok=True)

    items = ["plugin.json", "README.md", "LICENSE.md", "assets", "skills"]
    for item in items:
        src = repo_root / item
        dst = target_dir / item
        if not src.exists():
            continue
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        print(f" [+] Synced {item}")

    print("\n[+] Deployment finished.")

    # Try verifying with Antigravity Language Server
    ls_address = os.environ.get("ANTIGRAVITY_LS_ADDRESS")
    csrf_token = os.environ.get("ANTIGRAVITY_CSRF_TOKEN")
    if ls_address and csrf_token:
        try:
            url = f"http://{ls_address}/exa.language_server_pb.LanguageServerService/GetAllPlugins"
            req = urllib.request.Request(
                url,
                data=b"{}",
                headers={"Content-Type": "application/json", "x-codeium-csrf-token": csrf_token},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for p in data.get("plugins", []):
                    if p.get("name") == "scientific-agent-skills":
                        skills_len = len(p.get("skills", []))
                        print(f"[+] Antigravity Language Server re-scanned: {skills_len} skills active.")
        except Exception as e:
            print(f"[*] Note: Language Server verification skipped: {e}")

if __name__ == "__main__":
    deploy()
