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

from PIL import Image

from hypertext.gemini import image, review, style
from hypertext.gemini.config import (DEFAULT_IMAGE_MODEL, DEFAULT_REVIEW_MODEL,
                                     DEFAULT_TEXT_MODEL, image_endpoint, image_model,
                                     review_model, text_model)
from hypertext.gemini.image_contract import decode_and_validate


def png(width=1024, height=1536):
    stream = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(stream, "PNG")
    return stream.getvalue()


def jpeg(width=1024, height=1536):
    stream = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(stream, "JPEG")
    return stream.getvalue()


PNG = png()


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
            ({"candidates": [{"content": {"parts": [{"inlineData": {
                "mimeType": "image/jpeg", "data": base64.b64encode(PNG).decode()}}]}}]}, "MIME"),
            ({"candidates": [{"content": {"parts": [{"inlineData": {
                "mimeType": "image/png", "data": base64.b64encode(b"broken").decode()}}]}}]}, "corrupt"),
            ({"candidates": [{"content": {"parts": [{"inlineData": {
                "mimeType": "image/png", "data": base64.b64encode(png(100, 150)).decode()}}]}}]}, "dimensions"),
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
        with tempfile.TemporaryDirectory() as td, self.assertRaisesRegex(RuntimeError, "HTTP 400"), \
             mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake"}, clear=True), \
             mock.patch.object(image.urllib.request, "urlopen", side_effect=err) as opened:
            image.generate_image("prompt", os.path.join(td, "unused.png"))
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
            GenerateContentConfig=lambda **kwargs: kwargs,
            ImageConfig=lambda **kwargs: kwargs)
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
        self.assertEqual(calls[0]["config"]["image_config"],
                         {"aspect_ratio": "2:3", "image_size": "2K"})

    def test_missing_and_malformed_image_data(self):
        cases = [
            (ns.SimpleNamespace(candidates=[]), "No candidates"),
            (ns.SimpleNamespace(candidates=[ns.SimpleNamespace(content=ns.SimpleNamespace(
                parts=[ns.SimpleNamespace(inline_data=None)]))]), "No image data"),
            (ns.SimpleNamespace(candidates=[ns.SimpleNamespace(content=ns.SimpleNamespace(
                parts=[ns.SimpleNamespace(inline_data=ns.SimpleNamespace(
                    mime_type="image/png", data="%%%"))]))]), "malformed base64"),
            (ns.SimpleNamespace(candidates=[ns.SimpleNamespace(content=ns.SimpleNamespace(
                parts=[ns.SimpleNamespace(inline_data=ns.SimpleNamespace(
                    mime_type="text/plain", data=PNG))]))]), "MIME"),
            (ns.SimpleNamespace(candidates=[ns.SimpleNamespace(content=ns.SimpleNamespace(
                parts=[ns.SimpleNamespace(inline_data=ns.SimpleNamespace(
                    mime_type="image/png", data=b"broken"))]))]), "corrupt"),
            (ns.SimpleNamespace(candidates=[ns.SimpleNamespace(content=ns.SimpleNamespace(
                parts=[ns.SimpleNamespace(inline_data=ns.SimpleNamespace(
                    mime_type="image/png", data=png(100, 150)))]))]), "dimensions"),
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
    def test_success_metadata_records_latency_and_available_usage(self):
        from hypertext.gemini.image_contract import record_success
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "card.png")
            record_success(out, model="model", mime_type="image/jpeg",
                           dimensions=(1024, 1536), attempts=1, reference_count=3,
                           latency_ms=1234, usage_metadata={"totalTokenCount": 99})
            with open(os.path.join(td, "generation.json"), encoding="utf-8") as f:
                metadata = json.load(f)
        self.assertEqual(metadata["latency_ms"], 1234)
        self.assertEqual(metadata["usage_metadata"], {"totalTokenCount": 99})

    def test_success_metadata_records_usage_absence_explicitly(self):
        from hypertext.gemini.image_contract import record_success
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "card.png")
            record_success(out, model="model", mime_type="image/png",
                           dimensions=(1024, 1536), attempts=1, reference_count=0)
            with open(os.path.join(td, "generation.json"), encoding="utf-8") as f:
                metadata = json.load(f)
        self.assertIsNone(metadata["usage_metadata"])

    def test_environment_override(self):
        with mock.patch.dict(os.environ, {"GEMINI_IMAGE_MODEL": "custom"}):
            self.assertEqual(image_model(), "custom")
        with mock.patch.dict(os.environ, {"GEMINI_TEXT_MODEL": "custom-text"}):
            self.assertEqual(text_model(), "custom-text")
        self.assertEqual(DEFAULT_TEXT_MODEL, "gemini-2.5-pro")
        with mock.patch.dict(os.environ, {"GEMINI_REVIEW_MODEL": "custom-review"}):
            self.assertEqual(review_model(), "custom-review")
        self.assertEqual(DEFAULT_REVIEW_MODEL, "gemini-2.5-pro")

    def test_jpeg_and_known_gemini_2k_are_normalized_to_png(self):
        for data, mime in ((jpeg(), "image/jpeg"),
                           (jpeg(1696, 2528), "image/jpeg"),
                           (png(1696, 2528), "image/png")):
            with self.subTest(mime=mime, size=len(data)):
                normalized, dimensions = decode_and_validate(data, mime)
                self.assertEqual(dimensions, (1024, 1536))
                with Image.open(io.BytesIO(normalized)) as result:
                    self.assertEqual(result.format, "PNG")
                    self.assertEqual(result.size, (1024, 1536))

    def test_unknown_portrait_dimensions_are_rejected_before_normalization(self):
        for data, mime in ((jpeg(2048, 3072), "image/jpeg"),
                           (png(848, 1264), "image/png")):
            with self.subTest(mime=mime), self.assertRaisesRegex(RuntimeError, "dimensions"):
                decode_and_validate(data, mime)

    def test_random_card_contract_uses_rarity_text_and_three_trivia_items(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        daily_path = os.path.join(root, "package/hypertext/pipeline/daily.py")
        with open(daily_path, encoding="utf-8") as f:
            daily_source = f.read()
        self.assertNotIn('content.get("RARITY", "COMMON")', daily_source)
        for name in ("card_prompt_template.json", "card_prompt_template_explicit.json"):
            with open(os.path.join(root, "templates", name), encoding="utf-8") as f:
                template = json.load(f)
            trivia = next(panel for panel in template["layout"]["panels"]
                          if panel.get("label") == "TRIVIA")
            self.assertEqual(trivia["bullets_count"], 3)

    def test_multi_image_review_labels_are_adjacent_to_images(self):
        calls = []
        response = ns.SimpleNamespace(candidates=[ns.SimpleNamespace(
            content=ns.SimpleNamespace(parts=[ns.SimpleNamespace(text="{}")]))])
        fake_client = ns.SimpleNamespace(models=ns.SimpleNamespace(
            generate_content=lambda **kwargs: calls.append(kwargs) or response))
        fake_genai = ns.SimpleNamespace(Client=lambda api_key: fake_client)
        fake_types = ns.SimpleNamespace(
            Part=ns.SimpleNamespace(from_text=lambda text: ("text", text)),
            GenerateContentConfig=lambda **kwargs: kwargs)
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake"}, clear=True), \
             mock.patch.object(review, "genai", fake_genai), \
             mock.patch.object(review, "types", fake_types), \
             mock.patch.object(review, "_image_part_from_path",
                               side_effect=lambda path: ("image", str(path))):
            paths = [os.path.join(td, "reference.png"), os.path.join(td, "test.png")]
            review._call_gemini("compare [1] with test [2]", image_paths=paths)
        self.assertEqual(calls[0]["contents"], [
            ("text", "IMAGE [1]"), ("image", paths[0]),
            ("text", "IMAGE [2]"), ("image", paths[1]),
            ("text", "compare [1] with test [2]"),
        ])

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
        workflow_dir = os.path.join(root, ".github/workflows")
        automatic = r"(?m)^  (schedule|push|pull_request|issue_comment|workflow_run):"
        for name in os.listdir(workflow_dir):
            if name.endswith((".yml", ".yaml")):
                with open(os.path.join(workflow_dir, name), encoding="utf-8") as f:
                    content = f.read()
                self.assertIn("  workflow_dispatch:", content, name)
                self.assertNotRegex(content, automatic, name)


if __name__ == "__main__":
    unittest.main()
