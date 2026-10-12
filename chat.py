#!/usr/bin/env python3
"""Text-only Linux chat client. No tools, subprocesses, or application writes."""
import argparse
import json
import os
import re
import ssl
import stat
import sys
import time
import unicodedata

import httpx

# IT must review and hardcode the exact production HTTPS URL here.
ALLOWED_ENDPOINTS = frozenset()
LOCAL_ENDPOINT = "http://127.0.0.1:11434/v1/chat/completions"
MAX_CONFIG, MAX_LINE, MAX_INPUT = 16384, 65536, 8192
MAX_WIRE, MAX_REPLY, MAX_HISTORY = 1048576, 65536, 131072


class ChatError(Exception):
    pass


def clean(text):
    return "".join(c for c in text if c in "\n\t" or
                   not unicodedata.category(c).startswith("C"))


def configuration(path, local_test):
    if not sys.platform.startswith("linux"):
        raise ChatError("Linux krävs för verifierad filbehörighetskontroll.")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as source:
        info = os.fstat(source.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise ChatError("Konfig måste vara din vanliga fil med 0600 och en länk.")
        raw = source.read(MAX_CONFIG + 1)
    if len(raw) > MAX_CONFIG:
        raise ChatError("Konfigfilen är för stor.")
    try:
        cfg = json.loads(raw)
    except (ValueError, UnicodeError, RecursionError):
        raise ChatError("Konfigfilen måste innehålla giltig UTF-8 JSON.") from None
    if not isinstance(cfg, dict) or set(cfg) - {"endpoint", "model", "token"}:
        raise ChatError("Tillåtna konfigfält: endpoint, model, token.")
    endpoint, model = cfg.get("endpoint"), cfg.get("model")
    if not isinstance(endpoint, str) or not (
        endpoint in ALLOWED_ENDPOINTS and endpoint.startswith("https://")
        or local_test and endpoint == LOCAL_ENDPOINT
    ):
        raise ChatError("Endpoint spärrad av hårdkodad allowlist.")
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,128}", model):
        raise ChatError("Ange ett giltigt, lokalt installerat modellnamn.")
    if model == "REPLACE_WITH_INSTALLED_LOCAL_MODEL" or "cloud" in model.lower():
        raise ChatError("Välj en installerad lokal modell; cloud-modeller är spärrade.")
    token = os.environ.get("OLLAMA_API_KEY", cfg.get("token", ""))
    if not isinstance(token, str) or (token and not re.fullmatch(r"[A-Za-z0-9._~+/-]+=*", token)) or len(token) > 4096:
        raise ChatError("Token har ogiltigt format.")
    if endpoint == LOCAL_ENDPOINT and token:
        raise ChatError("Lokaltest skickar ingen token. Ta bort token och miljövariabeln.")
    if endpoint != LOCAL_ENDPOINT and not token:
        raise ChatError("HTTPS-proxyn kräver token i konfig eller OLLAMA_API_KEY.")
    return endpoint, model, token


def events(response):
    """Bound SSE lines/events and total raw bytes before JSON parsing."""
    pending, data, total = b"", [], 0
    started = time.monotonic()
    for chunk in response.iter_raw(chunk_size=None):
        total += len(chunk)
        if total > MAX_WIRE or time.monotonic() - started > 180:
            raise ChatError("Svar överskred storleks- eller tidsgränsen.")
        pending += chunk
        while b"\n" in pending:
            line, pending = pending.split(b"\n", 1)
            if len(line) > MAX_LINE:
                raise ChatError("För lång SSE-rad.")
            line = line.removesuffix(b"\r")
            if not line:
                if data:
                    yield b"\n".join(data).decode("utf-8", errors="strict")
                    data = []
            elif line.startswith(b"data:"):
                data.append(line[5:].removeprefix(b" "))
                if sum(map(len, data)) > MAX_LINE:
                    raise ChatError("För stor SSE-händelse.")
        if len(pending) > MAX_LINE:
            raise ChatError("För lång SSE-rad.")
    raise ChatError("Strömmen bröts före [DONE]; historiken har inte ändrats.")


def answer(client, endpoint, model, token, messages, emit):
    headers = {"Accept": "text/event-stream", "Accept-Encoding": "identity"}
    if token:
        headers["Authorization"] = "Bearer " + token
    parts, size, finished = [], 0, False
    with client.stream("POST", endpoint, headers=headers, json={
        "model": model, "messages": messages, "stream": True, "max_tokens": 2048,
    }) as response:
        if response.status_code != 200:
            reason = {401: "Ogiltig token", 403: "Åtkomst nekad", 404: "Modell eller sökväg saknas",
                      429: "För många anrop"}.get(response.status_code, "API-anrop misslyckades")
            raise ChatError(f"{reason} (HTTP {response.status_code}); ingen automatisk retry.")
        if response.headers.get("content-type", "").split(";")[0].strip() != "text/event-stream":
            raise ChatError("Servern skickade inte SSE.")
        if response.headers.get("content-encoding", "identity") != "identity":
            raise ChatError("Komprimerad ström accepteras inte.")
        for event in events(response):
            if event == "[DONE]":
                if not finished:
                    raise ChatError("Svar saknar normalt avslut.")
                return "".join(parts)
            try:
                item = json.loads(event)
                if "error" in item:
                    raise ChatError("Servern rapporterade ett fel i strömmen.")
                choices = item["choices"]
                if choices == []:  # Optional usage event.
                    continue
                if len(choices) != 1 or finished:
                    raise ValueError()
                choice = choices[0]
                delta = choice["delta"]
                if "tool_calls" in delta or "function_call" in delta:
                    raise ChatError("Verktygsanrop är förbjudna.")
                content = delta.get("content") or ""
                if not isinstance(content, str):
                    raise ValueError()
                reason = choice.get("finish_reason")
                if reason is not None:
                    if reason != "stop":
                        raise ChatError("Svaret avslutades ofullständigt; historiken har inte ändrats.")
                    finished = True
            except (ValueError, KeyError, TypeError, AttributeError, RecursionError):
                raise ChatError("Ogiltigt JSON-format i strömmen.") from None
            size += len(content)
            if size > MAX_REPLY:
                raise ChatError("Svaret är för långt.")
            parts.append(content)
            emit(clean(content))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="JSON-fil med exakt 0600")
    parser.add_argument("--local-test", action="store_true", help="Tillåt enbart exakt loopback-URL utan token")
    parser.add_argument("--check", action="store_true", help="Kontrollera konfig utan nätverk")
    parser.add_argument("--markdown", action="store_true", help="Rendera också färdigt svar med Rich på TTY")
    args = parser.parse_args()
    try:
        endpoint, model, token = configuration(args.config, args.local_test)
        if args.check:
            print("Konfiguration OK. Ingen anslutning gjord.")
            return 0
        renderer = None
        if args.markdown and sys.stdout.isatty():
            try:
                from rich.console import Console
                from rich.markdown import Markdown
            except ImportError:
                raise ChatError("Markdown kräver requirements-markdown.txt.") from None
            renderer = Console(highlight=False)
        history, interactive = [], sys.stdin.isatty()
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        tls.load_verify_locations(cafile="/etc/ssl/certs/ca-certificates.crt")
        with httpx.Client(trust_env=False, follow_redirects=False,
                          verify=tls,
                          timeout=httpx.Timeout(30, connect=5),
                          limits=httpx.Limits(max_connections=1)) as client:
            if interactive:
                print("Textassistent · /clear tömmer minnet · /exit avslutar", file=sys.stderr)
            while True:
                if interactive:
                    print("Du> ", end="", flush=True, file=sys.stderr)
                prompt = sys.stdin.readline(MAX_INPUT + 2)
                if not prompt:
                    return 0
                if len(prompt) > MAX_INPUT + 1:
                    raise ChatError("Indataraden är för lång; avslutar utan att skicka den.")
                prompt = prompt.rstrip("\r\n")
                if prompt == "/exit":
                    return 0
                if prompt == "/clear":
                    history.clear()
                    print("Historiken tömd.", file=sys.stderr)
                    continue
                if not prompt.strip():
                    continue
                if sum(len(m["content"]) for m in history) + len(prompt) + MAX_REPLY > MAX_HISTORY:
                    raise ChatError("Minneshistoriken är full. Starta om eller använd /clear tidigare.")
                messages = history + [{"role": "user", "content": prompt}]
                reply = answer(client, endpoint, model, token, messages,
                               lambda text: print(text, end="", flush=True))
                print()
                if renderer:
                    renderer.print(Markdown(clean(reply), hyperlinks=False))
                history = messages + [{"role": "assistant", "content": reply}]
    except KeyboardInterrupt:
        print("\nAvbrutet. Sessionen avslutad.", file=sys.stderr)
        return 130
    except (ChatError, OSError, UnicodeError, httpx.HTTPError) as error:
        if isinstance(error, ChatError):
            message = str(error)
        elif isinstance(error, httpx.TimeoutException):
            message = "Servern svarade inte i tid. Ingen automatisk retry gjordes."
        elif isinstance(error, httpx.ConnectError):
            message = "Anslutning eller TLS misslyckades. Kontrollera server, nätverk och intern CA."
        elif isinstance(error, httpx.HTTPError):
            message = "Nätverksfel eller bruten HTTP-ström. Sessionen avslutad."
        elif isinstance(error, UnicodeError):
            message = "Ogiltig textkodning i indata eller svar. UTF-8 krävs."
        else:
            message = "Kunde inte läsa konfig/CA eller använda terminalen. Kontrollera sökväg och rättigheter."
        print("\nFel: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
