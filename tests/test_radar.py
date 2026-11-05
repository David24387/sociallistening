import unittest
from unittest.mock import patch
from datetime import datetime, timezone
import io
import urllib.error
from radar import normalize, analyze, select, api, render, SourceError
NOW=datetime(2026,11,5,12,tzinfo=timezone.utc)
def post(i,account='test',age=100,count=10):
    return dict(id=str(i),account=account,age_hours=age,interactions=count,format='IMAGE',caption='<script>Reifen</script>',likes=count,comments=0,followers=1000,published_at='2026-11-01T12:00:00+00:00',url='https://instagram.com/p/test')
class RadarTests(unittest.TestCase):
    def test_unknown_is_not_zero(self):
        p={'username':'test','followers_count':100,'media':{'data':[{'id':'1','timestamp':'2026-11-04T12:00:00+0000','permalink':'https://instagram.com/p/test','like_count':None,'comments_count':0}]}}
        self.assertIsNone(normalize(p,NOW)[0]['interactions'])
    def test_benchmark_excludes_self_and_young_posts(self):
        rows=[post(i) for i in range(6)]+[post(99,age=1,count=500)]
        analyze(rows,{},NOW)
        self.assertEqual(rows[0]['baseline_n'],5)
        self.assertEqual(rows[0]['relative_score'],1)
        self.assertIsNone(rows[-1]['relative_score'])
        analyze(rows[:2],{},NOW)
        self.assertIsNone(rows[0]['relative_score'])
    def test_account_diversity_not_absolute_likes(self):
        rows=[post(i,'large',count=10000) for i in range(6)]+[post(9,'small',count=5)]
        analyze(rows,{},NOW)
        self.assertEqual({r['account'] for r in select(rows,2)},{'large','small'})
    def test_history_delta(self):
        row=post(1,count=100)
        analyze([row],{'1':[{'at':'2026-11-04T12:00:00+00:00','interactions':70}]},NOW)
        self.assertEqual(row['daily_gain'],30)
    def test_token_not_in_url_or_error(self):
        token='synthetic-secret'
        error=urllib.error.HTTPError('https://graph.facebook.com',400,'bad',{},io.BytesIO(b'{"error":{"code":190,"message":"synthetic-secret expired"}}'))
        with patch('urllib.request.urlopen',side_effect=error) as mock:
            with self.assertRaises(SourceError) as cm: api('adac',token,'17841403696908375','v26.0')
            request=mock.call_args.args[0]
            self.assertNotIn(token,request.full_url)
            self.assertNotIn(token,str(cm.exception))
    def test_render_labels_and_escaping(self):
        row=post(1);analyze([row],{},NOW)
        result=render(dict(items=[row],date='05.11.2026',total_posts=1,sources=[],generated_at=NOW.isoformat()))
        self.assertNotIn('<script>',result)
        self.assertIn('Noch kein belastbarer Vergleichswert',result)
        self.assertIn('Facebook und LinkedIn',result)
    def test_invalid_handle_before_network(self):
        with self.assertRaises(SourceError): api('bad){id}','secret','123','v26.0')
