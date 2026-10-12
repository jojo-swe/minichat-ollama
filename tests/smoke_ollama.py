"""Opt-in real inference smoke test; uses a temporary config, never a user token."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

# Run on Linux: python -B tests/smoke_ollama.py INSTALLED_MODEL
with tempfile.TemporaryDirectory() as directory:
    config = Path(directory) / "config.json"
    config.write_text(json.dumps({"endpoint": "http://127.0.0.1:11434/v1/chat/completions",
                                  "model": sys.argv[1]}))
    config.chmod(0o600)
    env = dict(os.environ)
    env.pop("OLLAMA_API_KEY", None)
    result = subprocess.run([sys.executable, "-B", "chat.py", "--config", str(config), "--local-test"],
                            input="Svara endast med ordet HEJ. /no_think\n/exit\n", text=True,
                            env=env, timeout=220)
    sys.exit(result.returncode)
