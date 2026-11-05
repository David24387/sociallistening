# EUROMASTER Content Radar

Tägliche Recherche bei beobachteten Automotive-Accounts auf Instagram und LinkedIn. Instagram nutzt Metas Business Discovery API. LinkedIn liest öffentliche Unternehmensseiten und erreichbare Einzelbeiträge ohne Login. Beide Wege haben im GitHub-Lauf echte Beiträge geliefert. Facebook wird auf Wunsch nicht weiter verfolgt. Keine kostenpflichtigen Daten- oder KI-Dienste.

## Einrichten und testen

[Repository-Secrets](https://github.com/David24387/sociallistening/settings/secrets/actions) → New repository secret:

| Name | Inhalt |
| --- | --- |
| META_ACCESS_TOKEN | Erfolgreich getesteter Facebook-Token mit instagram_basic, instagram_manage_insights, pages_read_engagement |
| INSTAGRAM_ACCOUNT_ID | 17841403696908375 |

Token niemals in Chat, Code oder Issues eintragen. Bei Ablauf oder Widerruf das Secret ersetzen. Alle Plattformzugriffe sind lesend. LinkedIn benötigt keine zusätzlichen Zugangsdaten.

[Daily Content Radar](https://github.com/David24387/sociallistening/actions/workflows/daily.yml) → Run workflow → main. Die Laufübersicht zeigt den Quellenstatus. Unter Artifacts → content-report-… die ZIP herunterladen und index.html öffnen. latest.json und diagnostics.json enthalten Daten bzw. Fehlerstatus. Ein komplett ausgefallener Instagram-Abruf lässt den Lauf fehlschlagen; Diagnoseartefakte werden trotzdem erzeugt.

## Was täglich passiert

1. Instagram: bis zu 50 aktuelle Beiträge je beobachtetem Account neu abrufen; aktuelle Zähler lesen.
2. LinkedIn: bis zu 8 öffentliche Unternehmensseiten auf aktuelle Beitragslinks prüfen. Nicht zuvor ausgelesene Links zuerst; anschließend bekannte aktuelle Beiträge zur Beobachtung ihres Wachstums. Maximal 18 Einzelbeiträge pro Lauf. Abrufplätze werden zwischen Publishing-Handles aufgeteilt; keine zufällige Rotation älterer Beiträge mehr.
3. Tagesauswahl auf beiden Kanälen: nur Beiträge, die höchstens 7 Tage alt sind. Erstmals berichtete Beiträge bevorzugen. Erstmals entdeckt bedeutet dabei nicht automatisch heute veröffentlicht und nicht automatisch erfolgreich.
4. Bereits generierte Reporteinträge werden gemerkt. An Folgetagen nur erneut aufnehmen, wenn seit dem letzten Report mindestens 50 zusätzliche Interaktionen UND mindestens 25 Prozent Wachstum vorliegen; mindestens 18 Stunden Abstand. Diese redaktionellen Schwellen sind kein statistischer Erfolgsnachweis.
5. Bis zu 12 Instagram- und 8 LinkedIn-Beiträge. Keine Auffüllung mit alten Wiederholungen: an ruhigen Tagen kann der Report kürzer oder leer sein. Manuelle Wiederholungsläufe am selben Kalendertag dürfen dieselben Beiträge zeigen.

Zeitplan: täglich 06:17 UTC = 07:17 MEZ / 08:17 MESZ. GitHub kann verzögern und Zeitpläne nach 60 Tagen ohne Repository-Aktivität deaktivieren. Dann in Actions wieder aktivieren. Der Job sucht innerhalb der konfigurierten Quellen; keine globale oder vollständige Plattformsuche.

## Erfolg einordnen

Interaktionen = Likes/Reaktionen + Kommentare. Fehlende Werte bleiben unbekannt. Original-Link, Caption, Format, Datum, Zähler und Auswertungsstatus stehen im Report. Reichweite, Saves, Shares, Paid-Anteil und Views werden nicht erfasst. Die Quote bezogen auf aktuelle Follower ist keine Reichweiten-Engagementrate.

Instagram: vorläufiger Medianvergleich mit mindestens 5 anderen Posts desselben Accounts und Formats, jeweils 3–90 Tage alt. Vergleichsfaktor nur für Kandidaten im Alter von 3–7 Tagen. Unterschiedliches Messalter und bezahlte Verbreitung sind nicht kontrolliert. Nach Vergleichsabruf ca. 24 Stunden später erscheinen Tagesveränderungen.

LinkedIn: mehrere Autoren werden abwechselnd berücksichtigt; innerhalb eines Accounts werden Automotive-Themen und danach sichtbare Interaktionen bevorzugt. Kein altersbereinigter Erfolgsbenchmark. Daten stammen aus öffentlichen JSON-LD-Metadaten zum exakten Beitrag. Einzelne Zähler können fehlen, unvollständig oder verzögert sein. Unternehmensseiten können Anmelde-/Prüfseiten liefern oder nur einen Ausschnitt zeigen. Keine Umgehung von Sperren, keine Cookies oder Proxys, keine garantierte tägliche Neuentdeckung. Nicht jeder neue Beitrag innerhalb des Tages wird zwingend erfasst.

Die Themenideen sind regelbasierte Hinweise aus Instagram-Captions und redaktionelle Vorschläge, keine KI-Bild-/Videoanalyse und keine bewiesenen Erfolgsursachen. Medien werden nicht kopiert, sondern im Original verlinkt.

## Quellen verwalten

config.json enthält instagram_accounts und linkedin.company_pages. Die Instagram-Handles aller 8 Quellen wurden im GitHub-Lauf bestätigt. Auch die sechs LinkedIn-Unternehmensseiten ADAC, ÖAMTC, Vergölst, ATU, Carglass und Ayvens lieferten im Test Beitragslinks; einzelne Postabrufe können fehlschlagen. linkedin.seed_posts sind ausdrücklich manuell recherchierte Startlinks, keine neu entdeckten Tagesfunde. Frisch aus Unternehmensseiten entdeckte Links haben Vorrang.

## E-Mail aktivieren

Zusätzlich diese Repository-Secrets hinterlegen:

| Secret | Inhalt |
| --- | --- |
| SMTP_HOST | Server des vorhandenen Mailanbieters |
| SMTP_PORT | STARTTLS-Port, normalerweise 587 |
| SMTP_USER | SMTP-Benutzername |
| SMTP_PASSWORD | App-Passwort/SMTP-Passwort |
| MAIL_FROM | Freigegebene Absenderadresse |
| MAIL_TO | Empfängeradresse |

Ohne vollständige SMTP-Secrets wird nur der Report erzeugt. Firmenkonten können SMTP sperren. Bei Versandfehlern bleibt der HTML-Report als Artifact erhalten; der Lauf ist fehlgeschlagen. Ein Wiederholungslauf kann erneut eine Mail senden.

## Speicherung und Grenzen

Berichtet bedeutet: HTML-Report generiert, nicht zwingend Mail erfolgreich zugestellt. Kennzahlen, bekannte Links und Reporthistorie liegen im Actions-Cache unter state/. Cache-Verlust kann Wiederholungen verursachen und Tagesvergleiche zurücksetzen. Nach der Einführung der Reporthistorie ist ein einmaliger Neustart der Wiedererkennung zu erwarten. Reports bleiben 30 Tage als Actions-Artefakte. Keine öffentliche Report-Website. Das Repository selbst ist öffentlich; Zugangsdaten werden nur aus Secrets gelesen und weder im Report noch im Verlauf gespeichert.

Python 3.12, Standardbibliothek. Lokal: META_ACCESS_TOKEN und INSTAGRAM_ACCOUNT_ID sicher als Umgebungsvariablen setzen, dann python radar.py, optional --send. Tests: python -m unittest discover -s tests -v. Tests verwenden synthetische Daten ohne Zugangsdaten. Neue Auswahlregeln sind getestet; ihre Wirkung im täglichen Livebetrieb muss über weitere Läufe beobachtet werden.
