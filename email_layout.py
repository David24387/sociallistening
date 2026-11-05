"""Readable mail-first briefing, inline styles and table layout for email clients."""
import html
import re
from datetime import datetime

BLUE='#164194';YELLOW='#fedd00';INK='#172b4d';MUTED='#64748b'

def tidy(value,limit):
    text=re.sub(r'\s+',' ',str(value or '')).strip()
    if len(text)<=limit:return text
    return text[:limit-1].rsplit(' ',1)[0]+'…'

def entries(report):
    rows=[]
    for platform,items in [('Instagram',report.get('items',[])),('LinkedIn',report.get('linkedin',{}).get('items',[]))]:
        for row in items:
            if row.get('top_performer') and row.get('adaptation'):
                rows.append(dict(row,platform=platform))
    return sorted(rows,key=lambda r:(r.get('benchmark_factor') or 0,r.get('benchmark_percentile') or 0),reverse=True)

def heading(row):
    lines=[line.strip() for line in row.get('caption','').splitlines() if line.strip() and not line.strip().startswith('#')]
    return tidy(lines[0] if lines else 'Starker Beitrag von '+row['account'],115)

def date_label(row):
    try:return datetime.fromisoformat(row['published_at'].replace('Z','+00:00')).strftime('%d.%m.%Y')
    except (KeyError,TypeError,ValueError):return 'Datum unbekannt'

def number(value):
    return f'{value:,}'.replace(',','.') if value is not None else 'unbekannt'

def proof(row):
    factor=str(row.get('benchmark_factor','?')).replace('.',',')
    n=row.get('benchmark_n',0)
    if row.get('public_profile_sample'):
        return f'{factor}× der mittlere Interaktionswert (Median) von {n} anderen öffentlich sichtbaren Posts dieses Accounts. Vergleich: {row.get("benchmark_scope","verschiedene Formate")}. Begrenzter Profil-Ausschnitt mit unterschiedlichem Beitragsalter; keine vollständige Account-Analyse.'
    text=f'{factor}× so viele Interaktionen wie ein typischer Beitrag dieses Accounts. Vergleich: {n} andere Beiträge desselben Formats (Median).'
    if '48–72' in row.get('benchmark_mode',''):
        text+=' Vergleich bei ähnlichem Beitragsalter.'
    else:
        text+=' Die Vergleichsbeiträge waren bei ihrer Messung mindestens ebenso alt.'
    if n<8:text+=' Kleinere Vergleichsbasis.'
    return text

def counts(report,rows):
    ig=sum(r['platform']=='Instagram' for r in rows)
    li=len(rows)-ig
    return ig,li

def card(row,index):
    e=html.escape
    platform=row['platform'];account=row['account']
    form={'IMAGE':'Bildpost','VIDEO':'Video','CAROUSEL_ALBUM':'Karussell','TEXT':'Textbeitrag'}.get(row.get('format'),'Beitrag')
    source=account if platform=='LinkedIn' else '@'+account
    badge='Stark im sichtbaren Profil-Ausschnitt' if row.get('public_profile_sample') else 'Besonders stark' if row.get('performance_tier')=='Deutlicher Ausreißer' else 'Überdurchschnittlich'
    age='Best of 30 Tage' if row.get('age_hours',0)>168 else 'Aus den letzten 7 Tagen'
    if row.get('inspiration'):age+=' · Branchenfremde Inspiration'
    caption=tidy(row.get('caption',''),240)
    # Never render source content as markup or accept non-platform links.
    from urllib.parse import urlsplit
    url=row.get('url','')
    p=urlsplit(url)
    if p.scheme!='https' or p.hostname not in {'instagram.com','www.instagram.com','linkedin.com','www.linkedin.com','de.linkedin.com','at.linkedin.com','uk.linkedin.com'}:url='#'
    labels='Likes' if platform=='Instagram' else 'Reaktionen'
    idea=row['adaptation'].get('idea','')
    return f'''<tr><td style="padding:0 22px 20px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #dfe5ef;background:#ffffff;border-radius:12px;"><tr><td style="padding:22px 22px 6px;font:700 12px/1.5 Arial,sans-serif;color:{BLUE};">{index:02d} &nbsp; {e(platform)} · {e(source)} · {e(form)}</td></tr><tr><td style="padding:0 22px 14px;font:12px/1.5 Arial,sans-serif;color:{MUTED};">{e(age)} · veröffentlicht {date_label(row)}</td></tr><tr><td style="padding:0 22px 14px;font:700 21px/1.35 Arial,sans-serif;color:{INK};">{e(heading(row))}</td></tr><tr><td style="padding:0 22px 12px;font:14px/1.6 Arial,sans-serif;color:#475569;">{e(caption)}</td></tr><tr><td style="padding:0 22px 14px;font:700 14px/1.6 Arial,sans-serif;color:{INK};">{number(row.get('likes'))} {labels} &nbsp;·&nbsp; {number(row.get('comments'))} Kommentare</td></tr><tr><td style="padding:0 22px 6px;font:700 14px/1.5 Arial,sans-serif;color:{BLUE};">Warum ausgewählt · {e(badge)}</td></tr><tr><td style="padding:0 22px 18px;font:14px/1.6 Arial,sans-serif;color:{INK};">{e(proof(row))}</td></tr><tr><td style="padding:0 22px 18px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#fff9d8;border-left:4px solid {YELLOW};"><tr><td style="padding:14px 16px;font:700 14px/1.5 Arial,sans-serif;color:{INK};">Idee für Euromaster</td></tr><tr><td style="padding:0 16px 14px;font:14px/1.6 Arial,sans-serif;color:{INK};">{e(idea)}</td></tr></table></td></tr><tr><td style="padding:0 22px 22px;"><table role="presentation" cellpadding="0" cellspacing="0"><tr><td style="background:{BLUE};border-radius:6px;"><a href="{e(url,quote=True)}" style="display:inline-block;padding:12px 18px;font:700 14px/1.4 Arial,sans-serif;color:#ffffff;text-decoration:none;">Originalbeitrag ansehen →</a></td></tr></table></td></tr></table></td></tr>'''

def source_note(report,rows):
    sources=report.get('sources',[])+report.get('linkedin',{}).get('sources',[])
    limited=any(s.get('status') in ('FEHLER','EINGESCHRÄNKT','NICHT KONFIGURIERT') for s in sources)
    if report.get('data_status')=='unavailable':
        return 'Heute konnten keine Beitragsdaten geladen werden. Das ist eine Erfassungsstörung und keine Aussage darüber, ob Beiträge gut liefen.'
    note='Auswahl aus beobachteten Accounts auf Instagram und öffentlich erreichbaren LinkedIn-Beiträgen.'
    if limited:note+=' Einzelne Quellen waren heute nicht vollständig erreichbar.'
    if not rows:
        ig_bad=bool(report.get('sources')) and all(s.get('status')!='OK' for s in report['sources'])
        li_bad=bool(report.get('linkedin',{}).get('sources')) and all(s.get('status')!='OK' for s in report['linkedin']['sources'])
        if ig_bad and li_bad:note+=' Wegen eingeschränkter Daten ist heute keine verlässliche Auswahl möglich.'
    return note

def render(report):
    e=html.escape;rows=entries(report);ig,li=counts(report,rows)
    if rows:
        intro=f'{len(rows)} starke Beiträge für eure Redaktionsplanung: {ig} von Instagram, {li} von LinkedIn. Zu jedem Beispiel findet ihr den Leistungsnachweis und eine konkrete Idee für Euromaster.'
        lead=f'<tr><td style="padding:22px 28px;font:15px/1.7 Arial,sans-serif;color:{INK};">{e(intro)}</td></tr><tr><td style="padding:0 28px 18px;font:700 18px/1.5 Arial,sans-serif;color:{INK};">Heute zuerst ansehen</td></tr>'
    else:
        intro='Heute konnten die Beiträge nicht ausgewertet werden.' if report.get('data_status')=='unavailable' else 'Heute keine neuen Empfehlungen mit ausreichend belegter überdurchschnittlicher Resonanz.'
        lead=f'<tr><td style="padding:28px;font:15px/1.7 Arial,sans-serif;color:{INK};"><b>{e(intro)}</b><br><br>Die beobachteten Quellen werden täglich erneut geprüft. Bereits berichtete Beiträge werden nur bei deutlichem Wachstum erneut aufgenommen.</td></tr>'
    body=''.join(card(row,i+1) for i,row in enumerate(rows))
    li_report=report.get('linkedin',{})
    if not li and li_report.get('checked_posts') is not None:
        checked=li_report['checked_posts']
        reasons=report.get('quality',{}).get('linkedin_rejections',{})
        insufficient=sum(count for reason,count in reasons.items() if reason.startswith('Zu wenig Vergleichsdaten'))
        if checked==0:
            li_note='Heute waren keine auswertbaren LinkedIn-Beiträge erreichbar.'
        elif insufficient:
            li_note=f'{checked} Beiträge geprüft. Für eine belastbare Empfehlung fehlen noch Vergleichsdaten; die Vergleichsbasis wird weiter aufgebaut.'
        else:
            li_note=f'{checked} Beiträge geprüft. Heute erfüllt kein neuer Beitrag die Auswahlkriterien für eine Empfehlung.'
        body+=f'<tr><td style="padding:0 28px 22px;font:14px/1.6 Arial,sans-serif;color:{MUTED};"><b>LinkedIn heute</b><br>{e(li_note)}</td></tr>'
    diagnostics=report.get('diagnostics_url','')
    details=f'<br><a href="{e(diagnostics,quote=True)}" style="color:{BLUE};">Technische Details zum Lauf</a>' if diagnostics.startswith('https://github.com/') else ''
    footer=f'''<tr><td style="padding:12px 28px 28px;font:12px/1.7 Arial,sans-serif;color:{MUTED};">{e(source_note(report,rows))}<br><br><b>Zur Einordnung:</b> Die Auswahl bewertet sichtbare Interaktionen, keine Reichweite oder Verkäufe. Ideen entstehen aus Text und Format; Bilder und Videos bitte vor Umsetzung im Original prüfen. „Best of 30 Tage“ kennzeichnet ältere Beispiele.{details}<br><br>Automatisches Tagesbriefing · täglich morgens · EUROMASTER Content Radar</td></tr>'''
    return f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Euromaster Content-Inspiration · {e(report['date'])}</title></head><body style="margin:0;padding:0;background:#eef2f7;"><div style="display:none;max-height:0;overflow:hidden;opacity:0;">{e(intro)}</div><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef2f7;"><tr><td align="center" style="padding:24px 8px;"><table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:100%;max-width:640px;background:#f8fafd;"><tr><td style="padding:24px 28px;background:{BLUE};border-bottom:6px solid {YELLOW};"><p style="margin:0 0 8px;font:700 12px/1.5 Arial,sans-serif;letter-spacing:1.4px;color:{YELLOW};">EUROMASTER · {e(report['date'])}</p><h1 style="margin:0;font:700 29px/1.25 Arial,sans-serif;color:#ffffff;">Eure Content-Inspiration</h1><p style="margin:10px 0 0;font:14px/1.5 Arial,sans-serif;color:#e3ebff;">Starke Beiträge. Konkrete Ideen.</p></td></tr>{lead}{body}{footer}</table></td></tr></table></body></html>'''

def plain(report):
    rows=entries(report)
    lines=['EUROMASTER – Eure Content-Inspiration',report['date'],'']
    if not rows:lines.append('Heute konnten die Beiträge nicht ausgewertet werden.' if report.get('data_status')=='unavailable' else 'Heute keine neuen Empfehlungen mit ausreichend belegter Resonanz.')
    for i,row in enumerate(rows,1):
        lines.extend([f'{i}. {heading(row)}',f'{row["platform"]} · {row["account"]} · {date_label(row)}',f'{number(row.get("likes"))} Reaktionen · {number(row.get("comments"))} Kommentare','Warum ausgewählt: '+proof(row),'Idee für Euromaster: '+row['adaptation'].get('idea',''),row.get('url',''),''])
    if not any(r['platform']=='LinkedIn' for r in rows) and report.get('linkedin',{}).get('checked_posts') is not None:
        lines.append(f'LinkedIn: {report["linkedin"]["checked_posts"]} Beiträge geprüft, heute keine qualifizierte Empfehlung; Details in der HTML-Version.')
    lines.extend([source_note(report,rows),'Ideen aus Text und Format; Bilder und Videos vor Umsetzung prüfen.','Automatisch täglich morgens.'])
    return '\n'.join(lines)
