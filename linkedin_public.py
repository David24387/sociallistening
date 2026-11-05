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
        return {'id':'linkedin:'+expected,'account':author.get('name','LinkedIn') if isinstance(author,dict) else str(author),'platform':'LinkedIn','followers':followers,'caption':node.get('description') or node.get('articleBody',''),'url':url,'published_at':date.isoformat(),'age_hours':round((now-date).total_seconds()/3600,1),'format':'VIDEO' if node.get('@type')=='VideoObject' else 'POST','likes':likes,'comments':comments,'interactions':likes+comments if likes is not None and comments is not None else None,'source':'Öffentlicher Seiteninhalt (JSON-LD)','fetched_at':now.isoformat()}
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

def select_posts(rows,limit=8):
    groups={}
    words=('reifen','werkstatt','autoglas','steinschlag','brems','fuhrpark','flotte','pannen','verkehr','auto','mobilität')
    for row in rows:
        if row['age_hours']<=168 and row.get('eligible_for_report',True):
            row['topic_relevance']=sum(word in row['caption'].lower() for word in words)
            groups.setdefault(row['account'],[]).append(row)
    for group in groups.values():
        group.sort(key=lambda r:(r['topic_relevance']>0,r.get('first_report',True),r['interactions'] is not None,r['interactions'] or 0),reverse=True)
    # Prioritize accounts with relevant content while preserving account diversity.
    queues=sorted(groups.values(),key=lambda g:g[0]['topic_relevance']>0,reverse=True)
    return round_robin(queues,limit)


def prioritize_links(group,inspected,discovered):
    # Preserve company-card order among new links. Refresh current cards before
    # archived seeds, so stale manually researched examples do not fill the run.
    fresh=[u for u in group if u not in inspected and u in discovered]
    refresh=[u for u in group if u in inspected and u in discovered]
    backlog=[u for u in group if u not in discovered]
    return fresh+refresh+backlog


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
            inspected[url]={'at':now.isoformat(),'interactions':row['interactions'],'published_at':row['published_at']}
            sources.append({'account':url,'status':'OK','count':1})
        except PublicPageError as exc:
            sources.append({'account':url,'status':'FEHLER','count':0,'error':str(exc)})
        time.sleep(1)
    state.parent.mkdir(exist_ok=True)
    state.write_text(json.dumps(all_urls,indent=2),encoding='utf-8')
    inspected={u:v for u,v in inspected.items() if (now-datetime.fromisoformat(v['at'])).days<90}
    inspected_path.write_text(json.dumps(inspected,indent=2),encoding='utf-8')
    return {'items':rows,'sources':sources,'discovery':'Best effort: öffentliche Unternehmensseiten; Startlinks sind manuell recherchiert, keine garantierte tägliche Neuentdeckung.'}

def render_section(report):
    e=html.escape
    cards=[]
    for row in report.get('items',[]):
        title=row['caption'].split('\n')[0][:160]
        likes=str(row['likes']) if row['likes'] is not None else 'unbekannt'
        comments=str(row['comments']) if row['comments'] is not None else 'unbekannt'
        cards.append(f'<article><small>{e(row.get('editorial_status','Öffentlicher Fund'))} · LinkedIn · {e(row["account"])} · veröffentlicht {e(row["published_at"][:10])}</small><h2><a href="{e(row["url"],quote=True)}">{e(title)}</a></h2><p>{e(row["caption"][:900]).replace(chr(10),"<br>")}</p><p><b>{likes} öffentliche Reaktionen · {comments} Kommentare</b></p><p class="muted">Öffentliche Metadaten, keine offizielle Analytics-API. Kennzahlen können unvollständig oder verzögert sein. Kein belegter Performance-Vorsprung. Abruf: {e(row["fetched_at"])}</p></article>')
    status=''.join(f'<li>{e(s["account"])}: {e(s["status"])} {e(s.get("error",""))}</li>' for s in report.get('sources',[]))
    return '<section><h2>LinkedIn · öffentlicher Testbetrieb</h2><p>Tagesauswahl aus den letzten 7 Tagen. Bereits berichtete Beiträge erscheinen an Folgetagen nur bei deutlichem Interaktionszuwachs. Keine vollständige Branchenabdeckung und kein Vergleich mit Instagram. Accounts werden abwechselnd berücksichtigt; innerhalb eines Accounts werden Themenbezug und sichtbare Interaktionen bevorzugt. Kein altersbereinigter Erfolgsvergleich. '+e(report.get('discovery',''))+'</p></section>'+(''.join(cards) or '<article>Keine neuen oder deutlich gewachsenen LinkedIn-Beiträge für diese Tagesauswahl. Quellenstatus unten beachten.</article>')+'<section><h2>LinkedIn-Quellenstatus</h2><ul>'+status+'</ul></section>'
