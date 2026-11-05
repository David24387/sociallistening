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
        self.assertIn('unbekannt',result)
