"""Instagram Business Discovery reports; credentials only from environment."""
import argparse
import html
import json
import os
import re
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from listening import send_mail
from email_layout import render as render_email, plain as plain_email
from performance import assess_public_linkedin, assess as assess_performance, choose as choose_performers, evidence, adaptation as adaptation_for_diagnostics
from editorial import prepare as prepare_editorial, record as record_editorial
from linkedin_public import collect as collect_linkedin, render_section as render_linkedin, select_posts as select_linkedin

class SourceError(Exception):
    pass

def api(account, token, own_id, version, limit=50):
    if not re.fullmatch(r'[A-Za-z0-9_.]{1,30}', account):
        raise SourceError('Ungültiger Benutzername in config.json')
    if not re.fullmatch(r'\d+', own_id) or not re.fullmatch(r'v\d+\.0', version):
        raise SourceError('Ungültige Instagram-ID oder API-Version')
    fields = f'business_discovery.username({account})' + '{username,followers_count,media.limit(' + str(limit) + '){id,caption,permalink,timestamp,media_type,like_count,comments_count}}'
    url = f'https://graph.facebook.com/{version}/{own_id}?' + urllib.parse.urlencode({'fields': fields})
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read(4_000_000))
    except urllib.error.HTTPError as error:
        try:
            meta = json.loads(error.read(100_000)).get('error', {})
            message = str(meta.get('message', 'HTTP-Fehler')).replace(token, '[REDACTED]')
            raise SourceError(f'Meta {meta.get("code", error.code)}: {message[:250]}') from None
        except (ValueError, UnicodeError):
            raise SourceError(f'HTTP {error.code}') from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise SourceError('Abruf fehlgeschlagen (Netzwerk, Timeout oder ungültige Antwort)') from None
    if 'error' in data:
        raise SourceError('Meta meldet einen API-Fehler')
    profile = data.get('business_discovery')
    if not isinstance(profile, dict) or not profile.get('username'):
        raise SourceError('Keine Business-Discovery-Daten erhalten')
    return profile

def number(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None

def stamp(value):
    try:
        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return date if date.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None

def normalize(profile, now):
    rows = []
    for media in profile.get('media', {}).get('data', []):
        date = stamp(media.get('timestamp'))
        url = media.get('permalink', '')
        parsed = urllib.parse.urlsplit(url)
        if not date or date > now or parsed.scheme != 'https' or parsed.hostname not in ('instagram.com', 'www.instagram.com'):
            continue
        likes, comments = number(media.get('like_count')), number(media.get('comments_count'))
        rows.append({'id':str(media['id']), 'account':profile['username'], 'followers':number(profile.get('followers_count')), 'caption':media.get('caption', ''), 'url':url, 'published_at':date.isoformat(), 'age_hours':round((now-date).total_seconds()/3600, 1), 'format':media.get('media_type','UNKNOWN'), 'likes':likes, 'comments':comments, 'interactions':likes+comments if likes is not None and comments is not None else None})
    return rows

THEMES = {
    'Verkehrsregeln und Irrtümer': ('regel', 'jurist', 'dräng', 'lichthupe', 'bußgeld', 'roller'),
    'Kosten und Planung': ('kosten', 'wertverlust', 'fuhrpark', 'termin', 'sparen'),
    'Reifen und Fahrzeugsicherheit': ('reifen', 'profiltiefe', 'brems', 'aquaplaning', 'steinschlag'),
    'Saisonale Pflege': ('winter', 'kalt', 'frost', 'akku', 'batterie'),
    'Werkstatt und Menschen': ('werkstatt', 'monteur', 'kolleg', 'team', 'ausbildung')
}
IDEAS = {
    'Verkehrsregeln und Irrtümer': 'Eigene kurze Expertenserie: eine typische Kundenfrage, eine fachlich geprüfte Antwort. Etwa zur Winterbereifung; DE und AT getrennt prüfen.',
    'Kosten und Planung': 'Infografik für Flottenkunden: Welche Angaben helfen, Werkstatt- und Reifenwechseltermine zu planen?',
    'Reifen und Fahrzeugsicherheit': 'An einem echten Reifen zeigen, welche Auffälligkeit eine weitere Prüfung in der Werkstatt auslöst.',
    'Saisonale Pflege': 'Saisonale Checkliste aus dem Werkstattalltag, etwa zum Batteriecheck vor kalten Tagen.',
    'Werkstatt und Menschen': 'Eine Fachkraft erklärt einen konkreten Arbeitsschritt und dessen Nutzen für Kunden.'
}

def analyze(rows, history, now):
    for row in rows:
        # Conservative preliminary benchmark: only mature posts of the same account/format.
        peers = [r['interactions'] for r in rows if r['id'] != row['id'] and r['account'] == row['account'] and r['format'] == row['format'] and 72 <= r['age_hours'] <= 2160 and r['interactions'] is not None]
        baseline = statistics.median(peers) if len(peers) >= 5 else None
        row['baseline_n'] = len(peers)
        row['baseline_median'] = baseline
        row['relative_score'] = round(row['interactions']/baseline, 2) if baseline and row['interactions'] is not None and 72 <= row['age_hours'] <= 168 else None
        snapshots = history.get(row['id'], [])
        prior = [(stamp(s['at']), s.get('interactions')) for s in snapshots]
        prior = [(d,n) for d,n in prior if d and number(n) is not None and 20 <= (now-d).total_seconds()/3600 <= 28]
        row['daily_gain'] = row['interactions']-prior[-1][1] if prior and row['interactions'] is not None else None
        text = row['caption'].lower()
        row['themes'] = [name for name,words in THEMES.items() if any(word in text for word in words)]
    return rows

def select(rows, limit):
    return choose_performers(rows,limit)


def render(report):
    return render_email(report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--send', action='store_true')
    args = parser.parse_args()
    config = json.loads(Path('config.json').read_text())
    now = datetime.now(timezone.utc)
    output = Path('reports'); output.mkdir(exist_ok=True)
    state = Path('state/instagram_history.json')
    history = json.loads(state.read_text()) if state.exists() else {}
    reported_path=Path('state/reported.json')
    reported=json.loads(reported_path.read_text()) if reported_path.exists() else {}
    token = os.environ.get('META_ACCESS_TOKEN', '').strip()
    own_id = os.environ.get('INSTAGRAM_ACCOUNT_ID', '').strip()
    rows, sources = [], []
    if token and own_id:
        for account in config['instagram_accounts'] + config.get('inspiration_accounts', []):
            try:
                profile = api(account, token, own_id, config.get('meta_api_version','v26.0'))
                found = normalize(profile, now)
                for row in found:row['inspiration']=account in config.get('inspiration_accounts',[])
                rows.extend(found)
                sources.append({'account':account,'status':'OK','count':len(found)})
            except SourceError as exc:
                sources.append({'account':account,'status':'FEHLER','error':str(exc),'count':0})
            time.sleep(0.5)
    else:
        sources.append({'account':'Instagram','status':'NICHT KONFIGURIERT','error':'META_ACCESS_TOKEN und INSTAGRAM_ACCOUNT_ID als GitHub-Secrets hinterlegen.','count':0})
    linkedin = collect_linkedin(config, now)
    linkedin_raw = linkedin['items']
    local_now = now.astimezone(ZoneInfo('Europe/Berlin'))
    prepare_editorial(rows,reported,local_now,config.get('performance',{}).get('max_age_hours',720))
    prepare_editorial(linkedin_raw,reported,local_now,config.get('performance',{}).get('max_age_hours',720))
    analyze(rows,history,now)
    assess_performance(rows,history,config.get('performance',{}))
    linkedin_baseline = {r['id']:r for r in linkedin.get('baseline_rows',[])}
    linkedin_baseline.update({r['id']:r for r in linkedin_raw})
    assess_public_linkedin(list(linkedin_baseline.values()),config.get('performance',{}))
    linkedin['items'] = choose_performers(linkedin_raw,config.get('linkedin',{}).get('max_report_posts',3),max_per_account=1)
    linkedin.pop('baseline_rows',None)
    linkedin['checked_posts']=len(linkedin_raw)
    linkedin['qualified_posts']=sum(r.get('top_performer',False) for r in linkedin_raw)
    report = {'date':now.astimezone(ZoneInfo('Europe/Berlin')).strftime('%d.%m.%Y'), 'generated_at':now.isoformat(), 'total_posts':len(rows), 'sources':sources, 'items':select(rows,config.get('max_results',10)), 'linkedin':linkedin}
    report['data_status']='unavailable' if not rows and not linkedin_raw else 'partial' if not rows else 'ok'
    report['quality']={'instagram_rejections':dict(Counter(r['performance_reason'] for r in rows if not r.get('top_performer'))),'linkedin_rejections':dict(Counter(r['performance_reason'] for r in linkedin_raw if not r.get('top_performer')))}
    report['quality']['instagram_qualified_before_editorial']=sum(r.get('top_performer',False) for r in rows)
    report['quality']['linkedin_qualified_before_editorial']=sum(r.get('top_performer',False) for r in linkedin_raw)
    report['quality']['qualified_but_previously_reported']=sum(r.get('top_performer',False) and not r.get('eligible_for_report',True) for r in rows+linkedin_raw)
    report['quality']['qualified_without_transfer']=sum(r.get('top_performer',False) and r.get('eligible_for_report',True) and not adaptation_for_diagnostics(r) for r in rows+linkedin_raw)
    report['quality']['linkedin_candidate_examples']=[{k:r.get(k) for k in ('account','url','published_at','format','interactions','performance_reason','benchmark_n','benchmark_factor','benchmark_percentile')} for r in linkedin_raw]
    report['quality']['candidate_examples']=[{k:r.get(k) for k in ('account','url','published_at','interactions','performance_reason','benchmark_n','benchmark_factor','benchmark_percentile','editorial_status')} for r in sorted(rows+linkedin_raw,key=lambda r:r.get('benchmark_factor') or 0,reverse=True)[:25]]
    if os.environ.get('GITHUB_RUN_ID'):
        report['diagnostics_url']='https://github.com/David24387/sociallistening/actions/runs/'+os.environ['GITHUB_RUN_ID']
    rendered = render(report)
    plain_text = plain_email(report)
    (output/'index.html').write_text(rendered,encoding='utf-8')
    (output/'report.txt').write_text(plain_text,encoding='utf-8')
    (output/'latest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'diagnostics.json').write_text(json.dumps({'instagram':sources, 'linkedin':linkedin['sources'], 'quality':report['quality']},ensure_ascii=False,indent=2),encoding='utf-8')
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a',encoding='utf-8') as f:
            f.write(f'## Content Radar · Tagesübersicht\n\n{len(rows)} Beiträge gelesen; {len(report["items"])} qualifizierte Top-Performer im Report.\n\n')
            for source in sources:
                f.write(f'- `@{source["account"]}`: {source["status"]}, {source["count"]} Beiträge\n')
            f.write(f'\nLinkedIn: {len(linkedin["items"])} qualifizierte starke öffentliche Beiträge im Report (letzte 30 Tage).\n')
            f.write(f'Geprüfte Einzelbeiträge: {linkedin.get("checked_posts",0)}. Vergleichsbasis erweitern: {"ja" if linkedin.get("baseline_refresh") else "nein"}.\n')
            for source in linkedin['sources']:
                f.write(f'- LinkedIn `{source["account"]}`: {source["status"]}, {source["count"]} Beiträge\n')
            f.write('\nQualitätsfilter: mindestens 1,5× Median, oberste 20 %, mindestens 50 Interaktionen, mindestens 5 Vergleichsposts. Ohne Beleg kein Reporteintrag.\n')
            f.write('\nDie Mail enthält die kompakte Auswahl mit Original-Links und Euromaster-Ideen. Quellenstatus und Auswahlgründe stehen in diagnostics.json. LinkedIn umfasst öffentlich erreichbare Beiträge; keine vollständige Plattformabdeckung.\n')
    if not rows:
        print('::warning::Keine Instagram-Beiträge abrufbar. Mail enthält den Hinweis zur eingeschränkten Datengrundlage.')
    # Reports survive a mail error; cached snapshot updates happen only after successful/disabled mail.
    reported=record_editorial(report['items']+linkedin['items'],reported,now.astimezone(ZoneInfo('Europe/Berlin')))
    reported_path.parent.mkdir(exist_ok=True)
    reported_path.write_text(json.dumps(reported,ensure_ascii=False,indent=2),encoding='utf-8')
    if args.send:
        send_mail(rendered, report['date'], plain_text=plain_text)
    for row in rows+linkedin_raw:
        snapshots = history.setdefault(row['id'], [])
        if not snapshots or (now-stamp(snapshots[-1]['at'])).total_seconds() >= 3600:
            snapshots.append({'at':now.isoformat(),'interactions':row['interactions']})
        history[row['id']] = [s for s in snapshots if stamp(s['at']) and (now-stamp(s['at'])).days < 35]
    history = {k:v for k,v in history.items() if v and (now-stamp(v[-1]['at'])).days < 35}
    state.parent.mkdir(exist_ok=True)
    state.write_text(json.dumps(history),encoding='utf-8')
    if report['data_status']=='unavailable':
        raise SystemExit('Keine Beitragsdaten erreichbar. Statusbericht wurde erzeugt; Mailversand wurde bei vorhandener Konfiguration versucht.')
    print(f'{len(rows)} Instagram-Beiträge gelesen, {len(report["items"])} im Report. Keine Zugangsdaten im Report gespeichert.')

if __name__ == '__main__':
    main()
