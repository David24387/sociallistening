# EUROMASTER Content Radar

Täglicher Instagram-Report mit echten Kennzahlen über Meta Business Discovery. Keine kostenpflichtigen Daten- oder KI-Dienste. Der manuelle ADAC-Test über euromaster.de war erfolgreich; automatischer Abruf muss nach Einrichtung der Secrets separat geprüft werden.

## Jetzt verbinden

[Repository-Secrets öffnen](https://github.com/David24387/sociallistening/settings/secrets/actions) → **New repository secret**:

| Name | Inhalt |
| --- | --- |
| META_ACCESS_TOKEN | Zuletzt erfolgreich getesteter Facebook-Token mit instagram_basic, instagram_manage_insights und pages_read_engagement |
| INSTAGRAM_ACCOUNT_ID | 17841403696908375 |

Token niemals in Code, Issues oder Chat schreiben. Token können ablaufen oder widerrufen werden; dann das Secret ersetzen. Nur lesender Zugriff; keine Veröffentlichung von Beiträgen.

Danach [Actions](https://github.com/David24387/sociallistening/actions/workflows/daily.yml) → **Run workflow**. Laufübersicht zeigt Anzahl und Accountstatus. Unter **Artifacts → content-report-…** ZIP herunterladen und **index.html** öffnen. Bei vollständig fehlgeschlagenem Abruf ist der Lauf rot; HTML und Diagnose werden trotzdem hochgeladen.

## Inhalte und Bewertung

Original-Links, Captions, Account, Format, Datum, echte Likes und Kommentare. Bis zu 50 aktuelle Beiträge je Account, davon Auswahl aus den letzten 7 Tagen. Keine vollständige Pagination. Konten kommen abwechselnd in die Auswahl; große Accounts dominieren nicht allein durch absolute Likes.

Interaktionen = Likes + Kommentare. Fehlende Werte bleiben unbekannt. Vorläufiger Vergleichsfaktor nur bei mindestens 5 anderen Beiträgen desselben Accounts und Formats: Vergleichsposts sind 3–90 Tage alt, bewerteter Post 3–7 Tage. Unterschiedliches Messalter und Paid-Verbreitung bleiben mögliche Einflüsse. Kein kausaler Erfolgsnachweis, keine globale Branchenrangliste. Quote bezogen auf aktuelle Follower ist keine Engagementrate auf Basis der Reichweite. Views, Reichweite, Saves und Shares sind nicht erfasst.

Nach einem zweiten Abruf nach ca. 24 Stunden erscheinen Veränderungen der Interaktionen. Wiederholungen auffälliger Posts sind beabsichtigt. Themenhinweise werden regelbasiert aus den Captions abgeleitet; Ideen sind redaktionelle Vorschläge, keine bewiesenen Erfolgsursachen. Keine KI-Bild-/Videoanalyse. Medien werden nicht kopiert, sondern im Original verlinkt.

**Facebook und LinkedIn haben noch keine Performance-Datenquelle.** Diese Einschränkung steht auch im Report. Das frühere RSS-Skript listening.py bleibt erhalten, läuft aber nicht mehr im täglichen Workflow.

## Accounts

In config.json unter instagram_accounts. **Nur adac ist durch den manuellen Test bestätigt.** Die weiteren Handles sind Startkandidaten, keine verifizierte Accountliste: oeamtc, atu_de, vergoelst, michelin, continental_reifen, carglass_de, pitstop.de. Der erste Lauf prüft sie; ungültige, private, persönliche oder gesperrte Accounts erscheinen als Quellenfehler. Handles anhand der Originalprofile korrigieren oder entfernen. Keine Vollständigkeitsgarantie, API-Limits beachten.

## Mail

Zusätzlich Repository-Secrets setzen:

| Secret | Inhalt |
| --- | --- |
| SMTP_HOST | Server des vorhandenen Mailanbieters |
| SMTP_PORT | STARTTLS-Port, normalerweise 587 |
| SMTP_USER | SMTP-Benutzername |
| SMTP_PASSWORD | App-Passwort/SMTP-Passwort |
| MAIL_FROM | Freigegebene Absenderadresse |
| MAIL_TO | Empfängeradresse |

Ohne vollständige SMTP-Secrets wird nur der Report erzeugt. Firmenkonten können SMTP sperren. Bei Versandfehlern ist der Lauf rot, der Report bleibt als Artifact erhalten. Ein erneuter Lauf kann eine zweite Mail senden, wenn der Versand zuvor trotz späterem Fehler erfolgt war.

Täglich 06:17 UTC (07:17 MEZ / 08:17 MESZ). GitHub kann verzögern oder nach 60 Tagen ohne Repository-Aktivität deaktivieren; dann in Actions wieder aktivieren. Reports bleiben 30 Tage als Actions-Artefakte. Snapshots liegen im Actions-Cache; Cache-Verlust setzt den Tagesvergleich zurück. Repository ist öffentlich; Secrets werden nicht in Report oder Verlauf geschrieben. Es wird keine öffentliche Report-Website eingerichtet.

## Lokal und Tests

Python 3.12, Standardbibliothek. META_ACCESS_TOKEN und INSTAGRAM_ACCOUNT_ID sicher als Umgebungsvariablen setzen und `python radar.py` ausführen; mit `--send` für Mail. Tests: `python -m unittest discover -s tests -v`. Tests sind synthetisch und benötigen keinen Token. Live-End-to-End-Test steht bis zum Setzen der Secrets aus.

## LinkedIn: öffentlicher Testbetrieb

Facebook wird auf Wunsch nicht weiter angebunden. LinkedIn wird jetzt separat im täglichen Report versucht, ohne Entwickler-App, Passwort, Cookies oder kostenpflichtigen Dienst. Die erste öffentliche ADAC-Postseite enthielt nachweislich Datum, Caption, 48 Reaktionen und 0 Kommentare; das ist kein Erfolgsbenchmark. Der regelmäßige Abruf auf GitHub muss noch geprüft werden.

In config.json steht der Abschnitt linkedin: company_pages für automatische Entdeckung aus öffentlich ausgelieferten Unternehmensseiten, seed_posts für manuell recherchierte Startlinks. Maximal 4 Unternehmensseiten und 8 Einzelbeiträge je Lauf, keine Pagination, keine Umgehung von Login-/Prüfseiten oder Abrufsperren. Neu entdeckte Links werden bevorzugt und bekannte rotiert; bekannte Links liegen im Actions-Cache. Die Unternehmensseiten lieferten im lokalen Test Prüfseiten statt Beiträgen. Neue tägliche LinkedIn-Funde sind daher ausdrücklich nicht gesichert.

Öffentliche Beiträge werden über passende JSON-LD-Metadaten zur exakten Activity-ID ausgewertet; fehlende Zähler bleiben unbekannt. Quellenfehler sind im separaten Reportabschnitt und diagnostics.json sichtbar. LinkedIn zeigt maximal 6 erreichbare Posts aus 30 Tagen, nach absoluten Interaktionen sortiert; kein alters-/accountbereinigter Erfolgsvergleich. Der Instagram-Abschnitt bleibt davon getrennt. Die Themenideen beziehen sich derzeit weiterhin auf Instagram-Captions.
