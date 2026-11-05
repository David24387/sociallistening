"""Free public-search discovery. No platform login, paid API or invented metrics."""
import argparse
import hashlib
import html
import json
import os
import re
import smtplib
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

PLATFORMS = {'instagram.com': ('/p/', '/reel/'), 'linkedin.com': ('/posts/', '/feed/update/'), 'facebook.com': ('/posts/', '/videos/', '/reel/', '/watch/')}

def canonical(url):
    p = urllib.parse.urlsplit(url)
    host = (p.hostname or '').lower().removeprefix('www.').removeprefix('m.')
    if host in ('de.linkedin.com', 'at.linkedin.com', 'uk.linkedin.com'):
        host = 'linkedin.com'
    if p.scheme != 'https' or host not in PLATFORMS:
        return None
    if not any(part in p.path for part in PLATFORMS[host]):
        return None
    query = urllib.parse.parse_qs(p.query)
    keep = {k: query[k][0] for k in ('v', 'story_fbid', 'id') if k in query}
    return urllib.parse.urlunsplit(('https', host, p.path.rstrip('/'), urllib.parse.urlencode(keep), ''))

def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', value or ''))).strip()

def parse_feed(data):
    root = ET.fromstring(data)
    if root.tag != 'rss':
        raise ValueError('Suchquelle lieferte keinen RSS-Feed')
    rows = []
    for item in root.findall('./channel/item'):
        url = canonical(item.findtext('link', ''))
        if url:
            rows.append({'url': url, 'title': clean(item.findtext('title')), 'excerpt': clean(item.findtext('description'))[:600], 'published_at': None, 'metrics': None})
    return rows

def discover(config, day):
    # Rotate brands for coverage without sending dozens of requests every day.
    brands = config['brands']
    start = day % len(brands)
    brands = brands[start:] + brands[:start]
    queries = [f'site:{host} {brand} Reifen Werkstatt' for brand in brands for host in PLATFORMS]
    queries += [f'site:{host} {topic}' for topic in config['topics'] for host in PLATFORMS]
    # Include topic discovery before remaining brand queries.
    queries = queries[:9] + queries[-len(config['topics'])*3:] + queries[9:-len(config['topics'])*3]
    found, errors, diagnostics = {}, [], []
    for query in queries[:config.get('max_queries', 18)]:
        endpoint = 'https://www.bing.com/search?' + urllib.parse.urlencode({'q': query, 'format': 'rss', 'count': 10})
        try:
            req = urllib.request.Request(endpoint, headers={'User-Agent': 'EuromasterContentDiscovery/0.1'})
            with urllib.request.urlopen(req, timeout=25) as response:
                data = response.read(2_000_000)
                rows = parse_feed(data)
                raw = ET.fromstring(data).findall('./channel/item')
                diagnostics.append({'query': query, 'raw_count': len(raw), 'post_count': len(rows), 'rejected_links': [item.findtext('link', '') for item in raw if not canonical(item.findtext('link', ''))][:5]})
            for row in rows:
                row['query'] = query
                found.setdefault(row['url'], row)
        except Exception as exc:
            errors.append({'query': query, 'error': type(exc).__name__ + ': ' + str(exc)[:180]})
        time.sleep(1)
    Path('reports').mkdir(exist_ok=True)
    Path('reports/diagnostics.json').write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding='utf-8')
    return list(found.values()), errors

IDEAS = [
    ('reifen', 'Wissensgrafik: Drei Reifenprüfungen vor der nächsten Fahrt – mit klaren Prüfschritten und Werkstatt-CTA.'),
    ('glas', 'Kurzes Video: Steinschlag entdeckt – welche nächsten Schritte sind sinnvoll?'),
    ('werkstatt', 'Einblick in einen tatsächlichen Werkstattablauf: Kundenfrage, Prüfung und verständliche Erklärung.')
]

def relevance(row):
    text = (row['title'] + ' ' + row['excerpt']).lower()
    return sum(word in text for word in ('reifen', 'werkstatt', 'autoglas', 'winter', 'brems', 'michelin', 'continental', 'adac', 'öamtc'))

def render(report):
    esc = html.escape
    cards = []
    for row in report['items']:
        cards.append(f'<article><small>{esc(urllib.parse.urlsplit(row["url"]).hostname or "")} · neu gefunden</small><h2><a href="{esc(row["url"], quote=True)}">{esc(row["title"])}</a></h2><p>{esc(row["excerpt"])}</p><p class="muted">Suchauszug; Original und Datum prüfen. Performance nicht gemessen.</p></article>')
    content = ''.join(cards) or '<article>Heute keine neuen passenden Beiträge gefunden. Das bedeutet nicht, dass keine veröffentlicht wurden.</article>'
    ideas = ''.join('<li>' + esc(idea) + '</li>' for _, idea in IDEAS)
    return f'''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Euromaster Content Radar</title><style>body{{margin:0;background:#f2f5fa;font:16px/1.6 Arial,sans-serif;color:#172b4d}}main{{max-width:900px;margin:auto;padding:28px}}header{{background:#164194;color:white;padding:28px;border-bottom:8px solid #fedd00;border-radius:16px}}h1{{margin:0;font-size:32px}}h2{{font-size:20px}}a{{color:#164194}}article,section{{background:white;padding:24px;margin-top:18px;border-radius:12px}}.muted,small{{color:#596579}}.notice{{background:#fff7cf;padding:18px;border-radius:12px}}</style><main><header><h1>Content Radar</h1><p>EUROMASTER · {esc(report['date'])}</p></header><p class="notice">Kostenlose Content-Recherche: öffentlich indexierte Fundstücke, keine vollständige Plattformabdeckung. „Neu“ bedeutet erstmals gefunden, nicht neu veröffentlicht. Keine Rangliste erfolgreicher Posts: Likes, Reichweite und bezahlte Verbreitung sind unbekannt.</p><p>{len(report['items'])} neue Fundstücke · {report['total_found']} passende Suchtreffer · {len(report['errors'])} Quellenfehler</p>{content}<section><h2>Redaktionelle Ansätze für Euromaster</h2><p>Allgemeine Vorschläge, keine aus Performance abgeleiteten Trends:</p><ul>{ideas}</ul></section><section><h2>Datenqualität</h2><p>Quelle: öffentliche Bing-Suchfeeds. Reihenfolge nach Themenrelevanz. Veröffentlichungsdaten unbestätigt. Fehlende Kennzahlen bleiben unbekannt.</p><p>{esc(json.dumps(report['errors'], ensure_ascii=False)) if report['errors'] else 'Keine technischen Quellenfehler gemeldet.'}</p></section></main></html>'''

def send_mail(report_html, date):
    required = ('SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD', 'MAIL_FROM', 'MAIL_TO')
    if not all(os.environ.get(key) for key in required):
        print('Mail nicht versendet: SMTP-Konfiguration unvollständig.')
        return False
    msg = EmailMessage()
    msg['Subject'] = 'Euromaster Content Radar – ' + date
    msg['From'], msg['To'] = os.environ['MAIL_FROM'], os.environ['MAIL_TO']
    msg.set_content('Der heutige Content-Report ist in der HTML-Version dieser E-Mail enthalten.')
    msg.add_alternative(report_html, subtype='html')
    with smtplib.SMTP(os.environ['SMTP_HOST'], int(os.environ.get('SMTP_PORT', '587')), timeout=30) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
        smtp.send_message(msg)
    print('Mail versendet.')
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--send', action='store_true')
    args = parser.parse_args()
    config = json.loads(Path('config.json').read_text())
    now = datetime.now(timezone.utc)
    state_path = Path('state/seen.json')
    seen = json.loads(state_path.read_text()) if state_path.exists() else {}
    rows, errors = discover(config, now.toordinal())
    fresh = [r for r in rows if hashlib.sha256(r['url'].encode()).hexdigest() not in seen]
    fresh.sort(key=relevance, reverse=True)
    items = [r for r in fresh if relevance(r) > 0][:config.get('max_results', 10)]
    report = {'date': now.strftime('%d.%m.%Y'), 'generated_at': now.isoformat(), 'items': items, 'total_found': len(rows), 'errors': errors}
    output = Path('reports'); output.mkdir(exist_ok=True)
    rendered = render(report)
    (output / 'index.html').write_text(rendered)
    (output / 'latest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as handle:
            handle.write(f'## Content-Recherche\n\n{len(rows)} passende Beiträge, {len(items)} neue Einträge, {len(errors)} Quellenfehler.\n\n')
            if not rows:
                handle.write('⚠️ **Recherche ohne brauchbare Treffer.** Dieser Lauf liefert keine Content-Auswertung. Im Artifact liegen HTML-Report und diagnostics.json mit verworfenen Suchtreffern.\n\n')
            handle.write('Geprüfte Startbeispiele: [BEISPIELE.md](https://github.com/David24387/sociallistening/blob/main/BEISPIELE.md). Diese sind manuell recherchiert und keine täglichen Funde.\n')
    if not rows:
        print('::warning::Keine passenden Social-Beiträge gefunden. Recherche ist nicht als funktionsfähig bestätigt; diagnostics.json prüfen.')
    if args.send:
        send_mail(rendered, report['date'])
    # Only delivered report entries are suppressed next time; excess discoveries remain eligible.
    for row in items:
        seen[hashlib.sha256(row['url'].encode()).hexdigest()] = now.isoformat()
    state_path.parent.mkdir(exist_ok=True)
    state_path.write_text(json.dumps(dict(list(seen.items())[-5000:]), indent=2))
    print(f'{len(rows)} passende Treffer, {len(items)} neue Reporteinträge, {len(errors)} Quellenfehler.')
    if errors and len(errors) == config.get('max_queries', 18):
        raise SystemExit('Alle Suchabfragen fehlgeschlagen. Report enthält den Fehlerstatus.')

if __name__ == '__main__':
    main()
