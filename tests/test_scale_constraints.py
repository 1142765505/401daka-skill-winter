import unittest,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from plan import plan
from seasons import person_reference
class ScaleConstraintTests(unittest.TestCase):
 def test_targets_require_calibration_in_both_seasons(self):
  for command in ["401增加2、3","春季401增加2、3"]:
   rules=plan(command)["scale_constraints"];self.assertEqual(set(rules),{"2","3"})
   for ident,rule in rules.items():
    self.assertEqual(rule["person_id"],int(ident));self.assertEqual(rule["status"],"requires_visual_calibration")
    self.assertFalse(rule["identity_board_is_size_reference"]);self.assertFalse(rule["calibration_is_automatic"])
    self.assertTrue(rule["preserve_pelvis_on_original_seat"]);self.assertTrue(rule["oversized_person_fails_review"])
    self.assertTrue((ROOT/rule["reference"]).is_file())
 def test_scale_requirements_only_apply_to_added_targets(self):
  p=plan("401增加2、3",True,[2]);self.assertEqual(set(p["scale_constraints"]),{"3"});self.assertEqual(p["skipped"],[2])
  self.assertEqual(plan("401增加2、3",True,[2,3])["scale_constraints"],{})
  self.assertEqual(plan("401增加2、3",True)["scale_constraints"],{})
 def test_unrelated_room_and_people_unchanged(self):
  self.assertEqual(plan("403增加2、3")["scale_constraints"],{})
  self.assertEqual(plan("401增加1、4")["scale_constraints"],{})
 def test_season_profiles_keep_identity_and_share_scale_policy(self):
  for ident in [2,3]:
   winter=person_reference("401",ident,"winter");old=person_reference("401",ident,"spring_autumn")
   self.assertEqual(winter["identity_source"],old["identity_source"])
   self.assertEqual(winter["scale_constraints"],old["scale_constraints"])
if __name__=="__main__":unittest.main()
