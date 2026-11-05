import json
import unittest
from datetime import datetime,timezone
from linkedin_public import parse_post,valid_url,PublicPageError,render_section
URL='https://de.linkedin.com/posts/test_activity-123456-test'
NOW=datetime(2026,11,5,tzinfo=timezone.utc)
def page(stats=None):
    node={'@type':'SocialMediaPosting','@id':URL,'datePublished':'2026-11-03T12:00:00Z','description':'<script>Reifen prüfen</script>','author':{'name':'Branchenkonto'}}
    if stats is not None:node['interactionStatistic']=stats
    return '<script type="application/ld+json">'+json.dumps(node).replace('<', chr(92)+'u003c')+'</script>'
class LinkedInTests(unittest.TestCase):
    def test_explicit_metrics(self):
        row=parse_post(page([{'interactionType':'https://schema.org/LikeAction','userInteractionCount':90},{'interactionType':'https://schema.org/CommentAction','userInteractionCount':10}]),URL,NOW)
        self.assertEqual(row['interactions'],100)
        self.assertEqual(row['account'],'Branchenkonto')
    def test_unknown_not_zero(self):
        row=parse_post(page(),URL,NOW)
        self.assertIsNone(row['likes']);self.assertIsNone(row['comments']);self.assertIsNone(row['interactions'])
    def test_challenge_not_content(self):
        with self.assertRaises(PublicPageError):parse_post('<script>window.location="/authwall"</script>',URL,NOW)
    def test_wrong_post_not_used(self):
        with self.assertRaises(PublicPageError):parse_post(page(),'https://linkedin.com/posts/wrong_activity-999-test',NOW)
    def test_url_scope(self):
        self.assertIsNone(valid_url('https://linkedin.com.evil.test/posts/a_activity-123-x'))
        self.assertIsNone(valid_url('https://linkedin.com:123/posts/a_activity-123-x'))
        self.assertIsNotNone(valid_url(URL+'?tracking=123'))
    def test_escape(self):
        row=parse_post(page(),URL,NOW)
        result=render_section({'items':[row],'sources':[]})
        self.assertNotIn('<script>',result)
        self.assertIn('Heute kein neuer LinkedIn-Beitrag',result)

class DistributionTests(unittest.TestCase):
    def test_companies_with_encoded_names(self):
        self.assertIsNotNone(valid_url('https://www.linkedin.com/company/verg%C3%B6lst/','company'))
        self.assertIsNotNone(valid_url('https://www.linkedin.com/company/a.t.u-auto-teile-unger-handels-gmbh-%26-co.-kg/','company'))
        self.assertIsNone(valid_url('https://www.linkedin.com/company/a%2fb/','company'))
    def test_balanced_fetch_budget(self):
        from linkedin_public import round_robin
        self.assertEqual(round_robin([list(range(10)),['other']],3),[0,'other',1])
    def test_no_report_without_performance_proof(self):
        from linkedin_public import select_posts
        rows=[{'account':'ADAC','caption':'Reifen prüfen','age_hours':100,'interactions':10000}]
        self.assertEqual(select_posts(rows,2),[])

class BaselineBudgetTests(unittest.TestCase):
    def test_initial_sample_expanded_not_threshold_lowered(self):
        from linkedin_public import needs_baseline
        urls=[f'post{i}' for i in range(10)]
        inspected={url:{'post':{'interactions':10}} for url in urls[:3]}
        self.assertTrue(needs_baseline({'company':urls},inspected))
        inspected.update({url:{'post':{'interactions':10}} for url in urls[:8]})
        self.assertFalse(needs_baseline({'company':urls},inspected))
    def test_single_seed_does_not_force_bootstrap_forever(self):
        from linkedin_public import needs_baseline
        self.assertFalse(needs_baseline({'one_seed':['one']},{}))
