from pathlib import Path
import copy
import importlib.util
import json
import tempfile
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts/build_site.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PublicBuildTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "data/game-data.json").read_text(encoding="utf-8"))

    def prepare(self, data):
        with tempfile.TemporaryDirectory(prefix="aniimax-build-test-") as folder:
            path = Path(folder) / "catalog.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return builder.prepare_site(path)

    def test_data_only_extension_updates_built_summary_and_preserves_every_level(self):
        row = copy.deepcopy(max(self.data["rv_levels"], key=lambda r: r["level"]))
        row["level"] += 1
        row["modules"]["kitchen_module"] += 10
        self.data["rv_levels"].insert(0, row)
        recipe = copy.deepcopy(self.data["recipes"][0])
        recipe["name"] = "future_build_test_recipe"
        self.data["recipes"].append(recipe)
        files, summary = self.prepare(self.data)
        built = json.loads(files["data/game-data.json"])
        self.assertEqual(built, self.data)
        self.assertEqual(summary["max_rv"], row["level"])
        minimum = min(r["level"] for r in self.data["rv_levels"])
        self.assertIn(f'RV {minimum}–{row["level"]}', files["index.html"].decode("utf-8"))
        self.assertIn(f'{summary["regular_recipes"]} regular recipes', files["index.html"].decode("utf-8"))
        self.assertFalse(any(Path(name).name.startswith("editor.") for name in files))
        self.assertNotIn("saveCatalog", files["catalog-store.js"].decode("utf-8"))

    def test_known_desktop_provenance_is_not_published(self):
        self.data["evidence"] = {"private": "not public"}
        self.data["notes"] = "not public"
        self.data["rv_levels"][0]["source"] = "local evidence"
        files, _ = self.prepare(self.data)
        published = json.loads(files["data/game-data.json"])
        self.assertNotIn("evidence", published)
        self.assertNotIn("notes", published)
        self.assertNotIn("source", published["rv_levels"][0])

    def test_invalid_data_and_private_paths_block_publication(self):
        data = copy.deepcopy(self.data)
        data["rv_levels"].append(copy.deepcopy(data["rv_levels"][-1]))
        with self.assertRaisesRegex(ValueError, "validation failed"):
            self.prepare(data)
        data = copy.deepcopy(self.data)
        data["translations"]["Private test"] = "C:" + chr(92) + "Users" + chr(92) + "Example"
        with self.assertRaisesRegex(ValueError, "private path"):
            self.prepare(data)

    def test_public_runtime_has_no_private_files_or_remote_page_resources(self):
        files, _ = self.prepare(self.data)
        forbidden = {"editor.html", "editor.js", "editor.css", "site.zip", "site.sha256"}
        self.assertFalse(forbidden & files.keys())
        self.assertEqual([n for n in files if n.startswith("data/")], ["data/game-data.json"])
        self.assertFalse(any(n.endswith((".exe", ".csv", ".log", ".map")) for n in files))
        for name, content in files.items():
            self.assertIsNone(builder.PRIVATE_MARKERS.search(content), name)

        class Resources(HTMLParser):
            def handle_starttag(parser, tag, attributes):
                attrs = dict(attributes)
                self.assertFalse(any(k.startswith("on") for k in attrs), (tag, attrs))
                if tag == "script":
                    self.assertIn("src", attrs, "Inline scripts are not permitted")
                for attribute in (["src"] if tag in {"script", "img", "iframe"} else ["href"] if tag == "link" else []):
                    value = attrs.get(attribute, "")
                    self.assertFalse(":" in value or value.startswith("//"), value)

        html = files["index.html"].decode("utf-8")
        Resources().feed(html)
        self.assertIn("connect-src 'self'", html)
        self.assertNotIn("'unsafe-eval'", html)
        self.assertIn('name="referrer" content="no-referrer"', html)
        self.assertIn('href="privacy.html"', html)


if __name__ == "__main__":
    unittest.main()
