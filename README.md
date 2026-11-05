# EUROMASTER Content Radar – kostenlose erste Version

Experimentelle Recherche öffentlich indexierter Instagram-, LinkedIn- und Facebook-Beiträge. HTML-Report mit Original-Links, Suchauszügen und Quellenstatus. Keine kostenpflichtigen APIs oder KI-Dienste. Python-Standardbibliothek.

**Noch keine Performance-Analyse:** Reichweite, Likes, Saves, Paid-Anteil und Veröffentlichungsdaten sind unbekannt. Reihenfolge nach Themenrelevanz. „Neu“ bedeutet erstmals gefunden. Suchtreffer können alt, unvollständig oder nicht mehr erreichbar sein. Original prüfen. Die Ideen im Report sind feste redaktionelle Vorschläge und keine gemessenen Trends. Suchquelle: öffentliche Bing-RSS-Suche; Verfügbarkeit und Abdeckung nicht garantiert.

## Benutzung

GitHub → Actions → Daily Content Radar → Run workflow. Danach unter Artifacts den Report herunterladen und index.html öffnen. Alternativ lokal `python listening.py`.

`config.json` enthält Marken, Themen und Limits. Marken rotieren täglich, nicht alle Accounts werden täglich erfasst. Tests: `python -m unittest discover -s tests -v`.

## Mail aktivieren

Settings → Secrets and variables → Actions: diese Repository-Secrets setzen:

| Secret | Wert |
| --- | --- |
| SMTP_HOST | SMTP-Server des vorhandenen Mailanbieters |
| SMTP_PORT | STARTTLS-Port, normalerweise 587 |
| SMTP_USER | SMTP-Benutzername |
| SMTP_PASSWORD | App-Passwort oder SMTP-Passwort |
| MAIL_FROM | Freigegebene Absenderadresse |
| MAIL_TO | Empfängeradresse |

Keine Zugangsdaten in Chat, Dateien oder Issues eintragen. Repository ist öffentlich. Maildaten bleiben Secrets. Ohne vollständige Secrets wird nur ein Report erzeugt. Firmenkonten können SMTP sperren; dann muss eine freigegebene Versandmöglichkeit ergänzt werden. SMTP-Fehler lassen den Lauf fehlschlagen.

Täglich 06:17 UTC = 07:17 MEZ / 08:17 MESZ. GitHub kann Läufe verzögern und Zeitpläne nach 60 Tagen ohne Repository-Aktivität deaktivieren. In Actions wieder aktivieren. Reports liegen 30 Tage als Actions-Artefakte vor. Es wird keine öffentliche Website eingerichtet. Bereits berichtete Links werden im Actions-Cache gemerkt; Cache-Verlust kann Wiederholungen verursachen. Manuelle Läufe zählen ebenfalls als Berichtslauf, auch ohne Mail.

## Grenzen und Ausbau

Zuerst Trefferqualität über mehrere Tage prüfen. Echte Engagementdaten und eine Vergleichshistorie sind nötig, um „funktioniert gut“ zu beurteilen. Diese Version erfindet keine Kennzahlen oder Erfolgsgründe. Keine Plattform-Logins, keine Kopien fremder Bilder/Videos. Null Treffer bedeuten nicht, dass keine Beiträge veröffentlicht wurden.
