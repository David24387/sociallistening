# EUROMASTER Top-Performer Radar

Täglicher Report mit überdurchschnittlich starken Beiträgen und klar gekennzeichneten Ausreißern aus Instagram und öffentlich erreichbaren LinkedIn-Beiträgen. Gewöhnliche neue Beiträge werden nicht aufgenommen. Facebook ist auf Wunsch deaktiviert. Keine kostenpflichtigen Daten- oder KI-Dienste.

## Strenge Auswahl statt beliebiger Fundstücke

Alle Bedingungen müssen gleichzeitig erfüllt sein:

- Beitrag 24 Stunden bis 30 Tage alt; bis 7 Tage als aktuell, darüber als Best of 30 Tage gekennzeichnet.
- Vollständige sichtbare Interaktionen (Likes/Reaktionen + Kommentare), mindestens 50.
- Mindestens 5 andere Vergleichsposts desselben Accounts; Kandidat ausgeschlossen. Instagram: gleiches Format. LinkedIn: gleiches Format, wenn mindestens 5 Vergleichsposts vorliegen, sonst formatübergreifender öffentlicher Account-Ausschnitt mit ausdrücklicher Kennzeichnung.
- Stark im Accountvergleich: mindestens 1,5× Median dieser Vergleichsposts und mindestens das 80. Perzentil der Vergleichsstichprobe. Deutlicher Ausreißer: zusätzlich mindestens 2× Median, oberhalb von mindestens 90 % der Vergleichsposts und mindestens 100 Interaktionen. Vergleichsgruppen mit nur 5–7 Posts werden als kleinere Basis gekennzeichnet.
- Keine erkennbaren Gewinnspiele/Verlosungen und kein unbekanntes Format.
- Konkreter Euromaster-Transfer aus Caption oder Format ableitbar.

**Instagram:** Wenn genügend Historie existiert, werden Messungen im Alter von 48–72 Stunden verglichen. Andernfalls verwenden wir Gesamtinteraktionen von Vergleichsposts, die bei ihrer Messung mindestens ebenso alt waren wie der Kandidat und höchstens 90 Tage alt sind. Das ist ein konservativer Ersatz, kein exakt altersbereinigter Test. Vergleichsmodus, Stichprobengröße, Median, Faktor und Zähler des Kandidaten stehen bei jedem ausgewählten Post.

Die Regeln identifizieren redaktionell definierte Ausreißer, keinen statistisch bewiesenen oder kausalen Erfolg. Reichweite, Views, Saves, Shares, Paid-Einsatz und Conversion sind unbekannt. Öffentliche LinkedIn-Metadaten können verzögert oder unvollständig sein. Eine hohe Reaktionszahl kann auch Kritik widerspiegeln. Vor eigener Umsetzung das Original ansehen und Tonalität/Inhalt prüfen. Die Followerquote ist keine Reichweiten-Engagementrate.

**Kein belastbarer Vergleich = kein Eintrag.** Daher sind leere oder kurze Tagesreports ausdrücklich zulässig. Insbesondere LinkedIn baut erst eine Vergleichshistorie auf. Höchstens 5 Instagram- und 3 LinkedIn-Beiträge, maximal 2 je Account; kein Mindestkontingent pro Quelle. Die frühere Kombination 2–7 Tage / mindestens 8 Peers / 2× Median / oberste 10 % war zu restriktiv: im geprüften Lauf lagen 461 von 500 Instagram-Posts und alle 17 ausgelesenen LinkedIn-Posts außerhalb dieses Altersfensters. Das 30-Tage-Fenster erschließt brauchbare Best-of-Beispiele, ohne sie als neue Veröffentlichungen auszugeben. Bis zu 2 branchenfremde Beispiele im Instagram-Abschnitt, nur mit konkret ableitbarem Transfer.

## Branchenfremde Inspiration und Ideen

Neben den 8 bestätigten Automotive-Instagram-Accounts werden hornbach_de und ikeadeutschland versucht. Handles anhand offizieller Quellen recherchiert und im API-Lauf bestätigt. Beide zusätzlichen Inspirations-Accounts lieferten im nächsten GitHub-Lauf je 50 Posts. Neue Fehler stehen im Quellenstatus. Weitere Quellen können in config.json ergänzt werden.

Ein Transfer nennt das erkannte Muster und einen eigenen Euromaster-Ansatz, z.B. Fehler vermeiden → Reifenlagerung; Kosten erklären → Leistungsumfang des Reifenservices; Vorher/nachher → Autoglas-Auftrag. Regeln lesen Caption und Metadaten. Es gibt **keine automatische Bild-/Videoanalyse oder frei formulierende KI-Redaktion**. Bei branchenfremden Bildposts ohne erkennbares Muster erfolgt kein Eintrag. Bei qualifizierten Videos mit aussagekräftiger Caption kann ein vorläufiger Formattransfer vorgeschlagen werden; dieser ist ausdrücklich nicht als Sichtung oder Interpretation des Videos ausgegeben. Karussellstruktur ist ein Metadatenhinweis und kein Beleg für die konkrete Bilddramaturgie.

## Tägliche Erfassung

Instagram: bis zu 50 aktuelle Posts je Account über Meta Business Discovery, erneut bei jedem Lauf. LinkedIn: bis zu 8 öffentliche Unternehmensseiten täglich auf Beitragslinks prüfen, die zwei neuesten sichtbaren Links je Publishing-Handle bei jedem Lauf aktualisieren, danach weitere noch nicht untersuchte aktuelle Links und weitere bekannte Posts prüfen. So verdrängen ältere unbekannte Links nicht dauerhaft die aktuellen Posts. Maximal 18 Einzelabrufe je Lauf, zwischen Publishing-Handles verteilt. Keine globale oder vollständige Plattformsuche. Keine Umgehung von Login-/Prüfseiten, keine LinkedIn-Passwörter, Cookies oder Proxys. Einzelfehler bleiben sichtbar. Die 6 konfigurierten LinkedIn-Unternehmensseiten haben im GitHub-Lauf Beitragslinks geliefert, einzelne Posts können unzugänglich sein.

Bekannte LinkedIn-Postdaten werden für Vergleiche über mehrere Läufe aufbewahrt. Fehlende Vergleichsdaten werden nicht durch Rohzahlen oder allgemeine Branchenmediane ersetzt. Unterschiedliche Plattformen werden nicht miteinander verglichen.

Berichtete Posts werden normalerweise nicht täglich wiederholt. Erneute Aufnahme nur, wenn weiterhin alle Top-Performer-Regeln gelten UND seit dem letzten generierten Report mindestens 50 zusätzliche Interaktionen und 25 % Wachstum vorliegen, bei mindestens 18 Stunden Abstand. Gleichentägige manuelle Wiederholungsläufe dürfen dieselben Posts zeigen. Cache-Verlust kann Wiederholungen verursachen.

Zeitplan: täglich 06:17 UTC (07:17 MEZ / 08:17 MESZ). GitHub kann verzögern oder nach 60 Tagen ohne Repository-Aktivität deaktivieren. Dann in Actions wieder aktivieren.

## Zugang und Mail

[Repository-Secrets](https://github.com/David24387/sociallistening/settings/secrets/actions):

| Secret | Inhalt |
| --- | --- |
| META_ACCESS_TOKEN | Facebook-Token mit instagram_basic, instagram_manage_insights und pages_read_engagement |
| INSTAGRAM_ACCOUNT_ID | 17841403696908375 |
| SMTP_HOST | mail.gmx.net für den eingerichteten GMX-Versand |
| SMTP_PORT | 587 (STARTTLS) |
| SMTP_USER | Vollständige GMX-Absenderadresse |
| SMTP_PASSWORD | GMX-App-Passwort |
| MAIL_FROM | Dieselbe freigegebene GMX-Adresse |
| MAIL_TO | Empfängeradressen, durch Komma getrennt |

Mailversand über GMX an die Firmenadressen ist vom Nutzer als funktionierend bestätigt. Keine Zugangsdaten im Code, Chat oder Report speichern. Bei Ablauf/Widerruf eines Tokens Secret ersetzen. Ohne vollständige SMTP-Secrets entsteht nur der Report. Bei Versandfehlern bleibt das Artifact erhalten, der Lauf ist fehlgeschlagen. Wiederholungsläufe können erneut senden.

## Testen und Diagnose

[Actions](https://github.com/David24387/sociallistening/actions/workflows/daily.yml) → Run workflow → main. Laufübersicht zeigt Quellen und Anzahl qualifizierter Beiträge. Artifact content-report-… herunterladen, ZIP entpacken, index.html öffnen. latest.json enthält die ausgewählten Posts mit Nachweisen. diagnostics.json enthält Quellenstatus und Ausschlussgründe mit Anzahlen. Reports 30 Tage aufbewahrt, keine öffentliche Report-Website.

Python 3.12, Standardbibliothek; lokal python radar.py, optional --send, Zugangsdaten nur aus Umgebungsvariablen. Tests: python -m unittest discover -s tests -v. Auswahlregeln, echte Schwellenunterschiede, Altersfenster, Wiederholungen, Ausschluss gewöhnlicher Posts und Kennzeichnung älterer Beispiele werden synthetisch geprüft. Der nächste Live-Lauf muss die Trefferzahl nach der Anpassung bestätigen; es gibt keine garantierte Mindestzahl und keine Auffüllung mit durchschnittlichen Posts.

Kennzahlenhistorie, bekannte Links, LinkedIn-Vergleichsposts und Reporthistorie liegen im Actions-Cache unter state/. Reporthistorie bedeutet generiertes HTML, nicht garantiert erfolgreich zugestellte Mail. Cache-Verlust setzt Vergleiche und Wiedererkennung zurück. Das Repository selbst ist öffentlich, die Zugangsdaten bleiben Secrets.

## Mail als Tagesbriefing

Betreff: „Euromaster | Eure Content-Inspiration – Datum“. Instagram und LinkedIn erscheinen in einer gemeinsamen Liste, die stärksten Vergleichsfaktoren zuerst. Jede Karte zeigt Account/Plattform, Original-Einstieg, Datum und Best-of-Kennzeichnung, Likes/Reaktionen und Kommentare, einen kurzen verständlichen Vergleich und eine Euromaster-Idee samt Original-Link. Keine technischen Statuslisten, API-Begriffe oder „öffentlicher Testbetrieb“ im Mailtext. Grenzen der öffentlichen LinkedIn-Daten bleiben kurz im Fußbereich genannt; Details in diagnostics.json und im verlinkten GitHub-Lauf.

Layout: maximal 640 Pixel, einspaltige Tabellen mit Inline-Stilen und großer Schrift für E-Mail-Clients; zusätzlich vollständige Klartextversion. Es wird auch an Tagen ohne neue qualifizierte Treffer ein kurzes Tagesbriefing erzeugt und gesendet. Sind gar keine Beitragsdaten erreichbar, wird das ausdrücklich als Erfassungsstörung gekennzeichnet; bei vorhandener Mailkonfiguration wird dieser Statusbericht vor dem fehlerhaften Laufabschluss versendet. Das ist keine Zusage bei einem Ausfall von GitHub oder GMX selbst.

Der bestehende Zeitplan bleibt täglich 06:17 UTC, inklusive Wochenende (07:17 MEZ / 08:17 MESZ), an beide konfigurierten Firmenempfänger. Manuelle Testläufe senden zusätzlich. Alle Zugangsdaten und Auswahlregeln bleiben unverändert. Die neue MIME-Mail wurde mit zwei Empfängern, HTML und Klartext ohne echten Versand getestet; Darstellung in der tatsächlichen Firmen-Gmail nach dem nächsten Lauf prüfen.

## LinkedIn-Vergleichsbasis gezielt aufbauen

Im geprüften Lauf vom 05.11.2026 waren 5 Instagram- und 0 LinkedIn-Posts ausgewählt. Bei 14 von 17 gelesenen LinkedIn-Posts fehlten vergleichbare Posts; 3 lagen außerhalb des 30-Tage-Fensters. Die Mail hatte deshalb tatsächlich keine LinkedIn-Empfehlung.

Der Abruf liest nun bis zu 10 öffentliche Beitragslinks pro Unternehmensseite. Solange Quellen mit mindestens 5 bekannten Links weniger als 8 ausgelesene Postdatensätze mit Kennzahlen haben, wird ein größerer Abruf mit bis zu 60 Einzelposts versucht; danach bis zu 30. Das erweitert die reale Vergleichsbasis, nicht die Performance-Schwellen. Einmalige Startlinks erzwingen keinen dauerhaften Basisausbau. Weiterhin maximal 8 Unternehmensseiten, kein Umgehen von Zugangssperren. Workflow-Limit auf 30 Minuten erhöht, damit Timeouts einzelner Quellen den Basisaufbau nicht vorzeitig abbrechen.

Die Mail zeigt bei fehlenden LinkedIn-Empfehlungen jetzt kurz „LinkedIn heute“ mit der Anzahl geprüfter Posts. Fehlende Vergleichsdaten und nicht erreichbare Beitragsdaten werden unterschiedlich erklärt. Kein künstlicher LinkedIn-Mindestanteil. Der nächste Live-Lauf muss bestätigen, wie viele zusätzliche Postdaten erreichbar sind und ob Beiträge anschließend die unveränderten Qualitätsschwellen erfüllen.

## LinkedIn: Vergleichsregel an den öffentlichen Ausschnitt angepasst

Der erweiterte Lauf las 59 LinkedIn-Posts, aber die frühere Forderung nach mindestens 5 älteren Posts desselben Formats war bei ungefähr 10 sichtbaren Posts pro Unternehmensseite strukturell häufig unerfüllbar. Mehr Abrufe allein lösten das nicht.

Für LinkedIn wird jetzt ausschließlich eine Momentaufnahme des sichtbaren Profil-Ausschnitts bewertet: mindestens 5 andere Account-Posts mit Kennzahlen aus den letzten 90 Tagen, mindestens 1,5× Median, oberste 20 % des Ausschnitts und mindestens 50 Interaktionen. Wenn mindestens 5 Posts desselben Formats vorliegen, werden diese bevorzugt; sonst formatübergreifend mit ausdrücklichem Hinweis. Es erfolgt keine Altersbereinigung und keine Behauptung vollständiger Account-Analytics. Kandidaten weiterhin höchstens 30 Tage alt. Keine erzwungene Quote. Maximal ein LinkedIn-Post pro Account in einer Mail.

Nachrechnung der Kennzahlen aus dem echten 59-Post-Lauf ergab passende Kandidaten. Mit den tatsächlich gelesenen Original-Captions wurden ATU (4× Median), ADAC (3,69×) und ÖAMTC (2,55×) als 3 übertragbare Empfehlungen bis in die Mail-Vorlage geprüft. Das ist eine Nachrechnung desselben Snapshots, keine Bestätigung eines neuen automatischen Mailversands. Der nächste Live-Lauf nutzt die neue Regel.

Übertragungsregeln unterscheiden nun echte Team-/Karriereporträts, besondere Serviceleistungen und Auszeichnungen. Das Wort „Preis“ allein löst keine Kosten-/Sparidee mehr aus. Datenschutzkonferenzen und Finanz-/Strategieberichte werden nicht künstlich mit Automotive-Ideen versehen. Ideen bleiben Vorschläge aus Text und Format ohne automatische Bild-/Videoanalyse.

## Erweiterte Quellenabdeckung (06.11.2026)

Konfiguriert sind jetzt 16 Automotive-Instagram-Accounts und 3 branchenfremde Inspirationsaccounts sowie 16 LinkedIn-Unternehmensseiten. Neu auf Instagram: Bosch Car Service Deutschland, DEKRA Germany, GTÜ, Hankook Tire Europe, Premio, Pneuhage, BestDrive Österreich, ARBÖ und OBI als Inspiration. Neue LinkedIn-Seiten: Bosch Car Service Deutschland, Michelin, Continental, DEKRA Germany, TÜV SÜD, GTÜ, Pneuhage, Hankook Deutschland, OBI und HORNBACH Baumarkt. Profile anhand der Unternehmens-Websites oder öffentlich auffindbarer Unternehmensprofile recherchiert. Das ist eine Quellenkonfiguration, noch kein Beleg erfolgreicher Meta-Abrufe.

Die frühere Grenze von 8 LinkedIn-Seiten und 80 bekannten Beitragslinks ist durch konfigurierbare Grenzen ersetzt: maximal 24 Seiten und 240 bekannte Links. Täglich bis zu 80 Einzelposts, beim Aufbau der Vergleichsbasis bis zu 128, fair auf Publishing-Handles verteilt. Workflow-Zeitlimit 60 Minuten. Qualitätsfilter, Reportlänge und bestehender Versandzeitplan bleiben gleich. Die tatsächliche Erreichbarkeit jeder neuen Quelle muss der nächste Lauf bestätigen; Zugangssperren werden nicht umgangen.
