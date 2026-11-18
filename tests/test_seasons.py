import unittest,tempfile,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from seasons import season_for,person_reference
from plan import plan
from prepare_references import prepare
class SeasonTests(unittest.TestCase):
 def test_default_and_explicit_winter(self):
  for command in ["401增加2、3","冬季401增加2、3","使用打卡skill，401增加2、3，冬季"]:
   p=plan(command);self.assertEqual(p["season"],"winter");self.assertEqual(p["requested"],[2,3]);self.assertEqual(p["state"],"ready")
 def test_spring_autumn(self):
  for term in ["春","春季","秋","秋季","春秋"]:
   p=plan("使用打卡skill，401增加2、3，"+term);self.assertEqual(p["season"],"spring_autumn");self.assertEqual(p["requested"],[2,3])
 def test_conflict_rejected(self):
  with self.assertRaises(ValueError):plan("冬季401增加3，秋季")
 def test_403_no_cross_room(self):
  self.assertEqual(plan("403增加4")["season"],"legacy")
  with self.assertRaises(ValueError):plan("冬季403增加1")
 def test_missing_winter_blocks_only_added(self):
  p=plan("401增加6、9");self.assertEqual(p["state"],"needs_reference");self.assertEqual(p["candidate_count"],0);self.assertEqual(p["missing_season_references"],[6])
  p=plan("401增加3、6、9",True,[6,9]);self.assertEqual(p["state"],"ready");self.assertEqual(p["to_add"],[3]);self.assertEqual(p["skipped"],[6,9])
  self.assertEqual(plan("春季401增加6、9")["state"],"ready")
 def test_user_excludes_six_candidate_and_keeps_nine(self):
  data=json.loads((ROOT/"references/private/roster.json").read_text(encoding="utf-8"))
  six=data["401"]["people"][5]["seasonal_references"]["winter"]
  self.assertEqual(six["status"],"missing");self.assertNotIn("candidate_reference",six)
  nine=person_reference("401",9,"winter");old=person_reference("401",9,"spring_autumn")
  self.assertEqual(nine["status"],"unchanged");self.assertEqual(nine["identity_source"],old["identity_source"])
  self.assertEqual(plan("401增加9")["state"],"ready")
  with tempfile.TemporaryDirectory() as tmp:self.assertTrue(prepare("401",[9],tmp))
 def test_all_profiles(self):
  data=json.loads((ROOT/"references/private/roster.json").read_text(encoding="utf-8"))
  for p in data["401"]["people"]:
   self.assertEqual(set(p["seasonal_references"]),{"winter","spring_autumn"})
   for ref in p["seasonal_references"].values():
    if ref.get("identity_source"):self.assertTrue((ROOT/ref["identity_source"]).is_file())
 def test_selected_person_uses_correct_season(self):
  w=person_reference("401",3,"winter");old=person_reference("401",3,"spring_autumn")
  self.assertEqual(w["identity_source"],old["identity_source"]);self.assertEqual(old["identity_source"],"401照片/7.png");self.assertTrue(w["clothing_source"].startswith("401照片冬季/"))
  self.assertEqual(person_reference("401",8,"winter")["status"],"head_only")
 def test_boards_do_not_mix(self):
  with tempfile.TemporaryDirectory() as tmp:
   winter=prepare("401",[2,3],Path(tmp)/"winter")
   legacy=prepare("401",[2,3],Path(tmp)/"old",season="spring_autumn")
   self.assertTrue(all("winter" in Path(f).name for f in winter));self.assertTrue(all("spring_autumn" in Path(f).name for f in legacy))
   self.assertTrue(any("clothing" in Path(f).name for f in winter));self.assertFalse(any("clothing" in Path(f).name for f in legacy))
 def test_identity_is_legacy_for_every_401_profile(self):
  data=json.loads((ROOT/"references/private/roster.json").read_text(encoding="utf-8"))
  for p in data["401"]["people"]:
   w=p["seasonal_references"]["winter"];old=p["seasonal_references"]["spring_autumn"]
   for field in ["identity_source","identity_box","identity_references"]:self.assertEqual(w.get(field),old.get(field),(p["id"],field))
   self.assertEqual(w["identity_season"],"spring_autumn")
 def test_identity_board_pixels_are_season_invariant(self):
  for selected in [[2,3],[1,4],[7,8,10],[9]]:
   with tempfile.TemporaryDirectory() as tmp:
    winter=prepare("401",selected,Path(tmp)/"winter",season="winter")
    old=prepare("401",selected,Path(tmp)/"old",season="spring_autumn")
    winter_id=[Path(f).read_bytes() for f in winter if "identity" in Path(f).name]
    old_id=[Path(f).read_bytes() for f in old if "identity" in Path(f).name]
    self.assertEqual(winter_id,old_id,selected)
 def test_rebuilt_compatibility_aliases_only_contain_legacy_pixels(self):
  for ident in range(1,11):
   self.assertEqual((ROOT/f"references/private/identities/401/{ident}.png").read_bytes(),(ROOT/f"references/private/identities/401/winter/{ident}.png").read_bytes())
 def test_winter_only_changes_clothing_route(self):
  winter=plan("401增加2、3");old=plan("秋季401增加2、3")
  self.assertEqual(winter["identity_reference_set"],old["identity_reference_set"])
  self.assertEqual(winter["clothing_reference_set"],"winter");self.assertEqual(old["clothing_reference_set"],"spring_autumn")
 def test_incomplete_winter_board_not_emitted(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/"request"
   with self.assertRaises(ValueError):prepare("401",[3,6],dest)
   self.assertFalse(dest.exists())
if __name__=="__main__":unittest.main()
