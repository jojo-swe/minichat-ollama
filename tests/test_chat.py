import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import httpx
import chat


def sse(content="Hej 🌲", reason="stop"):
    return ("data: " + json.dumps({"choices": [{"delta": {"content": content},
            "finish_reason": reason}]}, ensure_ascii=False) + "\r\n\r\ndata: [DONE]\r\n\r\n").encode()


class Chunks(httpx.SyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks

    def __iter__(self):
        yield from self.chunks


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "config.json"
        self.path.write_text(json.dumps({"endpoint": chat.LOCAL_ENDPOINT, "model": "local:8b"}))
        self.path.chmod(0o600)
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_valid(self):
        self.assertEqual(chat.configuration(self.path, True), (chat.LOCAL_ENDPOINT, "local:8b", ""))

    def test_local_opt_in(self):
        with self.assertRaises(chat.ChatError):
            chat.configuration(self.path, False)

    def test_permissions(self):
        for mode in (0o644, 0o400, 0o660, 0o4600):
            self.path.chmod(mode)
            with self.assertRaises(chat.ChatError):
                chat.configuration(self.path, True)

    def test_symlink(self):
        link = self.path.with_name("link")
        link.symlink_to(self.path)
        with self.assertRaises(OSError):
            chat.configuration(link, True)

    def test_hardlink(self):
        os.link(self.path, self.path.with_name("other"))
        with self.assertRaises(chat.ChatError):
            chat.configuration(self.path, True)

    def test_owner(self):
        with patch.object(chat.os, "getuid", return_value=os.getuid() + 1):
            with self.assertRaises(chat.ChatError):
                chat.configuration(self.path, True)

    def test_no_token_on_http(self):
        os.environ["OLLAMA_API_KEY"] = "secret"
        with self.assertRaises(chat.ChatError):
            chat.configuration(self.path, True)

    def test_exact_url(self):
        for url in (chat.LOCAL_ENDPOINT + "?x=1", chat.LOCAL_ENDPOINT + "/",
                    "http://localhost:11434/v1/chat/completions", "https://evil.example/v1/chat/completions"):
            self.path.write_text(json.dumps({"endpoint": url, "model": "local"}))
            with self.assertRaises(chat.ChatError):
                chat.configuration(self.path, True)

    def test_https_token_precedence_and_injection(self):
        url = "https://internal.example/v1/chat/completions"
        self.path.write_text(json.dumps({"endpoint": url, "model": "local", "token": "file-secret"}))
        with patch.object(chat, "ALLOWED_ENDPOINTS", frozenset({url})):
            self.assertEqual(chat.configuration(self.path, False)[2], "file-secret")
            os.environ["OLLAMA_API_KEY"] = "env-secret"
            self.assertEqual(chat.configuration(self.path, False)[2], "env-secret")
            os.environ["OLLAMA_API_KEY"] = "secret\r\nInjected: yes"
            with self.assertRaises(chat.ChatError):
                chat.configuration(self.path, False)

    def test_invalid_configs(self):
        for value in ("[]", "{", "x" * (chat.MAX_CONFIG + 1),
                      '{"endpoint": null}', '{"unknown": 1}'):
            self.path.write_text(value)
            with self.assertRaises(chat.ChatError):
                chat.configuration(self.path, True)

    def test_deep_json(self):
        self.path.write_text("[" * 2000 + "]" * 2000)
        with self.assertRaises(chat.ChatError):
            chat.configuration(self.path, True)

    def test_fifo_no_block(self):
        fifo = self.path.with_name("fifo")
        os.mkfifo(fifo, 0o600)
        with self.assertRaises(chat.ChatError):
            chat.configuration(fifo, True)


class StreamTests(unittest.TestCase):
    def run_answer(self, body=None, status=200, headers=None):
        self.requests, self.output = [], []
        def handler(request):
            self.requests.append(request)
            return httpx.Response(status, headers=headers or {"content-type": "text/event-stream"},
                                  stream=Chunks([bytes([b]) for b in (sse() if body is None else body)]))
        with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False) as client:
            return chat.answer(client, "https://internal.example/v1/chat/completions", "local", "secret",
                               [{"role": "user", "content": "Hej"}], self.output.append)

    def test_valid_split_stream_and_request(self):
        self.assertEqual(self.run_answer(), "Hej 🌲")
        self.assertEqual("".join(self.output), "Hej 🌲")
        request = self.requests[0]
        self.assertEqual(request.headers["authorization"], "Bearer secret")
        self.assertEqual(set(json.loads(request.content)), {"model", "messages", "stream", "max_tokens"})

    def test_multiline_and_comment(self):
        body = b': heartbeat\n\ndata: {"choices":\ndata: [{"delta":{"content":"ok"},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n'
        self.assertEqual(self.run_answer(body), "ok")

    def test_truncated_and_malformed(self):
        for body in (b"", b"data: [DONE]\n\n", b"data: bad\n\n", sse().split(b"data: [DONE]")[0],
                     b'data: {"choices":[{"delta":null}]}\n\n', sse(reason="length")):
            with self.assertRaises(chat.ChatError):
                self.run_answer(body)

    def test_tool_calls(self):
        with self.assertRaisesRegex(chat.ChatError, "Verktygsanrop"):
            self.run_answer(b'data: {"choices":[{"delta":{"tool_calls":[]}}]}\n\n')

    def test_limits(self):
        with patch.object(chat, "MAX_LINE", 16):
            with self.assertRaises(chat.ChatError):
                self.run_answer(b"x" * 17)
        with patch.object(chat, "MAX_WIRE", 16):
            with self.assertRaises(chat.ChatError):
                self.run_answer()
        with patch.object(chat, "MAX_REPLY", 2):
            with self.assertRaises(chat.ChatError):
                self.run_answer()

    def test_status_and_no_redirect(self):
        for status in (302, 401, 403, 404, 429, 500):
            with self.assertRaises(chat.ChatError) as caught:
                self.run_answer(b"secret backend text", status, {"location": "https://evil.example"})
            self.assertNotIn("secret", str(caught.exception))
            self.assertEqual(len(self.requests), 1)

    def test_content_type_and_compression(self):
        for headers in ({"content-type": "text/html"}, {"content-type": "text/event-stream", "content-encoding": "gzip"}):
            with self.assertRaises(chat.ChatError):
                self.run_answer(headers=headers)

    def test_terminal_controls(self):
        content = "\x1b[31mred\x07\x9b\u202eevil\r\b"
        self.run_answer(sse(content))
        self.assertEqual("".join(self.output), "[31mredevil")

    def test_deadline(self):
        with patch.object(chat.time, "monotonic", side_effect=[0, 181]):
            with self.assertRaises(chat.ChatError):
                self.run_answer()

    def test_deep_stream_json(self):
        with self.assertRaises(chat.ChatError):
            self.run_answer(b"data: " + b"[" * 2000 + b"]" * 2000 + b"\n\n")

    def test_markdown_sanitized_no_hyperlinks(self):
        from rich.console import Console
        from rich.markdown import Markdown
        output = io.StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        console.print(Markdown(chat.clean("# Hej\n\x1b]52;c;evil\x07\n[Link](https://example.com)"), hyperlinks=False))
        rendered = output.getvalue()
        self.assertIn("Hej", rendered)
        self.assertNotIn("\x1b]", rendered)

    def test_timeout_propagates_without_history_mutation(self):
        messages = [{"role": "user", "content": "hello"}]
        def fail(request):
            raise httpx.ReadTimeout("sensitive raw error")
        with httpx.Client(transport=httpx.MockTransport(fail)) as client:
            with self.assertRaises(httpx.ReadTimeout):
                chat.answer(client, chat.LOCAL_ENDPOINT, "local", "", messages, lambda text: None)
        self.assertEqual(messages, [{"role": "user", "content": "hello"}])


class CLITests(unittest.TestCase):
    def test_history_clear_pipe_and_env_proxy(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                self.wfile.write(sse("Svar"))
        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "config.json"
                path.write_text(json.dumps({"endpoint": chat.LOCAL_ENDPOINT, "model": "local"}))
                path.chmod(0o600)
                real_client = httpx.Client
                def local_client(**kwargs):
                    # Map only the test transport; production allowlist remains unchanged.
                    class Transport(httpx.HTTPTransport):
                        def handle_request(self, request):
                            request.url = request.url.copy_with(port=server.server_port)
                            return super().handle_request(request)
                    return real_client(transport=Transport(), **kwargs)
                output = io.StringIO()
                with patch.object(sys, "argv", ["chat.py", "--config", str(path), "--local-test", "--markdown"]), \
                     patch.object(sys, "stdin", io.StringIO("ett\ntvå\n/clear\ntre\n/exit\n")), \
                     patch.object(sys, "stdout", output), patch.object(chat.httpx, "Client", side_effect=local_client), \
                     patch.dict(os.environ, {"HTTP_PROXY": "http://127.0.0.1:1", "OLLAMA_API_KEY": ""}):
                    self.assertEqual(chat.main(), 0)
                self.assertEqual(output.getvalue(), "Svar\nSvar\nSvar\n")
                self.assertEqual([len(r["messages"]) for r in received], [1, 3, 1])
            server.shutdown()
            worker.join()


if __name__ == "__main__":
    unittest.main()
