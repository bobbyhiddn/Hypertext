"""Offline request/response contract tests for Gemini image paths."""

import base64
import io
import json
import os
import tempfile
import types as ns
import unittest
import urllib.error
from unittest import mock

from hypertext.gemini import image, style
from hypertext.gemini.config import DEFAULT_IMAGE_MODEL, image_endpoint, image_model


PNG = b"\x89PNG\r\n\x1a\ncontract"


class HttpResponse:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self): return json.dumps(self.payload).encode()


class RestContractTests(unittest.TestCase):
    def run_generate(self, responses):
        captured = []
        def open_fake(req, timeout):
            captured.append(req)
            value = responses.pop(0)
            if isinstance(value, Exception): raise value
            return HttpResponse(value)
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(os.environ, {
            "GEMINI_API_KEY": "fake", "GEMINI_MAX_ATTEMPTS": "3",
            "GEMINI_RETRY_BASE_DELAY_S": "0"}, clear=True), \
             mock.patch.object(image.urllib.request, "urlopen", side_effect=open_fake), \
             mock.patch.object(image.time, "sleep"):
            path = os.path.join(td, "out.png")
            image.generate_image("prompt", path)
            with open(path, "rb") as f: result = f.read()
        return result, captured

    def test_success_request_and_interleaved_response(self):
        payload = {"candidates": [{"content": {"parts": [
            {"text": "done"}, {"inlineData": {"mimeType": "image/png",
             "data": base64.b64encode(PNG).decode()}}]}}]}
        result, requests = self.run_generate([payload])
        self.assertEqual(result, PNG)
        self.assertEqual(requests[0].full_url, image_endpoint())
        body = json.loads(requests[0].data)
        self.assertEqual(body["generationConfig"]["imageConfig"],
                         {"aspectRatio": "2:3", "imageSize": "2K"})

    def test_missing_and_malformed_image_data(self):
        cases = [
            ({"candidates": []}, "No candidates"),
            ({"candidates": [{"content": {"parts": [{"text": "only"}]}}]}, "No image"),
            ({"candidates": [{"content": {"parts": [{"inlineData": {
                "mimeType": "image/png", "data": "%%%"}}]}}]}, "malformed base64"),
        ]
        for payload, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(RuntimeError, message):
                self.run_generate([payload])

    def test_transient_http_error_retries(self):
        err = urllib.error.HTTPError("url", 503, "busy", {"Retry-After": "0"}, io.BytesIO(b"{}"))
        result, requests = self.run_generate([err, {"candidates": [{"content": {"parts": [
            {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(PNG).decode()}}
        ]}}]}])
        self.assertEqual(result, PNG)
        self.assertEqual(len(requests), 2)

    def test_permanent_http_error_is_not_retried(self):
        err = urllib.error.HTTPError("url", 400, "bad", {}, io.BytesIO(b"bad request"))
        with self.assertRaisesRegex(RuntimeError, "HTTP 400"), mock.patch.dict(os.environ, {
            "GEMINI_API_KEY": "fake"}, clear=True), mock.patch.object(
                image.urllib.request, "urlopen", side_effect=err) as opened:
            image.generate_image("prompt", "unused.png")
        opened.assert_called_once()


class FakePart:
    @staticmethod
    def from_bytes(data, mime_type): return ns.SimpleNamespace(data=data, mime_type=mime_type)
    @staticmethod
    def from_text(text): return ns.SimpleNamespace(text=text)


class SdkContractTests(unittest.TestCase):
    def run_generate(self, responses):
        calls = []
        def generate_content(**kwargs):
            calls.append(kwargs)
            value = responses.pop(0)
            if isinstance(value, Exception): raise value
            return value
        client = ns.SimpleNamespace(models=ns.SimpleNamespace(generate_content=generate_content))
        fake_genai = ns.SimpleNamespace(Client=lambda api_key: client)
        fake_types = ns.SimpleNamespace(Part=FakePart,
            GenerateContentConfig=lambda **kwargs: kwargs)
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(os.environ, {
            "GEMINI_API_KEY": "fake", "GEMINI_MAX_ATTEMPTS": "3",
            "GEMINI_RETRY_BASE_DELAY_S": "0"}, clear=True), \
             mock.patch.object(style, "genai", fake_genai), \
             mock.patch.object(style, "types", fake_types), \
             mock.patch.object(style.time, "sleep"):
            ref = os.path.join(td, "ref.png")
            with open(ref, "wb") as f: f.write(PNG)
            out = os.path.join(td, "out.png")
            style.generate_with_styles("prompt", [ref], out)
            with open(out, "rb") as f: result = f.read()
        return result, calls

    def test_success_and_default_model(self):
        inline = ns.SimpleNamespace(mime_type="image/png", data=PNG)
        response = ns.SimpleNamespace(candidates=[ns.SimpleNamespace(
            content=ns.SimpleNamespace(parts=[ns.SimpleNamespace(inline_data=inline)]))])
        result, calls = self.run_generate([response])
        self.assertEqual(result, PNG)
        self.assertEqual(calls[0]["model"], DEFAULT_IMAGE_MODEL)
        self.assertEqual(calls[0]["config"]["response_modalities"], ["IMAGE"])

    def test_missing_and_malformed_image_data(self):
        cases = [
            (ns.SimpleNamespace(candidates=[]), "No candidates"),
            (ns.SimpleNamespace(candidates=[ns.SimpleNamespace(content=ns.SimpleNamespace(
                parts=[ns.SimpleNamespace(inline_data=None)]))]), "No image data"),
            (ns.SimpleNamespace(candidates=[ns.SimpleNamespace(content=ns.SimpleNamespace(
                parts=[ns.SimpleNamespace(inline_data=ns.SimpleNamespace(
                    mime_type="image/png", data="%%%"))]))]), "malformed base64"),
        ]
        for response, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(RuntimeError, message):
                self.run_generate([response])

    def test_retry_and_api_error(self):
        transient = RuntimeError("busy"); transient.status_code = 503
        response = ns.SimpleNamespace(candidates=[ns.SimpleNamespace(content=ns.SimpleNamespace(
            parts=[ns.SimpleNamespace(inline_data=ns.SimpleNamespace(
                mime_type="image/png", data=PNG))]))])
        _, calls = self.run_generate([transient, response])
        self.assertEqual(len(calls), 2)
        permanent = RuntimeError("denied"); permanent.status_code = 401
        with self.assertRaisesRegex(RuntimeError, "API request failed"):
            self.run_generate([permanent])


class ConfigurationTests(unittest.TestCase):
    def test_environment_override(self):
        with mock.patch.dict(os.environ, {"GEMINI_IMAGE_MODEL": "custom"}):
            self.assertEqual(image_model(), "custom")

    def test_no_preview_image_defaults_and_daily_is_manual_only(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        runtime_paths = ["package/hypertext", "scripts", "utils",
                         "templates/card/meta.yml", "templates/lot/meta.yml"]
        for relative in runtime_paths:
            path = os.path.join(root, relative)
            files = ([path] if os.path.isfile(path) else [
                os.path.join(base, name) for base, _, names in os.walk(path)
                for name in names if name.endswith((".py", ".yml", ".yaml", ".md"))])
            for filename in files:
                if filename == __file__:
                    continue
                with open(filename, encoding="utf-8") as f:
                    self.assertNotIn("gemini-3.1-flash-image-preview", f.read(), filename)
        workflow = os.path.join(root, ".github/workflows/daily-hypertext.yml")
        with open(workflow, encoding="utf-8") as f:
            self.assertNotRegex(f.read(), r"(?m)^\s*schedule\s*:")


if __name__ == "__main__":
    unittest.main()
