"""Daily report novelty; state tracks generated reports, not successful mail delivery."""
from datetime import datetime

def prepare(rows,reported,now,max_age_hours=720):
    for row in rows:
        previous=reported.get(row['id'])
        row['first_report']=previous is None
        row['eligible_for_report']=False
        row['growth_since_report']=None
        if row['age_hours']>max_age_hours:
            row['editorial_status']=f'Älter als {max_age_hours/24:g} Tage; nicht in der Tagesauswahl'
            continue
        if previous is None:
            row['eligible_for_report']=True
            row['editorial_status']='Neu im Report · aktuell (letzte 7 Tage)' if row['age_hours']<=168 else 'Neu im Report · Best of 30 Tage'
            continue
        date=datetime.fromisoformat(previous['at'])
        # Re-running the same calendar day keeps the report reviewable.
        today=date.astimezone(now.tzinfo).date()==now.date()
        old=previous.get('interactions');current=row.get('interactions')
        delta=current-old if old is not None and current is not None else None
        threshold=max(50,old*0.25) if old is not None else None
        breakout=delta is not None and threshold is not None and delta>=threshold and (now-date).total_seconds()>=18*3600
        row['growth_since_report']=delta
        row['eligible_for_report']=today or breakout
        if breakout:row['editorial_status']=f'Erneut auffällig: +{delta} Interaktionen seit dem letzten Report'
        elif today:row['editorial_status']='Heute bereits im Report'
        else:row['editorial_status']='Bereits berichtet; kein ausreichender Zuwachs'
    return rows

def record(rows,reported,now):
    for row in rows:
        # Keep first report snapshot for the day so manual reruns do not reset growth.
        previous=reported.get(row['id'])
        if previous and datetime.fromisoformat(previous['at']).astimezone(now.tzinfo).date()==now.date():continue
        reported[row['id']]={'at':now.isoformat(),'interactions':row.get('interactions')}
    return {k:v for k,v in reported.items() if (now-datetime.fromisoformat(v['at'])).days<90}
