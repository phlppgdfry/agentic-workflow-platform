# Leer- en eigenaarschapstoets

**Status kandidaat: nog niet getoetst.** Deze code is met AI-hulp gemaakt. Een werkende repo bewijst niet vanzelf dat je de architectuur beheerst.

## Begrippen in deze code

Een **agentic workflow** gebruikt een model om een actievoorstel te kiezen, maar bewaakt uitvoering met applicatieregels. Hier maakt het model één begrensd plan; fixture mode is een deterministisch alternatief. De engine voert daarna vaste, gecontroleerde stappen uit. Dit is geen autonoom multi-agent systeem.

Een **checkpoint** bewaart voortgang na een stap, zodat een herstart niet opnieuw van nul begint. De `cursor` en het toolresultaat committen samen. Een **lease** kent tijdelijk één worker eigenaarschap toe; het **fencing token** voorkomt dat een oude worker alsnog schrijft nadat een nieuwe worker het werk overnam.

**Idempotency** betekent dat een herhaalde opdracht niet onbedoeld een tweede resultaat oplevert. Een requestkey met payloadhash voorkomt dubbel aanmaken. Unieke sleutels en een transactie voorkomen dubbele lokale CRM-cases. Dat garandeert nog geen eenmalige verwerking door een externe netwerk-API.

Een **outbox** bewaart een goedgekeurde actie als verzendopdracht. Hier zitten outbox en mock CRM in dezelfde database. Bij een echte CRM-connector moet je ook onzekere netwerkuitkomsten, idempotency van de bestemming en reconciliatie oplossen.

**Human-in-the-loop** is hier een afdwingbare autorisatiegrens: een andere subject met approverrol beslist. Een modeltekst “approved” of een requestveld `roles` geeft geen rechten. **Prompt injection** bestrijd je niet alleen met een systeemprompt; de toolallowlist, scopes en goedkeuringsgrens begrenzen wat een misleid model technisch kan doen.

## Zelf doen: uitleggen, aanpassen, diagnosticeren

1. Leg zonder AI uit welke tabellen veranderen tussen `running`, `waiting_approval`, `approved` en `completed`. Teken de transacties.
2. Zoek de code die een self-approval tegenhoudt. Verwijder die in een tijdelijke branch, toon welke test faalt en herstel de controle.
3. Voeg een read-only `lookup_contract`-stap toe. Pas schemas, planbudget, receipts, policyvoorwaarden en tests aan. Leg uit waarom je niet alleen een toolnaam toevoegt.
4. Simuleer een crash na het modelantwoord maar vóór de checkpointcommit. Waarom kan de planning opnieuw plaatsvinden, en waarom mag een tool hier geen externe write doen?
5. Verander de leaseklok in de fencingtest en toon dat een oude worker niet kan checkpointen.
6. Bouw een HTTP-mock met timeout na een mogelijke remote write. Ontwerp een reconciliatiepad vóór je een echte CRM-connector toevoegt.
7. Geef een kwaadaardige modeltoolcall met een ander klantnummer. Toon de falende run en verklaar de grens die ingrijpt.
8. Leg uit welke semantische fouten de technische tests niet detecteren. Ontwerp tien gelabelde beoordelingscases met een menselijke rubric.
9. Leg de businesscase uit met reviewtijd van drie én vijf minuten. Welke aannames moet je eerst meten?
10. Geef een demo van drie minuten en beantwoord waarom een gewoon formulier hier soms beter kan zijn dan een LLM.

## Bewijslog om zelf in te vullen

| Onderdeel | Uitleg zonder AI | Zelf aangepast | Fout zelf gevonden | Datum/bewijs |
|---|---|---|---|---|
| State + transacties | Niet getoetst | Niet getoetst | Niet getoetst | — |
| Tools + scopes | Niet getoetst | Niet getoetst | Niet getoetst | — |
| Approvals + tenant | Niet getoetst | Niet getoetst | Niet getoetst | — |
| Lease + recovery | Niet getoetst | Niet getoetst | Niet getoetst | — |
| Azure adapter | Niet getoetst | Niet getoetst | Niet getoetst | — |

Gebruik in je cv voorlopig: “AI-assisted portfolio reference implementation met synthetische data”. Claim pas zelfstandige beheersing na de oefeningen; claim geen live Azure- of klantervaring op basis van HTTP-mocks.
