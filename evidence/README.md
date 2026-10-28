# Verificatie

Lokaal op 28 oktober 2026: 25 pytest-tests geslaagd, vastgelegd in `tests.xml` en eerdere `pytest.txt`. De CLI-demo staat in `cli-demo.txt`. Herstart, idempotency, retries, leases/fencing, rollen, tenantgrenzen, verboden tools en Azure-responsecontracten zijn getest.

Docker-image werkelijk gebouwd; verpakte app gecontroleerd met synthetische serverprincipals; standaard Uvicorn-CMD geïsoleerd gestart en health=200. Zie `container-smoke.txt` en `container-runtime.txt`. Zonder vereiste principalconfiguratie start de workflow-API bewust niet.

Geen live Azure, echte CRM-write, Microsoft-tenantpublicatie of productielastmeting. Eén upstream TestClient-deprecationwarning. GitHub Actions bewaart eigen remote resultaten.
