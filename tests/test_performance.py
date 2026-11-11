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
        rows=sample(peers=4);assess(rows);self.assertEqual(choose(rows),[])
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
        rows=sample(49)
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
        assess(rows);self.assertTrue(rows[0]['top_performer']);self.assertEqual(choose(rows)[0]['id'],'candidate')
        rows[0]['caption']='Drei Fehler vermeiden: unsere Tipps'
        self.assertIsNone(choose(rows)[0]['adaptation'])
    def test_formats_and_accounts_not_mixed(self):
        rows=sample()
        for p in rows[1:5]:p['account']='other'
        for p in rows[5:]:p['format']='VIDEO'
        assess(rows);self.assertFalse(rows[0]['top_performer'])
    def test_growth_does_not_override_failed_outlier_rules(self):
        rows=sample(120);rows[0]['eligible_for_report']=True;rows[0]['growth_since_report']=500
        assess(rows);self.assertEqual(choose(rows),[])


class PracticalWindowTests(unittest.TestCase):
    def test_strong_and_outlier_labels_are_distinct(self):
        rows=sample(160);assess(rows)
        self.assertTrue(rows[0]['top_performer'])
        self.assertEqual(rows[0]['performance_tier'],'Stark im Accountvergleich')
        rows=sample(300);assess(rows)
        self.assertEqual(rows[0]['performance_tier'],'Deutlicher Ausreißer')
    def test_useful_older_post_with_real_baseline_qualifies(self):
        rows=[post('older',300,480)]+[post(i,100,600+i) for i in range(5)]
        assess(rows);self.assertEqual(choose(rows)[0]['id'],'older')
        self.assertIn('Kleinere',rows[0]['benchmark_confidence'])
    def test_regular_posts_still_not_padding(self):
        rows=sample(120);assess(rows);self.assertEqual(choose(rows),[])
    def test_post_after_thirty_days_excluded(self):
        rows=[post('too_old',1000,750)]+[post(i,100,800+i) for i in range(8)]
        assess(rows);self.assertFalse(rows[0]['top_performer'])

class PublicLinkedInTests(unittest.TestCase):
    def test_actual_atu_snapshot_qualifies_with_honest_scope(self):
        from performance import assess_public_linkedin
        rows=[post('atu',60,50,account='ATU',fmt='CAROUSEL_ALBUM',caption='Teamvorstellung: unsere Mitarbeitenden')]
        metrics=[11,10,20,37,12,10,15,29,27]
        for i,value in enumerate(metrics):
            rows.append(post(i,value,70+i,account='ATU',fmt='CAROUSEL_ALBUM' if i<3 else 'IMAGE'))
        assess_public_linkedin(rows)
        self.assertTrue(rows[0]['top_performer'])
        self.assertEqual(rows[0]['benchmark_factor'],4)
        self.assertEqual(rows[0]['benchmark_scope'],'verschiedene Formate')
        self.assertTrue(rows[0]['public_profile_sample'])
        self.assertIn('Menschen',choose(rows)[0]['adaptation']['pattern'])
    def test_same_format_preferred_when_sample_sufficient(self):
        from performance import assess_public_linkedin
        rows=sample(300);assess_public_linkedin(rows)
        self.assertEqual(rows[0]['benchmark_scope'],'gleiches Format')
    def test_no_forced_linkedin_quota_or_cross_account_baseline(self):
        from performance import assess_public_linkedin
        rows=sample(120);assess_public_linkedin(rows)
        self.assertFalse(rows[0]['top_performer'])
        rows=sample(peers=4);assess_public_linkedin(rows)
        self.assertFalse(rows[0]['top_performer'])
    def test_financial_and_privacy_posts_not_forced_into_transfer(self):
        from performance import adaptation
        self.assertIsNone(adaptation(post('x',300,caption='Financial results: unsere Quartalsergebnisse')))
        self.assertIsNone(adaptation(post('x',300,caption='Datenschutzkonferenz und neue Pannenhilfe-Daten')))

class TransferMeaningTests(unittest.TestCase):
    def test_hr_award_not_misread_as_price_saving(self):
        from performance import adaptation
        result=adaptation(post('x',300,caption='Wir freuen uns über einen HR Inside Award. Ein toller Preis für das Team.'))
        self.assertNotIn('Kosten',result['pattern'])
        self.assertIn('Leistung',result['pattern'])
    def test_roadside_award_gets_service_case_transfer(self):
        from performance import adaptation
        result=adaptation(post('x',300,caption='Bronze für unsere Pannenhilfe! Die Serviceleistung war hervorragend.'))
        self.assertIn('Panneneinsatz',result['idea'])
