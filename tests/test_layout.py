"""Image size classes: suggested from pixels, kept in front matter, honoured by both renderers."""

import json
import struct
import zlib
from pathlib import Path

import pytest

import penult
from penult import figures as layout
from penult.base import PenultError
from penult.render import essay_fields, render_comment


def _png(path: Path, width: int, height: int) -> None:
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


ESSAY = (
    "---\ntitle: T\nsubtitle: S\n---\n# T\n\n"
    '![hero](img/hero.png "The hero")\n\n' + "word " * 600 + '\n\n![wide](img/wide.png "A wide one")\n\n'
    + "word " * 600 + "\n"
)


@pytest.fixture
def ws(tmp_path):
    (tmp_path / "img").mkdir()
    _png(tmp_path / "img" / "hero.png", 64, 64)
    _png(tmp_path / "img" / "wide.png", 160, 90)
    (tmp_path / "essay.md").write_text(ESSAY, encoding="utf-8")
    (tmp_path / "penult.json").write_text(json.dumps({"stage": "posted", "slug": "t", "platform": "substack"}))
    return tmp_path


def test_the_rules_make_a_square_hero_an_inset_and_a_landscape_body_image_normal(ws):
    report = penult.layout(str(ws))
    by_image = {r["image"]: r for r in report["images"]}
    assert by_image["img/hero.png"]["pixels"] == [64, 64]
    assert by_image["img/hero.png"]["suggested"] == "inset"
    assert by_image["img/wide.png"]["suggested"] == "normal"
    assert report["differ"] == ["img/hero.png"]
    assert report["notes"] == []  # one body image for 1200 words is within the rule


def test_apply_writes_only_the_images_key_and_keeps_a_hand_set_class(ws):
    essay = ws / "essay.md"
    essay.write_text(ESSAY.replace("subtitle: S\n", "subtitle: S\nimages:\n  img/wide.png: large\n"))
    report = penult.layout(str(ws), apply=True)
    assert report["changed"] == ["img/hero.png"]
    text = essay.read_text()
    assert text.startswith("---\ntitle: T\nsubtitle: S\nimages:\n  img/hero.png: inset\n  img/wide.png: large\n---\n# T\n")
    assert text.count("images:") == 1
    assert layout.sizes_from_fields(essay_fields(text)) == {"img/hero.png": "inset", "img/wide.png": "large"}
    # a second apply changes nothing
    penult.layout(str(ws), apply=True)
    assert essay.read_text() == text


def test_an_unknown_class_is_refused():
    with pytest.raises(PenultError, match="unknown size"):
        layout.sizes_from_fields({"images": {"img/a.png": "huge"}})


def test_the_comment_draws_an_inset_narrow_and_captions_small(ws):
    penult.layout(str(ws), apply=True)
    text = render_comment((ws / "essay.md").read_text(), raw_base="https://raw/x/", footer="", inset_width=420)
    assert '<p align="center"><img src="https://raw/x/img/hero.png" alt="hero" width="420"></p>' in text
    assert '<p align="center"><sub>The hero</sub></p>' in text
    assert '<img src="https://raw/x/img/wide.png" alt="wide">' in text  # normal: no width
    assert "![" not in text and "*The hero*" not in text


def test_substack_gets_python_substacks_own_marker_which_it_merges_into_the_image(ws):
    substack = pytest.importorskip("substack.post")
    penult.layout(str(ws), apply=True)
    sized = layout.substack_markdown((ws / "essay.md").read_text())
    lines = sized.splitlines()
    i = next(n for n, line in enumerate(lines) if line.startswith("![hero]"))
    assert lines[i + 1].startswith("<!-- python-substack-image:v1 ")
    assert sum(line.startswith("<!-- python-substack-image") for line in lines) == 1  # normal: no marker
    post = substack.Post(title="T", subtitle="S", user_id=1)
    post.from_markdown(sized.split("---\n", 2)[2], api=None)
    images = [
        node["content"][0]["attrs"]
        for node in json.loads(post.get_draft()["draft_body"])["content"]
        if node["type"] == "captionedImage"
    ]
    assert [a["resizeWidth"] for a in images] == [layout.INSET_WIDTH, 728]


def test_publish_hands_article_a_sized_private_copy_only_when_something_is_sized(ws, tmp_path, monkeypatch):
    seen = []

    def publisher(platform, essay, **kwargs):
        seen.append(Path(essay))
        return {"draft_url": "https://x/edit", "text": ""}

    files = {}
    data = tmp_path / "data"
    penult.approve(str(ws), by="octo")
    penult.publish(str(ws), files=files, data_dir=str(data), publisher=publisher)
    assert seen[-1] == ws / "essay.md"  # nothing sized: the essay itself

    penult.layout(str(ws), apply=True)
    penult.approve(str(ws), by="octo")
    penult.publish(str(ws), files=files, data_dir=str(data), publisher=publisher)
    copy = seen[-1]
    assert copy == data / "work" / ws.name / "substack.md"
    text = copy.read_text()
    assert "python-substack-image:v1" in text
    assert str((ws / "img" / "hero.png").resolve()) in text  # images resolve without the copy's folder
    assert "images:\n  img/hero.png: inset" in text  # front matter untouched
