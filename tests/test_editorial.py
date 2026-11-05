import unittest
from datetime import datetime,timedelta,timezone
from editorial import prepare,record
from linkedin_public import prioritize_links,select_posts
NOW=datetime(2026,11,5,8,tzinfo=timezone.utc)
def row(i='1',n=100,age=24):return {'id':i,'interactions':n,'age_hours':age,'account':'test','caption':'Reifen prüfen'}
class DailyTests(unittest.TestCase):
    def test_new_then_next_day_suppressed(self):
        r=row();prepare([r],{},NOW);self.assertTrue(r['eligible_for_report'])
        state=record([r],{},NOW)
        tomorrow=NOW+timedelta(days=1)
        prepare([r],state,tomorrow)
        self.assertFalse(r['eligible_for_report'])
    def test_growth_requires_absolute_and_relative_threshold(self):
        state={'1':{'at':(NOW-timedelta(days=1)).isoformat(),'interactions':100}}
        r=row(n=150);prepare([r],state,NOW);self.assertTrue(r['eligible_for_report'])
        r=row(n=140);prepare([r],state,NOW);self.assertFalse(r['eligible_for_report'])
        state['1']['interactions']=1000;r=row(n=1050);prepare([r],state,NOW);self.assertFalse(r['eligible_for_report'])
    def test_manual_same_day_rerun_does_not_erase_report(self):
        state=record([row()],{},NOW);r=row(n=110)
        prepare([r],state,NOW+timedelta(hours=1));self.assertTrue(r['eligible_for_report'])
        self.assertEqual(record([r],state,NOW+timedelta(hours=1))['1']['interactions'],100)
    def test_old_found_post_is_not_new_content(self):
        r=row(age=200);prepare([r],{},NOW);self.assertFalse(r['eligible_for_report'])
        self.assertEqual(select_posts([r]),[])
    def test_newly_discovered_ahead_of_rotation_and_refresh(self):
        self.assertEqual(prioritize_links(['old','new','seed'],{'old':{}},['old','new']),['new','old','seed'])
