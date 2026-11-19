import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from seasons import person_reference
from prepare_references import prepare


class ShiwenfuIdentityUpdateTests(unittest.TestCase):
    def test_current_photo_pixels_reach_both_seasons(self):
        winter = person_reference("401", 4, "winter")
        spring = person_reference("401", 4, "spring_autumn")
        self.assertTrue(winter["identity_source"].endswith("shiwenfu-20261119-01.jpg"))
        for key in ["identity_source", "identity_box", "identity_references"]:
            self.assertEqual(winter[key], spring[key])
        with Image.open(ROOT / winter["identity_source"]) as im:
            crop = im.crop(tuple(round(v * (im.width if i % 2 == 0 else im.height)) for i, v in enumerate(winter["identity_box"])))
        for path in ["references/private/identities/401/4.png", "references/private/identities/401/winter/4.png"]:
            with Image.open(ROOT / path) as actual:
                self.assertEqual(actual.size, crop.size)
                self.assertEqual(actual.tobytes(), crop.tobytes())

    def test_identity_update_does_not_silently_change_clothes(self):
        winter = person_reference("401", 4, "winter")
        spring = person_reference("401", 4, "spring_autumn")
        self.assertTrue(winter["clothing_source"].endswith("173_2.jpg"))
        self.assertEqual(spring["clothing_source"], "401照片/4.png")
        for ref in [winter, spring]:
            self.assertNotEqual(ref["clothing_source"], ref["identity_source"])
        with tempfile.TemporaryDirectory() as tmp:
            for season in ["winter", "spring_autumn"]:
                files = prepare("401", [4], Path(tmp) / season, season=season)
                self.assertEqual(len([f for f in files if "identity" in Path(f).name]), 2)
                self.assertEqual(len([f for f in files if "clothing" in Path(f).name]), 1)

    def test_all_eight_user_photos_are_catalogued(self):
        roster = json.loads((ROOT / "references/private/roster.json").read_text(encoding="utf-8"))
        four = next(p for p in roster["401"]["people"] if p["id"] == 4)
        photos = four["identity_update"]["source_photos"]
        self.assertEqual(len(photos), 8)
        catalog = {p["file"]: p for p in json.loads((ROOT / "references/private/catalog.json").read_text(encoding="utf-8"))}
        for photo in photos:
            self.assertIn(photo["source"], catalog)
            self.assertLess(photo["box"][3], 0.85)  # identity crops omit bottom camera/location watermark
        self.assertEqual(four["identity_history"]["identity_source"], "401照片/4.png")


if __name__ == "__main__":
    unittest.main()
