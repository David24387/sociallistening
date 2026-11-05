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
    recent = [r for r in rows if r['age_hours'] <= 168]
    # No cross-account ranking of raw like counts. First fill one slot per account,
    # then fill remaining slots with each account's next result.
    accounts = {}
    for row in recent:
        accounts.setdefault(row['account'], []).append(row)
    for group in accounts.values():
        group.sort(key=lambda r:(r['relative_score'] is not None, r['relative_score'] or 0, r['interactions'] if r['interactions'] is not None else -1), reverse=True)
    chosen = []
    while len(chosen) < limit and any(accounts.values()):
        for group in accounts.values():
            if group and len(chosen) < limit:
                chosen.append(group.pop(0))
    return chosen

def render(report):
    e = html.escape
    cards = []
    for row in report['items']:
        values = lambda n: f'{n:,}'.replace(',', '.') if n is not None else 'unbekannt'
        score = row['relative_score']
        assessment = f'{score}× des Medianwerts von {row["baseline_n"]} anderen ausgereiften Beiträgen desselben Formats und Accounts. Vorläufiger Vergleich; kein einheitliches Messalter.' if score is not None else 'Noch kein belastbarer Vergleichswert für diesen Beitrag. Auswahl innerhalb des Accounts nach sichtbaren Interaktionen.'
        gain = f' · Veränderung seit ca. gestern: {row["daily_gain"]:+d}' if row['daily_gain'] is not None else ''
        date = stamp(row['published_at']).astimezone(ZoneInfo('Europe/Berlin')).strftime('%d.%m.%Y %H:%M')
        title = row['caption'].split('\n')[0][:140] or 'Instagram-Beitrag'
        rate = 100*row['interactions']/row['followers'] if row['interactions'] is not None and row['followers'] else None
        rate_text = f' · Interaktionen / aktuelle Follower: {rate:.2f} %' if rate is not None else ''
        cards.append(f'<article><small>@{e(row["account"])} · {e(row["format"])} · {date} MEZ/MESZ · {row["age_hours"]:.0f} Stunden alt</small><h2><a href="{e(row["url"], quote=True)}">{e(title)}</a></h2><p>{e(row["caption"][:1200]).replace(chr(10), "<br>")}</p><p><b>{values(row["likes"])} Likes · {values(row["comments"])} Kommentare</b>{gain}{rate_text}</p><p>{e(assessment)}</p><p class="muted">Themenhinweis: {e(", ".join(row["themes"]) or "Allgemeiner Brancheninhalt")}. Originalbild/-video über den Link ansehen.</p></article>')
    themes = Counter(theme for row in report['items'] for theme in row['themes'])
    suggestions = ''.join(f'<li><b>{e(name)}</b> ({count} ausgewählte Beiträge): {e(IDEAS[name])}</li>' for name,count in themes.most_common(3)) or '<li>Noch keine thematische Auswertung möglich.</li>'
    status = ''.join(f'<li>@{e(s["account"])}: {e(s["status"])} · {s.get("count",0)} Beiträge{": " + e(s["error"]) if s.get("error") else ""}</li>' for s in report['sources'])
    return f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>EUROMASTER Content Radar</title><style>body{{margin:0;background:#f2f5fa;font:16px/1.6 Arial,sans-serif;color:#172b4d}}main{{max-width:940px;margin:auto;padding:24px}}header{{padding:28px;background:#164194;color:white;border-bottom:8px solid #fedd00;border-radius:14px}}h1{{margin:0;font-size:34px}}h2{{font-size:21px}}a{{color:#164194}}article,section{{padding:24px;background:white;margin:20px 0;border-radius:12px}}small,.muted{{color:#596579}}.notice{{background:#fff4bd;padding:18px;border-radius:12px}}li{{margin-bottom:10px}}</style></head><body><main><header><h1>Content Radar</h1><p>EUROMASTER · {e(report['date'])}</p></header><p class="notice">Instagram: echte API-Kennzahlen. Facebook ist auf Wunsch deaktiviert. LinkedIn: öffentlicher Testbetrieb im separaten Abschnitt. Keine vollständige Branchenabdeckung.</p><p>{report['total_posts']} gelesene Beiträge · {len(report['items'])} ausgewählte Beiträge der letzten 7 Tage</p>{''.join(cards) or '<article>Keine aktuellen Instagram-Beiträge verfügbar. Quellenstatus unten prüfen.</article>'}{render_linkedin(report.get('linkedin', {}))}<section><h2>Ansätze für Euromaster</h2><p>Regelbasierte Themenhinweise aus den ausgewählten Captions und redaktionelle Vorschläge. Keine bewiesenen Erfolgsursachen oder plattformweiten Trends.</p><ul>{suggestions}</ul></section><section><h2>Quellen und Abdeckung</h2><ul>{status}</ul><p>Instagram Business Discovery, Abruf: {e(report['generated_at'])}. Bis zu 50 aktuelle Beiträge je Account; keine vollständige Pagination. Mögliche oder falsche Accountnamen werden als Fehler ausgewiesen.</p></section><section><h2>Bewertung verstehen</h2><p>Interaktionen = Likes + Kommentare. Fehlende Werte bleiben unbekannt. Vorläufige Vergleiche verwenden mindestens 5 andere Beiträge desselben Accounts und Formats, jeweils 3–90 Tage alt. Nur Beiträge im Alter von 3–7 Tagen erhalten einen Vergleichsfaktor. Unterschiedliches Messalter und bezahlte Verbreitung bleiben mögliche Einflüsse. Konten werden abwechselnd berücksichtigt; große Accounts dominieren die Auswahl nicht allein durch ihre Followerzahl.</p><p>Die Followerquote ist keine Reichweiten-Engagementrate. Reichweite, Saves, Shares und Views sind in dieser Version nicht erfasst. Tägliche Veränderungen erscheinen erst nach einem Vergleichsabruf nach ca. 24 Stunden. Spitzenbeiträge können an mehreren Tagen erscheinen; das ist als laufende Beobachtung beabsichtigt.</p></section></main></body></html>'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--send', action='store_true')
    args = parser.parse_args()
    config = json.loads(Path('config.json').read_text())
    now = datetime.now(timezone.utc)
    output = Path('reports'); output.mkdir(exist_ok=True)
    state = Path('state/instagram_history.json')
    history = json.loads(state.read_text()) if state.exists() else {}
    token = os.environ.get('META_ACCESS_TOKEN', '').strip()
    own_id = os.environ.get('INSTAGRAM_ACCOUNT_ID', '').strip()
    rows, sources = [], []
    if token and own_id:
        for account in config['instagram_accounts']:
            try:
                profile = api(account, token, own_id, config.get('meta_api_version','v26.0'))
                found = normalize(profile, now)
                rows.extend(found)
                sources.append({'account':account,'status':'OK','count':len(found)})
            except SourceError as exc:
                sources.append({'account':account,'status':'FEHLER','error':str(exc),'count':0})
            time.sleep(0.5)
    else:
        sources.append({'account':'Instagram','status':'NICHT KONFIGURIERT','error':'META_ACCESS_TOKEN und INSTAGRAM_ACCOUNT_ID als GitHub-Secrets hinterlegen.','count':0})
    linkedin = collect_linkedin(config, now)
    linkedin['items'] = select_linkedin(linkedin['items'], config.get('linkedin', {}).get('max_report_posts', 8))
    analyze(rows, history, now)
    report = {'date':now.astimezone(ZoneInfo('Europe/Berlin')).strftime('%d.%m.%Y'), 'generated_at':now.isoformat(), 'total_posts':len(rows), 'sources':sources, 'items':select(rows,config.get('max_results',10)), 'linkedin':linkedin}
    rendered = render(report)
    (output/'index.html').write_text(rendered,encoding='utf-8')
    (output/'latest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'diagnostics.json').write_text(json.dumps({'instagram':sources, 'linkedin':linkedin['sources']},ensure_ascii=False,indent=2),encoding='utf-8')
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a',encoding='utf-8') as f:
            f.write(f'## Instagram Content Radar\n\n{len(rows)} Beiträge gelesen; {len(report["items"])} aktuelle Beiträge im Report.\n\n')
            for source in sources:
                f.write(f'- `@{source["account"]}`: {source["status"]}, {source["count"]} Beiträge\n')
            f.write(f'\nLinkedIn-Testbetrieb: {len(linkedin["items"])} öffentliche Beiträge im Report (30-Tage-Fenster).\n')
            for source in linkedin['sources']:
                f.write(f'- LinkedIn `{source["account"]}`: {source["status"]}, {source["count"]} Beiträge\n')
            f.write('\nFacebook deaktiviert. LinkedIn ist ein öffentlicher Testbetrieb, keine vollständige Branchenanalyse. HTML-Report unter Artifacts herunterladen.\n')
    if not rows:
        print('::error::Keine Instagram-Beiträge abrufbar. Report und diagnostics.json enthalten den Status.')
        raise SystemExit(1)
    # Reports survive a mail error; cached snapshot updates happen only after successful/disabled mail.
    if args.send:
        send_mail(rendered, report['date'])
    for row in rows:
        snapshots = history.setdefault(row['id'], [])
        if not snapshots or (now-stamp(snapshots[-1]['at'])).total_seconds() >= 3600:
            snapshots.append({'at':now.isoformat(),'interactions':row['interactions']})
        history[row['id']] = [s for s in snapshots if stamp(s['at']) and (now-stamp(s['at'])).days < 35]
    history = {k:v for k,v in history.items() if v and (now-stamp(v[-1]['at'])).days < 35}
    state.parent.mkdir(exist_ok=True)
    state.write_text(json.dumps(history),encoding='utf-8')
    print(f'{len(rows)} Instagram-Beiträge gelesen, {len(report["items"])} im Report. Keine Zugangsdaten im Report gespeichert.')

if __name__ == '__main__':
    main()
