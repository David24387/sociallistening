"""Best-effort public LinkedIn pages only. No cookies, login, proxy or challenge bypass."""
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from performance import evidence,choose

class PublicPageError(Exception):
    pass

HOSTS={'www.linkedin.com','linkedin.com','de.linkedin.com','at.linkedin.com','uk.linkedin.com'}

def valid_url(url,kind='post'):
    try:
        p=urllib.parse.urlsplit(html.unescape(url))
        port=p.port
    except ValueError:
        return None
    if p.scheme!='https' or p.hostname not in HOSTS or p.username or p.password or port:
        return None
    if kind=='post' and not re.fullmatch(r'/posts/[^/]*activity-\d+-[^/]+/?',p.path):
        return None
    if kind=='company' and not re.fullmatch(r'/company/[\w.& -]+/?',urllib.parse.unquote(p.path)):
        return None
    path=urllib.parse.quote(urllib.parse.unquote(p.path).rstrip('/'),safe='/.-_~')
    return urllib.parse.urlunsplit(('https',p.netloc,path,'',''))

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_schema=False;self.buf=[];self.schemas=[];self.posts=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='script' and a.get('type')=='application/ld+json':
            self.in_schema=True;self.buf=[]
        if tag=='a':
            url=valid_url(a.get('href',''))
            if url:self.posts.append(url)
    def handle_data(self,data):
        if self.in_schema:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self.in_schema:
            self.in_schema=False
            try:self.schemas.append(json.loads(''.join(self.buf)))
            except ValueError:pass

def walk(value):
    if isinstance(value,list):
        for child in value:yield from walk(child)
    elif isinstance(value,dict):
        yield value
        for key in ('@graph','mainEntity','mainEntityOfPage'):
            if isinstance(value.get(key),(list,dict)):yield from walk(value[key])

def integer(value):
    return value if isinstance(value,int) and not isinstance(value,bool) and value>=0 else None

def parse_post(document,url,now):
    parser=PageParser();parser.feed(document)
    expected=re.search(r'activity-(\d+)',url).group(1)
    candidates=[node for schema in parser.schemas for node in walk(schema) if node.get('datePublished') and (node.get('description') or node.get('articleBody'))]
    for node in candidates:
        identity=str(node.get('@id') or node.get('url') or '')
        if expected not in identity:continue
        try:date=datetime.fromisoformat(node['datePublished'].replace('Z','+00:00'))
        except (ValueError,TypeError):continue
        if not date.tzinfo or date>now:continue
        counts={}
        stats=node.get('interactionStatistic',[])
        if isinstance(stats,dict):stats=[stats]
        for stat in stats:
            if isinstance(stat,dict):
                action=stat.get('interactionType','')
                if isinstance(action,dict):action=action.get('@type','')
                counts[str(action).split('/')[-1]]=integer(stat.get('userInteractionCount'))
        likes=counts.get('LikeAction')
        comments=counts.get('CommentAction',integer(node.get('commentCount')))
        author=node.get('author') or node.get('creator') or {}
        if isinstance(author,list):author=author[0] if author else {}
        followers=None
        if isinstance(author,dict):
            follow=author.get('interactionStatistic',{})
            if isinstance(follow,dict) and str(follow.get('interactionType','')).endswith('FollowAction'):
                followers=integer(follow.get('userInteractionCount'))
        return {'id':'linkedin:'+expected,'account':author.get('name','LinkedIn') if isinstance(author,dict) else str(author),'platform':'LinkedIn','followers':followers,'caption':node.get('description') or node.get('articleBody',''),'url':url,'published_at':date.isoformat(),'age_hours':round((now-date).total_seconds()/3600,1),'format':'VIDEO' if node.get('@type')=='VideoObject' else ('CAROUSEL_ALBUM' if isinstance(node.get('image'),list) and len(node['image'])>1 else 'IMAGE' if node.get('image') else 'TEXT' if node.get('@type')=='SocialMediaPosting' else 'UNKNOWN'),'likes':likes,'comments':comments,'interactions':likes+comments if likes is not None and comments is not None else None,'source':'Öffentlicher Seiteninhalt (JSON-LD)','fetched_at':now.isoformat()}
    raise PublicPageError('Keine passenden öffentlichen Beitragsdaten: Anmeldeseite, Prüfseite oder geändertes Seitenformat.')

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if urllib.parse.urlsplit(newurl).hostname not in HOSTS:
            raise PublicPageError('Weiterleitung außerhalb von LinkedIn nicht verfolgt.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch(url):
    opener=urllib.request.build_opener(SafeRedirect())
    req=urllib.request.Request(url,headers={'User-Agent':'EuromasterContentRadar/0.2 (public content research)'})
    try:
        with opener.open(req,timeout=20) as response:
            return response.read(3_000_000).decode('utf-8',errors='replace')
    except urllib.error.HTTPError as exc:
        raise PublicPageError(f'HTTP {exc.code}; kein Wiederholungsversuch oder Umgehen von Sperren.') from None
    except (urllib.error.URLError,TimeoutError):
        raise PublicPageError('Netzwerkfehler oder Timeout.') from None

def round_robin(queues,limit):
    queues=[list(q) for q in queues]
    chosen=[]
    while len(chosen)<limit and any(queues):
        for queue in queues:
            if queue and len(chosen)<limit:
                chosen.append(queue.pop(0))
    return chosen

def select_posts(rows,limit=3):
    return choose(rows,limit)


def prioritize_links(group,inspected,discovered):
    # Preserve company-card order among new links. Refresh current cards before
    # archived seeds, so stale manually researched examples do not fill the run.
    latest=[u for u in group if u in discovered][:2]
    fresh=[u for u in group if u not in inspected and u in discovered and u not in latest]
    refresh=[u for u in group if u in inspected and u in discovered and u not in latest]
    backlog=[u for u in group if u not in discovered]
    return latest+fresh+refresh+backlog


def collect(config,now):
    settings=config.get('linkedin',{})
    if not settings.get('enabled',False):return {'items':[],'sources':[],'discovery':'deaktiviert'}
    state=Path('state/linkedin_known.json')
    known=json.loads(state.read_text()) if state.exists() else []
    seeds=[u for raw in settings.get('seed_posts',[]) if (u:=valid_url(raw))]
    inspected_path=Path('state/linkedin_inspected.json')
    inspected=json.loads(inspected_path.read_text()) if inspected_path.exists() else {}
    sources=[]; discovered=[]
    for raw in settings.get('company_pages',[])[:8]:
        url=valid_url(raw,'company')
        if not url:continue
        try:
            parser=PageParser();parser.feed(fetch(url))
            links=list(dict.fromkeys(parser.posts))
            discovered.extend(links[:8])
            sources.append({'account':url,'status':'OK' if links else 'EINGESCHRÄNKT','count':len(links),'error':'' if links else 'Keine Beitragslinks im öffentlichen Abruf; neue Beiträge hier nicht entdeckt.'})
        except PublicPageError as exc:
            sources.append({'account':url,'status':'FEHLER','count':0,'error':str(exc)})
        time.sleep(1)
    all_urls=list(dict.fromkeys(discovered+seeds+[u for raw in known if (u:=valid_url(raw))]))[:80]
    # Fair queues by publishing handle; one prolific company cannot consume the run.
    groups={}
    for url in all_urls:
        handle=urllib.parse.unquote(urllib.parse.urlsplit(url).path).split('/posts/',1)[1].split('_',1)[0]
        groups.setdefault(handle,[]).append(url)
    # Re-read the latest public company cards every day. Uninspected links come first;
    # then refresh current cards to measure growing resonance. No random rotation.
    queues=[prioritize_links(group,inspected,discovered) for group in groups.values()]
    work=round_robin(queues,settings.get('max_posts_per_run',18))
    rows=[]
    for url in work:
        try:
            row=parse_post(fetch(url),url,now);rows.append(row)
            inspected[url]={'at':now.isoformat(),'interactions':row['interactions'],'published_at':row['published_at'],'post':row}
            sources.append({'account':url,'status':'OK','count':1})
        except PublicPageError as exc:
            sources.append({'account':url,'status':'FEHLER','count':0,'error':str(exc)})
        time.sleep(1)
    state.parent.mkdir(exist_ok=True)
    state.write_text(json.dumps(all_urls,indent=2),encoding='utf-8')
    inspected={u:v for u,v in inspected.items() if (now-datetime.fromisoformat(v['at'])).days<90}
    inspected_path.write_text(json.dumps(inspected,indent=2),encoding='utf-8')
    return {'items':rows,'baseline_rows':[v['post'] for v in inspected.values() if 'post' in v and (now-datetime.fromisoformat(v['published_at'])).days<=90],'sources':sources,'discovery':'Best effort: öffentliche Unternehmensseiten; Startlinks sind manuell recherchiert, keine garantierte tägliche Neuentdeckung.'}

def render_section(report):
    e=html.escape
    cards=[]
    for row in report.get('items',[]):
        if not row.get('top_performer') or not row.get('adaptation'):continue
        title=row['caption'].split('\n')[0][:160]
        likes=str(row['likes']) if row['likes'] is not None else 'unbekannt'
        comments=str(row['comments']) if row['comments'] is not None else 'unbekannt'
        proof = evidence(row) if row.get('top_performer') else 'Kein qualifizierter Top-Performer.'
        adopt = row.get('adaptation') or {}
        adoption='<p><b>Übertragbares Muster:</b> '+e(adopt.get('pattern',''))+'</p><p><b>Für Euromaster:</b> '+e(adopt.get('idea',''))+'</p><p class="muted">'+e(adopt.get('basis',''))+'</p>'
        cards.append(f'<article><small>{e(row.get('editorial_status','Öffentlicher Fund'))} · LinkedIn · {e(row["account"])} · veröffentlicht {e(row["published_at"][:10])}</small><h2><a href="{e(row["url"],quote=True)}">{e(title)}</a></h2><p>{e(row["caption"][:900]).replace(chr(10),"<br>")}</p><p><b>{likes} öffentliche Reaktionen · {comments} Kommentare</b></p><p><b>Warum im Report:</b> {e(proof)}</p>{adoption}<p class="muted">Öffentliche Metadaten, keine offizielle Analytics-API. Kennzahlen können unvollständig oder verzögert sein. Paid-Einsatz, Reichweite und Conversion unbekannt. Abruf: {e(row["fetched_at"])}</p></article>')
    status=''.join(f'<li>{e(s["account"])}: {e(s["status"])} {e(s.get("error",""))}</li>' for s in report.get('sources',[]))
    return '<section><h2>LinkedIn · öffentlicher Testbetrieb</h2><p>Starke Beiträge der letzten 30 Tage: mindestens 5 Vergleichsposts desselben Accounts und Formats, mindestens 1,5× Median, oberste 20 % und mindestens 50 Interaktionen. Aktuelle Posts und ältere Best-of-Beispiele werden beim Beitrag unterschieden. Bereits berichtete Beiträge erscheinen an Folgetagen nur bei deutlichem Interaktionszuwachs. Keine vollständige Branchenabdeckung und kein Vergleich mit Instagram. Keine Auffüllung ohne Benchmark. Vergleichsmodus steht beim Beitrag; ohne ausreichende Historie kann dieser Abschnitt leer bleiben. '+e(report.get('discovery',''))+'</p></section>'+(''.join(cards) or '<article>Heute kein neuer LinkedIn-Beitrag mit ausreichenden Vergleichsdaten und erfüllten Top-Performer-Schwellen. Quellenstatus unten beachten.</article>')+'<section><h2>LinkedIn-Quellenstatus</h2><ul>'+status+'</ul></section>'
