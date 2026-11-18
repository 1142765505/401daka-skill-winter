import unittest,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from plan import plan
from seasons import person_reference
class SeatConstraintTests(unittest.TestCase):
 def test_li_tao_gap_is_requested_for_both_clothing_versions(self):
  for cmd in ["401增加2","春季401增加2、3","401增加全部"]:
   p=plan(cmd);rule=p["seat_constraints"]["2"]
   self.assertEqual(rule["person_id"],2);self.assertEqual(rule["anchor_person_id"],1)
   self.assertEqual(rule["intervening_empty_workstations"],1)
   self.assertTrue(rule["preserve_intervening_empty_seat"])
   self.assertTrue(rule["forbid_nearest_empty_seat_substitution"])
   self.assertTrue(rule["requires_visual_verification"])
 def test_gap_does_not_cross_room_or_add_extra_people(self):
  self.assertEqual(plan("403增加2")["seat_constraints"],{})
  self.assertEqual(plan("401增加3")["seat_constraints"],{})
  p=plan("401增加2");self.assertEqual(p["requested"],[2]);self.assertNotIn(1,p["requested"])
 def test_canonical_and_season_profiles_share_the_same_seat_rule(self):
  data=json.loads((ROOT/"references/private/roster.json").read_text(encoding="utf-8"))
  main=data["401"]["people"][1]["seat_constraints"]
  for season in ["winter","spring_autumn"]:self.assertEqual(person_reference("401",2,season)["seat_constraints"],main)
if __name__=="__main__":unittest.main()
