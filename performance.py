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
    min_peers=settings.get('min_peers',5)
    min_interactions=settings.get('min_interactions',50)
    min_factor=settings.get('min_factor',1.5)
    min_percentile=settings.get('min_percentile',80)
    min_age=settings.get('min_age_hours',24)
    max_age=settings.get('max_age_hours',720)
    for row in rows:
        row.update(top_performer=False,performance_reason='',benchmark_n=0,benchmark_median=None,benchmark_factor=None,benchmark_percentile=None)
        if row.get('format') in ('UNKNOWN','POST'):
            row['performance_reason']='Format nicht zuverlässig erfasst';continue
        if row.get('interactions') is None:
            row['performance_reason']='Interaktionen unvollständig';continue
        if not min_age<=row['age_hours']<=max_age:
            row['performance_reason']=f'Außerhalb des Messfensters von {min_age/24:g}–{max_age/24:g} Tagen';continue
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
        cutoff=sorted(values)[max(0,math.ceil(min_percentile/100*len(values))-1)]
        percentile=100*sum(v<=own for v in values)/len(values)
        row.update(benchmark_median=median,benchmark_factor=round(factor,2),benchmark_percentile=round(percentile),benchmark_p90=cutoff)
        row['top_performer']=own>=min_interactions and factor>=min_factor and own>=cutoff
        row['performance_tier']='Deutlicher Ausreißer' if row['top_performer'] and factor>=2 and percentile>=90 and own>=100 else 'Stark im Accountvergleich' if row['top_performer'] else 'Nicht qualifiziert'
        row['benchmark_confidence']='Kleinere Vergleichsbasis' if len(values)<8 else 'Vergleichsbasis vorhanden'
        row['performance_reason']='Alle Schwellen für starke Resonanz erfüllt' if row['top_performer'] else 'Resonanz nicht ausreichend über dem Accountvergleich'
    return rows

def adaptation(row):
    """Caption-grounded editorial transfer; never infer unseen image/video content."""
    caption = re.sub(r'https?://\\S+|#[\\w]+|@[\\w]+', ' ', row.get('caption', '') or '')
    text = caption.lower()
    if GIVEAWAY.search(text) or re.search(r'datenschutzkonferenz|financial results|finanzergebnisse|quartalsergebnisse|hauptversammlung|strategic plan', text):
        return None

    def has(*terms):
        return any(re.search(term, text) for term in terms)

    # Match the specific subject first, before broad storytelling formats.
    topics = [
        (('steinschlag', 'windschutzscheib', 'autoglas', 'scheibenreparatur'), 'Autoglas', 'Steinschlag in der Windschutzscheibe', 'Ein echtes Autoglas-Beispiel zeigen: Wann ist eine Reparatur möglich und wann muss die Scheibe ersetzt werden? Fachliche Voraussetzungen prüfen.'),
        (('aquaplaning', 'nassbrems', 'bremsweg', 'nässe'), 'Sicherheit bei Nässe', 'Reifen und Bremsweg auf nasser Straße', 'Ein Karussell zur Frage „Was beeinflusst den Bremsweg bei Nässe?“ entwickeln: Reifenprofil, Geschwindigkeit und Abstand fachlich korrekt erklären.'),
        (('profiltiefe', 'reifenprofil', 'abgefahren', 'reifenverschleiß', 'verschleißbild'), 'Reifenverschleiß', 'Auffälligkeiten am Reifenprofil', 'An einem echten Reifen verschiedene Verschleißbilder erklären und zeigen, wann eine fachliche Prüfung sinnvoll ist.'),
        (('winterreifen', 'sommerreifen', 'ganzjahresreifen', 'reifenwechsel', 'räderwechsel'), 'Saisonaler Reifenwechsel', 'Passende Bereifung und Wechselzeitpunkt', 'Eine konkrete Kundenfrage zur saisonalen Bereifung als Karussell beantworten: Was ist zu beachten und wann ist ein Werkstatttermin sinnvoll? DE/AT-Regeln getrennt prüfen.'),
        (('lkw', 'truck', 'nutzfahrzeug', 'fuhrpark', 'flotten', 'fleet'), 'Flotten- und LKW-Service', 'Reifenservice für gewerbliche Fahrzeuge', 'Einen realen Ablauf aus dem Euromaster-Flotten- oder LKW-Service zeigen: Herausforderung, Organisation und Nutzen für den Fuhrpark.'),
        (('pannenhilfe', 'pannendienst', 'panneneinsatz', 'notdienst'), 'Pannenservice', 'Hilfe bei einer Reifenpanne', 'Einen echten Euromaster-Panneneinsatz als Dreischritt erzählen: Herausforderung, Vorgehen und Ergebnis für den Kunden.'),
        (('batterie', 'akku', 'startproblem'), 'Batterie und Startprobleme', 'Startprobleme und Batterieprüfung', 'Eine Fachkraft erklärt anhand eines realen Beispiels, welche Anzeichen auf eine schwache Fahrzeugbatterie hindeuten und wann ein Check sinnvoll ist.'),
        (('ausbildung', 'azubi', 'karriere', 'recruiting', 'stellenangebot', 'bewerbung'), 'Recruiting', 'Berufsalltag bei Euromaster', 'Ein kurzes Recruiting-Reel mit einer echten Fachkraft drehen: konkrete Aufgabe, überraschender Einblick und ein authentischer Grund für den Beruf.'),
        (('werkstatt', 'monteur', 'mechaniker', 'kolleg', 'mitarbeitende', 'mitarbeiter', 'team'), 'Menschen im Service', 'Menschen hinter der Werkstattleistung', 'Eine Euromaster-Fachkraft bei einem tatsächlichen Arbeitsschritt begleiten und erklären lassen, was daran für Kunden wichtig ist.'),
        (('reifenlagerung', 'einlagerung'), 'Reifenlagerung', 'Reifen richtig lagern', 'Drei konkrete Fehler bei der Reifenlagerung anhand echter Beispiele zeigen und die korrekte Vorgehensweise erklären.'),
        (('luftdruck', 'reifendruck'), 'Reifendruck', 'Reifendruck richtig kontrollieren', 'Eine kurze Demonstration zur Prüfung des Reifendrucks nach Fahrzeugvorgabe erstellen und typische Missverständnisse aufklären.'),
        (('kosten', 'teuer', 'sparen', 'preisvergleich', 'preistransparenz'), 'Kosten und Leistung', 'Leistungsumfang transparent erklären', 'Anhand eines realen Reifenservice-Auftrags erläutern, welche Arbeitsschritte zur Leistung gehören, ohne pauschale Preisversprechen.'),
    ]
    selected = next(((label, subject, idea) for terms, label, subject, idea in topics if has(*(re.escape(t) for t in terms))), None)
    if selected:
        label, subject, idea = selected
        if has(r'award', r'auszeichnung', r'bronze', r'goldmedaille', r'silbermedaille') and has(r'pannen', r'service'):
            idea = 'Einen echten Euromaster-Panneneinsatz als Dreischritt erzählen: Welche Herausforderung gab es, wie hat das Team gehandelt und welches Ergebnis hatte der Kunde? Die fachliche Leistung mit konkreten Fakten belegen; keine fremde Auszeichnung übernehmen.'
            label = 'Besondere Serviceleistung zeigen'
        elif has(r'award', r'auszeichnung') and has(r'hr', r'team', r'mitarbeit'):
            label = 'Anerkennung mit konkreter Leistung verbinden'
            idea = 'Eine echte Auszeichnung oder belegbares Kundenlob für ein Euromaster-Team zum Anlass nehmen: Leistung und beteiligte Kolleginnen und Kollegen zeigen, statt nur einen Pokal zu posten.'
        elif has(r'irrt[uü]m', r'myth', r'wusstest', r'stimmt das'):
            idea = f'Ein fachlich geprüftes Mythos-oder-Fakt-Format zum Thema „{subject}“ entwickeln: Behauptung, Erklärung und konkreter Praxistipp. ' + idea
        elif has(r'fehler', r'nicht machen', r'vermeiden', r'niemals'):
            idea = f'Die häufigsten Fehler rund um „{subject}“ erklären: pro Fehler eine reale Situation, die richtige Vorgehensweise und ein kurzer Werkstatttipp. ' + idea
        elif has(r'vorher', r'nachher'):
            idea = f'Einen echten Vorher-nachher-Fall zu „{subject}“ dokumentieren; Bildmaterial und fachliche Aussage vor Veröffentlichung prüfen. ' + idea
        return {'pattern': label, 'idea': idea, 'basis': 'Themenbezogen aus Caption; keine Bild-/Videoanalyse und kein bewiesener Erfolgsgrund.'}

    # Do not turn a generic keyword into the same recycled tire tip.
    if has(r'award', r'auszeichnung'):
        return {'pattern':'Anerkennung mit konkreter Leistung verbinden', 'idea':'Eine echte Auszeichnung oder belegbares Kundenlob für ein Euromaster-Team zum Anlass nehmen: Leistung und beteiligte Kolleginnen und Kollegen zeigen, statt nur einen Pokal zu posten.', 'basis':'Regelbasiert aus Caption; Original prüfen.'}
    return None

def choose(rows,limit=5,max_inspiration=4,max_per_account=1):
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
    if row.get('public_profile_sample'):
        return f"{row['benchmark_factor']}× Median der {row['benchmark_n']} anderen öffentlich sichtbaren Account-Posts; {row.get('benchmark_scope','verschiedene Formate')}. Begrenzter Profil-Ausschnitt mit unterschiedlichem Beitragsalter, keine vollständige Account-Analyse."
    return f"{row.get('performance_tier','Starker Beitrag')}: {row['benchmark_factor']}× Account-Median ({row['benchmark_median']:g}); mindestens so viele Interaktionen wie {row['benchmark_percentile']} % der {row['benchmark_n']} Vergleichsposts desselben Formats. Vergleichswert dieses Posts: {row['performance_interactions']}. {row.get('benchmark_confidence','')}. Modus: {row['benchmark_mode']}."


def assess_public_linkedin(rows,settings=None):
    """Rank within the public profile excerpt, never pretend full analytics/age control."""
    settings=settings or {};minimum=settings.get('min_peers',5)
    for row in rows:
        row.update(top_performer=False,performance_reason='',benchmark_n=0,benchmark_median=None,benchmark_factor=None,benchmark_percentile=None,public_profile_sample=True)
        if row.get('interactions') is None:
            row['performance_reason']='Interaktionen unvollständig';continue
        if not settings.get('min_age_hours',24)<=row['age_hours']<=settings.get('max_age_hours',720):
            row['performance_reason']='Außerhalb des Messfensters von 1–30 Tagen';continue
        if GIVEAWAY.search(row.get('caption','')):
            row['performance_reason']='Gewinnspiel/Verlosung ausgeschlossen';continue
        pool=[p for p in rows if p['id']!=row['id'] and p['account']==row['account'] and p.get('interactions') is not None and 24<=p['age_hours']<=2160 and not GIVEAWAY.search(p.get('caption',''))]
        same=[p for p in pool if p['format']==row['format'] and row['format'] not in ('UNKNOWN','POST')]
        peers=same if len(same)>=minimum else pool
        scope='gleiches Format' if peers is same else 'verschiedene Formate'
        values=[p['interactions'] for p in peers]
        row.update(benchmark_n=len(values),benchmark_scope=scope,benchmark_mode='Öffentlich sichtbarer Profil-Ausschnitt; unterschiedliche Beitragsalter',performance_interactions=row['interactions'])
        if len(values)<minimum:
            row['performance_reason']=f'Zu wenig öffentliche Vergleichsposts ({len(values)}/{minimum})';continue
        median=statistics.median(values)
        if median<=0:
            row['performance_reason']='Kein belastbarer Medianwert';continue
        own=row['interactions'];factor=own/median
        percentile=100*sum(v<=own for v in values)/len(values)
        cutoff=sorted(values)[max(0,math.ceil(settings.get('min_percentile',80)/100*len(values))-1)]
        row.update(benchmark_median=median,benchmark_factor=round(factor,2),benchmark_percentile=round(percentile),benchmark_p90=cutoff)
        row['top_performer']=own>=settings.get('min_interactions',50) and factor>=settings.get('min_factor',1.5) and own>=cutoff
        row['performance_tier']='Stark im sichtbaren LinkedIn-Ausschnitt' if row['top_performer'] else 'Nicht qualifiziert'
        row['benchmark_confidence']='Begrenzter öffentlicher Ausschnitt; '+scope+', keine Altersbereinigung'
        row['performance_reason']='Starke Resonanz im öffentlichen Profil-Ausschnitt' if row['top_performer'] else 'Resonanz nicht ausreichend über dem öffentlichen Profilvergleich'
    return rows
