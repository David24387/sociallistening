import unittest
from datetime import datetime,timedelta,timezone
from performance import assess,choose
NOW=datetime(2026,11,5,12,tzinfo=timezone.utc)
def post(i,n=100,age=100,account='a',fmt='IMAGE',caption='Reifen Tipps'):
    return {'id':str(i),'interactions':n,'age_hours':age,'account':account,'format':fmt,'caption':caption,'published_at':(NOW-timedelta(hours=age)).isoformat()}
def sample(n=300,peers=8):return [post('candidate',n,60)]+[post(i,100,100+i) for i in range(peers)]
class PerformanceTests(unittest.TestCase):
    def test_real_outlier_selected_with_proof(self):
        rows=sample();assess(rows);self.assertTrue(rows[0]['top_performer'])
        self.assertEqual(rows[0]['benchmark_factor'],3)
        self.assertEqual(choose(rows)[0]['id'],'candidate')
    def test_twice_median_not_sufficient_if_below_top_decile(self):
        rows=sample();rows[-1]['interactions']=800;rows[-2]['interactions']=800
        assess(rows);self.assertFalse(rows[0]['top_performer'])
    def test_too_few_peers_never_padded(self):
        rows=sample(peers=7);assess(rows);self.assertEqual(choose(rows),[])
    def test_large_account_raw_count_is_not_success(self):
        rows=sample(10000)
        for peer in rows[1:]:peer['interactions']=9000
        assess(rows);self.assertFalse(rows[0]['top_performer'])
    def test_zero_baseline_missing_metrics_and_giveaway(self):
        for mutation in ('zero','missing','giveaway'):
            rows=sample()
            if mutation=='zero':
                for peer in rows[1:]:peer['interactions']=0
            if mutation=='missing':rows[0]['interactions']=None
            if mutation=='giveaway':rows[0]['caption']='Gewinnspiel: tolle Preise'
            assess(rows);self.assertFalse(rows[0]['top_performer'])
    def test_minimum_volume_and_age(self):
        rows=sample(99)
        for peer in rows[1:]:peer['interactions']=10
        assess(rows);self.assertFalse(rows[0]['top_performer'])
        rows=sample();rows[0]['age_hours']=10;assess(rows);self.assertFalse(rows[0]['top_performer'])
    def test_equal_age_snapshots_preferred_when_available(self):
        rows=sample();hist={}
        for peer in rows[1:]:
            hist[peer['id']]=[{'at':(datetime.fromisoformat(peer['published_at'])+timedelta(hours=60)).isoformat(),'interactions':100}]
            peer['interactions']=2000
        assess(rows,hist)
        self.assertTrue(rows[0]['top_performer']);self.assertEqual(rows[0]['benchmark_median'],100)
        self.assertIn('48–72',rows[0]['benchmark_mode'])
    def test_cross_industry_needs_specific_transfer(self):
        rows=sample();rows[0].update(inspiration=True,caption='Wonderful launch today')
        assess(rows);self.assertTrue(rows[0]['top_performer']);self.assertEqual(choose(rows),[])
        rows[0]['caption']='Drei Fehler vermeiden: unsere Tipps'
        self.assertIn('Reifenlagerung',choose(rows)[0]['adaptation']['idea'])
    def test_formats_and_accounts_not_mixed(self):
        rows=sample()
        for p in rows[1:5]:p['account']='other'
        for p in rows[5:]:p['format']='VIDEO'
        assess(rows);self.assertFalse(rows[0]['top_performer'])
    def test_growth_does_not_override_failed_outlier_rules(self):
        rows=sample(150);rows[0]['eligible_for_report']=True;rows[0]['growth_since_report']=500
        assess(rows);self.assertEqual(choose(rows),[])
