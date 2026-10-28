# Demo in drie minuten

**0:00–0:30 — het probleem.** “Een fictief accountancyteam wil intakevragen sneller omzetten in opvolgcases. Het systeem mag nooit zelf een boeking doen. Deze demo gebruikt synthetische data en een lokale mock CRM.”

**0:30–1:15 — verzoek naar voorstel.** Start de API, maak een run aan in Swagger en gebruik `/drain`. Toon de drie toolresultaten, het opgeslagen voorstel en `waiting_approval`. Wijs op `crm_case_id: null`. Toon dat dezelfde requestkey geen tweede run maakt.

**1:15–2:00 — verantwoordelijkheid.** Probeer als requester goed te keuren en toon 403. Wissel naar de reviewerkey, lees het voorstel en keur goed met reden. Drain als operator. Toon het lokale case-ID en de auditvolgorde. Noem dat de case geen echt ERP-record is.

**2:00–2:40 — herstel.** Toon de restart-, backoff- en fencingtests en verklaar waarom een verlopen worker geen wijzigingen mag opslaan. Gebruik een foutieve klant om te tonen dat het systeem stopt.

**2:40–3:00 — eerlijke grenzen.** “De Azure-adapter is HTTP-contractgetest; ik claim geen live deployment. Voor een echt pilot voeg ik Entra ID, een sandboxconnector, data-afspraken, providertracing en een restoretest toe. Ik meet eerst reviewerkwaliteit en doorlooptijd.”

Offline alternatief: `python -m workflow_platform.cli` toont voorstel en voltooiing automatisch. Die CLI simuleert beide menselijke rollen en is daarom een technische walkthrough, geen bewijs van echte gebruikersadoptie.
