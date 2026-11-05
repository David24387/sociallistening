"""Strict editorial outlier rules, not proof of reach, conversion or organic success."""
import math
import re
import statistics
from datetime import datetime

GIVEAWAY=re.compile(r'gewinnspiel|giveaway|verlosung|teilnahmebedingungen|markier.{0,35}freund',re.I)

def sample_48h(row,history):
    samples=[]
    for value in history.get(row['id'],[]):
        try:
            age=(datetime.fromisoformat(value['at'])-datetime.fromisoformat(row['published_at'])).total_seconds()/3600
        except (ValueError,TypeError,KeyError):continue
        if 48<=age<=72 and value.get('interactions') is not None:
            samples.append((age,value['interactions']))
    if 48<=row['age_hours']<=72 and row.get('interactions') is not None:
        samples.append((row['age_hours'],row['interactions']))
    return min(samples)[1] if samples else None

def assess(rows,history=None,settings=None):
    history=history or {};settings=settings or {}
    min_peers=settings.get('min_peers',8)
    min_interactions=settings.get('min_interactions',100)
    min_factor=settings.get('min_factor',2.0)
    for row in rows:
        row.update(top_performer=False,performance_reason='',benchmark_n=0,benchmark_median=None,benchmark_factor=None,benchmark_percentile=None)
        if row.get('format') in ('UNKNOWN','POST'):
            row['performance_reason']='Format nicht zuverlässig erfasst';continue
        if row.get('interactions') is None:
            row['performance_reason']='Interaktionen unvollständig';continue
        if not 48<=row['age_hours']<=168:
            row['performance_reason']='Außerhalb des Messfensters von 2–7 Tagen';continue
        if GIVEAWAY.search(row.get('caption','')):
            row['performance_reason']='Gewinnspiel/Verlosung ausgeschlossen';continue
        peers=[p for p in rows if p['id']!=row['id'] and p['account']==row['account'] and p['format']==row['format'] and p.get('interactions') is not None and p['age_hours']<=2160 and not GIVEAWAY.search(p.get('caption',''))]
        own_48=sample_48h(row,history)
        equal=[value for p in peers if (value:=sample_48h(p,history)) is not None]
        if own_48 is not None and len(equal)>=min_peers:
            values=equal;own=own_48;mode='48–72 Stunden nach Veröffentlichung'
        else:
            values=[p['interactions'] for p in peers if p['age_hours']>=max(72,row['age_hours'])]
            own=row['interactions'];mode='Öffentliche Gesamtinteraktionen; Vergleichsposts mindestens ebenso alt'
        row.update(benchmark_n=len(values),benchmark_mode=mode,performance_interactions=own)
        if len(values)<min_peers:
            row['performance_reason']=f'Zu wenig Vergleichsdaten ({len(values)}/{min_peers})';continue
        median=statistics.median(values)
        # A zero baseline cannot support a meaningful multiplier.
        if median<=0:
            row['performance_reason']='Kein belastbarer Medianwert';continue
        factor=own/median
        cutoff=sorted(values)[max(0,math.ceil(0.9*len(values))-1)]
        percentile=100*sum(v<=own for v in values)/len(values)
        row.update(benchmark_median=median,benchmark_factor=round(factor,2),benchmark_percentile=round(percentile),benchmark_p90=cutoff)
        row['top_performer']=own>=min_interactions and factor>=min_factor and own>=cutoff
        row['performance_reason']='Alle Top-Performer-Schwellen erfüllt' if row['top_performer'] else 'Resonanz erfüllt die strengen Schwellen nicht'
    return rows

def adaptation(row):
    """Grounded caption/format patterns; no claim to have watched the video."""
    text=row.get('caption','').lower()
    if GIVEAWAY.search(text):return None
    rules=[
        (bool(re.search(r'irrt[uü]m|myth|wusstest|stimmt das|falsch gedacht',text)), 'Mythos oder Wissenslücke', '„Müssen Reifen immer paarweise ersetzt werden?“ als fachlich geprüftes Expertenformat: Frage, Erklärung am Reifen, Beratungshinweis.'),
        (bool(re.search(r'fehler|nicht machen|vermeiden|niemals',text)), 'Fehler vermeiden', '„Drei Fehler bei der Reifenlagerung“: pro Fehler eine konkrete Erklärung und eine richtige Vorgehensweise aus dem Werkstattalltag.'),
        ('vorher' in text and 'nachher' in text, 'Vorher–nachher', 'Einen echten Autoglas-Auftrag vor und nach dem Austausch zeigen; dazu kurz erklären, welche Arbeitsschritte und Prüfungen erforderlich waren.'),
        (bool(re.search(r'kosten|teuer|sparen|preis',text)), 'Kosten verständlich machen', '„Was gehört eigentlich zum Reifenservice?“ als transparente Leistungsübersicht mit echten Arbeitsschritten statt eines isolierten Preisversprechens.'),
        (bool(re.search(r'schritt|anleitung|tipps|so geht|checkliste',text)), 'Praktische Anleitung', '„Reifencheck vor der nächsten Fahrt“ als kurze Schrittfolge: Zustand ansehen, Luftdruck nach Fahrzeugvorgabe prüfen, bei Auffälligkeiten Fachbetrieb kontaktieren.'),
        (row.get('format')=='CAROUSEL_ALBUM', 'Karussellstruktur (Format nachgewiesen, Bildinhalt ungeprüft)', 'Eine eigene Wissensserie „Was Ihr Reifen verrät“: auffälliges Verschleißbild, mögliche Ursachen und nächster Prüfschritt. Die konkrete Bilddramaturgie des Originals vor Umsetzung manuell prüfen.')
    ]
    for matches,pattern,idea in rules:
        if matches:return {'pattern':pattern,'idea':idea,'basis':'Regelbasiert aus Caption und Format; keine Bild-/Videoanalyse und kein bewiesener Erfolgsgrund.'}
    if row.get('inspiration'):
        return None
    if any(w in text for w in ('reifen','werkstatt','autoglas','brems','pannen')):
        return {'pattern':'Automotive-Thema mit belegter außergewöhnlicher Resonanz','idea':'Die konkrete Kundenfrage dieses Beitrags aufgreifen und von einer Euromaster-Fachkraft an einem echten Werkstattbeispiel erklären lassen. Original vor der Umsetzung inhaltlich prüfen.','basis':'Regelbasierter Themenvorschlag; keine Medienanalyse oder bewiesene Erfolgsursache.'}
    return None

def choose(rows,limit=5,max_inspiration=2,max_per_account=2):
    candidates=[]
    for row in rows:
        if not row.get('top_performer') or not row.get('eligible_for_report',True):continue
        row['adaptation']=adaptation(row)
        if row['adaptation']:candidates.append(row)
    candidates.sort(key=lambda r:(r['benchmark_factor'],r['benchmark_percentile'],r['performance_interactions']),reverse=True)
    selected=[];accounts={};inspiration=0
    for row in candidates:
        if len(selected)>=limit:break
        if accounts.get(row['account'],0)>=max_per_account:continue
        if row.get('inspiration') and inspiration>=max_inspiration:continue
        selected.append(row);accounts[row['account']]=accounts.get(row['account'],0)+1
        inspiration+=bool(row.get('inspiration'))
    return selected

def evidence(row):
    return f"{row['benchmark_factor']}× Account-Median ({row['benchmark_median']:g}), oberste 10 % der {row['benchmark_n']} Vergleichsposts desselben Formats. Vergleichswert dieses Posts: {row['performance_interactions']}. Modus: {row['benchmark_mode']}."
