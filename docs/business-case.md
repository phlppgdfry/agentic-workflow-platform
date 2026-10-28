# Business case — synthetic accounting intake

## Process and problem

A fictional accounting team receives repetitive intake questions. Today a colleague checks the customer, finds policy, drafts a follow-up and creates a CRM case. The risk is losing context, duplicating work or taking action before somebody checks the proposed output. This reference automates the read/proposal stages and keeps accountable human approval.

The proposed pilot covers one narrow process and synthetic data. It does not post accounting entries, determine tax treatment, make credit decisions or send customer communications.

## Hypothesis, not measured savings

Assume 200 requests per week, six manual minutes per request, three minutes of assisted human review and €45/hour fully loaded staff cost. Gross potential capacity released is `200 × (6−3) / 60 = 10 hours/week`, valued at `10 × €45 = €450/week`. If weekly operating/review overhead were €150, hypothetical net capacity value is €300/week. A hypothetical €6,000 build effort would then have a 20-week simple payback.

These inputs are assumptions, not Titeca data, a price quote, measured savings or a claim that staff cost disappears. Measure real baseline handling times, rework, adoption and cloud costs before making an investment decision. If review takes five minutes rather than three, gross capacity becomes 3.33 hours/week (€150) and the assumed net benefit becomes zero.

## Pilot success criteria

- Process owner agrees on allowed data and one action type.
- Zero actions before independent approval; zero cross-tenant access in the tested routes.
- Reviewer can inspect customer and policy evidence with the exact proposal.
- At least 50 representative, approved synthetic scenarios are evaluated before moving to controlled real data.
- Measure median/p95 end-to-end lead time separately from active reviewer time.
- Measure correct routing, unsupported proposal rate, rework rate, duplicate actions and user adoption.
- Compare with a deterministic form/rules implementation. Use an LLM only if variable language improves outcomes enough to justify added cost and risk.

The current automated suite verifies technical boundaries and recovery, not accounting quality or organizational adoption. The baseline fixture planner is useful for testing the workflow independently of model variability.

## Adoption plan

Workshop with intake staff to map decisions; name a process owner and reviewers; agree a rejection/escalation path; run a supervised synthetic demo; gather feedback on proposal readability; pilot with a restricted volunteer group only after security/data review; keep a manual process available. Train colleagues to check evidence and report suspicious or wrong proposals. Review exceptions weekly and publish measured results, including failures.
