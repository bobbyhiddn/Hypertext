"""The ability panel is transcribed and diffed exactly against the card record."""
import json

from hypertext.gemini import review


def _fake(response):
    def call(prompt, image_path=None, model=None):
        return json.dumps({"ability_text": response})
    return call


def test_matching_copy_passes_through_typographic_differences(monkeypatch, tmp_path):
    monkeypatch.setattr(review, "_call_gemini", _fake("Look at the bottom four cards of the Tower.  Add up to three of those cards to your hand, put the other cards into Sheol, and then draw one card from the Tower"))
    expected = "Look at the bottom four cards of the Tower. Add up to three of those cards to your hand, put the other cards into Sheol, and then draw one card from the Tower."
    assert review.check_ability_text(tmp_path / "x.png", expected) is None


def test_a_dropped_word_is_a_mismatch(monkeypatch, tmp_path):
    seen = "Look at the bottom four cards of the Tower. Add up to three of those to your hand, put the other cards into Sheol, and then draw one card from the Tower."
    monkeypatch.setattr(review, "_call_gemini", _fake(seen))
    expected = "Look at the bottom four cards of the Tower. Add up to three of those cards to your hand, put the other cards into Sheol, and then draw one card from the Tower."
    assert review.check_ability_text(tmp_path / "x.png", expected) == seen


def test_unparseable_response_is_unreadable(monkeypatch, tmp_path):
    monkeypatch.setattr(review, "_call_gemini", lambda prompt, image_path=None, model=None: "not json at all")
    assert review.check_ability_text(tmp_path / "x.png", "anything") == "__unreadable__"
