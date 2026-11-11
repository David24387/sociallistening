import os
import unittest
from unittest.mock import patch
from email.utils import getaddresses
from email_layout import render,plain
from listening import send_mail

def post(i,platform='Instagram',factor=2):
    return {'id':i,'account':'Beispiel','caption':'Drei Fehler bei der Reifenlagerung vermeiden','url':'https://www.instagram.com/p/example/','published_at':'2026-11-03T10:00:00+00:00','age_hours':48,'format':'CAROUSEL_ALBUM','likes':300,'comments':20,'top_performer':True,'benchmark_factor':factor,'benchmark_percentile':95,'benchmark_n':10,'benchmark_mode':'Öffentliche Gesamtinteraktionen','performance_tier':'Deutlicher Ausreißer','adaptation':{'idea':'Ein eigenes Reifenlagerungs-Karussell erstellen.'}}
def report():
    return {'date':'05.11.2026','items':[post('ig')],'sources':[],'linkedin':{'items':[dict(post('li',factor=3),account='LinkedIn-Konto',url='https://de.linkedin.com/posts/example_activity-123-x')],'sources':[]}}
class EmailTests(unittest.TestCase):
    def test_readable_and_no_debug_noise(self):
        result=render(report())
        for text in ('Eure Content-Inspiration','Warum ausgewählt','Originalbeitrag ansehen','Originalbeitrag ansehen','Instagram','LinkedIn'):
            self.assertIn(text,result)
        for text in ('Testbetrieb','JSON-LD','API-Kennzahlen','Quellenstatus','FEHLER','48–72 Stunden nach Veröffentlichung'):
            self.assertNotIn(text,result)
        self.assertNotIn('Kreative Inspiration – Original ansehen',result)
        self.assertIn('role="presentation"',result)
        self.assertIn('style=',result)
    def test_strongest_first_and_old_examples_labelled(self):
        d=report();d['items'][0]['age_hours']=300
        result=render(d)
        self.assertLess(result.index('LinkedIn-Konto'),result.index('@Beispiel'))
        self.assertIn('Best of 30 Tage',result)
    def test_excludes_unqualified_even_if_passed_by_caller(self):
        d=report();d['items'][0]['top_performer']=False;d['linkedin']['items']=[]
        result=render(d)
        self.assertNotIn('Originalbeitrag ansehen',result)
        self.assertIn('Heute keine neuen Empfehlungen',result)
    def test_escape_external_text_and_bad_link(self):
        d=report();d['items'][0]['caption']='<script>bad</script>';d['items'][0]['url']='javascript:alert(1)'
        result=render(d)
        self.assertNotIn('<script>',result);self.assertNotIn('javascript:',result)
    def test_plain_version_has_real_content_and_links(self):
        result=plain(report())
        self.assertIn('Warum ausgewählt',result)
        self.assertIn('https://www.instagram.com/p/example/',result)
    def test_multipart_mail_to_two_recipients(self):
        env={'SMTP_HOST':'example.invalid','SMTP_USER':'sender@example.invalid','SMTP_PASSWORD':'synthetic','MAIL_FROM':'sender@example.invalid','MAIL_TO':'a@example.invalid,b@example.invalid','SMTP_PORT':'587'}
        with patch.dict(os.environ,env),patch('listening.smtplib.SMTP') as smtp:
            send_mail(render(report()),'05.11.2026',plain_text=plain(report()))
            msg=smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
            self.assertEqual(len(getaddresses(msg.get_all('To'))),2)
            self.assertIn('https://www.instagram.com/p/example/',msg.get_body(preferencelist=('plain',)).get_content())
            self.assertIn('role="presentation"',msg.get_body(preferencelist=('html',)).get_content())

class DailyPipelineTests(unittest.TestCase):
    def run_case(self,unavailable=False):
        import tempfile,json
        from pathlib import Path
        from radar import main,SourceError
        from datetime import datetime,timezone
        with tempfile.TemporaryDirectory() as tmp:
            old=os.getcwd();os.chdir(tmp)
            try:
                Path('config.json').write_text(json.dumps({'instagram_accounts':['test'],'linkedin':{'enabled':False}}))
                profile={'username':'test','media':{'data':[{'id':'1','caption':'Reifen Tipps','timestamp':datetime.now(timezone.utc).isoformat(),'permalink':'https://instagram.com/p/test','media_type':'IMAGE','like_count':10,'comments_count':0}]}}
                with patch.dict(os.environ,{'META_ACCESS_TOKEN':'synthetic','INSTAGRAM_ACCOUNT_ID':'123'}),patch('sys.argv',['radar.py','--send']),patch('radar.api',side_effect=SourceError('synthetic failure') if unavailable else None,return_value=profile),patch('radar.collect_linkedin',return_value={'items':[],'sources':[]}),patch('radar.time.sleep'),patch('radar.send_mail',return_value=True) as send:
                    if unavailable:
                        with self.assertRaises(SystemExit):main()
                    else:main()
                    send.assert_called_once()
                    mail=send.call_args.args[0]
                    self.assertIn('Erfassungsstörung' if unavailable else 'Heute keine neuen Empfehlungen',mail)
                    self.assertIn('plain_text',send.call_args.kwargs)
                    self.assertTrue(Path('reports/report.txt').exists())
            finally:os.chdir(old)
    def test_daily_mail_even_without_new_recommendation(self):self.run_case()
    def test_source_outage_mail_before_failed_run(self):self.run_case(True)

class LinkedInStatusTests(unittest.TestCase):
    def test_missing_comparison_not_hidden_or_called_testbetrieb(self):
        d=report();d['linkedin']['items']=[];d['linkedin']['checked_posts']=17
        d['quality']={'linkedin_rejections':{'Zu wenig Vergleichsdaten (3/5)':14}}
        result=render(d)
        self.assertIn('LinkedIn heute',result)
        self.assertIn('17 Beiträge geprüft',result)
        self.assertIn('fehlen noch Vergleichsdaten',result)
        self.assertNotIn('Testbetrieb',result)
    def test_zero_access_not_presented_as_no_good_posts(self):
        d=report();d['linkedin']['items']=[];d['linkedin']['checked_posts']=0
        self.assertIn('keine auswertbaren LinkedIn-Beiträge erreichbar',render(d))

class PublicLinkedInExplanationTests(unittest.TestCase):
    def test_mixed_format_sample_not_called_same_format_or_age_matched(self):
        from email_layout import proof
        r=post('li');r.update(public_profile_sample=True,benchmark_scope='verschiedene Formate')
        result=proof(r)
        self.assertIn('öffentlich sichtbaren',result)
        self.assertIn('unterschiedlichem Beitragsalter',result)
        self.assertNotIn('desselben Formats',result)
        self.assertNotIn('mindestens ebenso alt',result)
