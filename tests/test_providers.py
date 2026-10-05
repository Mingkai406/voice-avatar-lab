import json, os, sys, threading, unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from avatar_lab.providers import OpenAICompatibleProvider, create_provider


class Handler(BaseHTTPRequestHandler):
    received = None
    response = {"choices": [{"message": {"content": "A different model reply"}}]}
    status = 200

    def log_message(self, *args):
        pass

    def do_POST(self):
        type(self).received = {
            "path": self.path,
            "body": json.loads(self.rfile.read(int(self.headers["Content-Length"]))),
            "auth": self.headers.get("Authorization"),
        }
        raw = json.dumps(self.response).encode()
        self.send_response(self.status)
        self.end_headers()
        self.wfile.write(raw)


class ProviderTests(unittest.TestCase):
    def setUp(self):
        Handler.status = 200
        Handler.response = {"choices": [{"message": {"content": "A different model reply"}}]}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.env = patch.dict(
            os.environ,
            {
                "AVATAR_LLM_MODEL": "test-model",
                "AVATAR_LLM_BASE_URL": f"http://127.0.0.1:{self.server.server_port}/v1",
                "AVATAR_LLM_API_KEY": "synthetic-test-key",
            },
        )
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_api_contract(self):
        messages = [{"role": "user", "content": "Hello"}]
        text = OpenAICompatibleProvider().generate(messages, max_tokens=20, temperature=0.2)
        self.assertEqual(text, "A different model reply")
        self.assertEqual(Handler.received["path"], "/v1/chat/completions")
        self.assertEqual(Handler.received["body"]["messages"], messages)
        self.assertEqual(Handler.received["body"]["model"], "test-model")
        self.assertEqual(Handler.received["auth"], "Bearer synthetic-test-key")

    def test_error_body_not_exposed(self):
        Handler.status = 401
        Handler.response = {"error": "secret request details"}
        with self.assertRaisesRegex(ValueError, "HTTP 401") as ctx:
            OpenAICompatibleProvider().generate([])
        self.assertNotIn("secret", str(ctx.exception))

    def test_bad_schema(self):
        Handler.response = {"choices": []}
        with self.assertRaisesRegex(ValueError, "choices"):
            OpenAICompatibleProvider().generate([])

    def test_unknown_provider_rejected(self):
        with patch.dict(os.environ, {"AVATAR_LLM_PROVIDER": "unregistered"}):
            with self.assertRaises(ValueError):
                create_provider(ROOT)

    def test_sample_overrides_configuration(self):
        self.assertEqual(create_provider(ROOT, sample=True).name, "fixtures")


if __name__ == "__main__":
    unittest.main()
