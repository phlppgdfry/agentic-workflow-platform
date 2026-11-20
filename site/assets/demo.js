// evidence/local-model-run.json: genuine local tool calling with qwen3:8b, synthetic records, mock CRM.
const $ = id => document.getElementById(id);
const run = await (await fetch('assets/run.json')).json();
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const j = o => `<pre class="aw-pre">${esc(JSON.stringify(o, null, 2))}</pre>`;
const p = run.proposal_state, f = run.final_state, t0 = run.events[0].at, u = p.plan.usage;
const ms = at => `+${((at - t0) * 1000).toFixed(0)} ms`;
const DETAIL = {
  run_created: () => `<h3>Request received</h3><p>A requester asks for a case. The planner mode is <b>ollama</b>: one bounded planning call to a model running on the laptop.</p>${j(p.request)}`,
  plan_validated: () => `<h3>Model plan, validated by code</h3><p><b>${u.model}</b> proposed ${p.plan.steps.length} tool calls in ${(u.latency_ms / 1000).toFixed(1)} s (${u.input_tokens} input, ${u.output_tokens} output tokens). The server checks tool names, argument schemas, customer scope and the three-step budget before anything runs.</p>${j(p.plan.steps)}`,
  tool_completed: e => { const r = p.tool_results[e.detail.step]; return `<h3>Tool: ${esc(r.tool)}</h3><p>A plain function, not an autonomous agent. Its result is checkpointed in SQLite.</p>${j(r.result)}`; },
  approval_requested: () => `<h3>Waiting for approval</h3><p>The proposal is immutable and <b>no CRM case exists yet</b> (<code>crm_case_id: null</code>). The requester cannot approve their own run.</p>${j({ status: p.status, crm_case_id: p.crm_case_id, proposal: p.tool_results[2].result.proposal })}`,
  approved: () => `<h3>Independent reviewer approves</h3><p>A different identity records the decision with a reason.</p>${j(f.decision)}`,
  case_created: () => `<h3>Delivered once to the mock CRM</h3><p>An approval-gated outbox writes the case idempotently to <b>local mock CRM tables</b>. No external system is touched.</p>${j({ status: f.status, crm_case_id: f.crm_case_id })}`,
};
function show(i) {
  document.querySelectorAll('#aw-tl li').forEach((li, k) => li.setAttribute('aria-current', k === i));
  const e = run.events[i]; $('aw-detail').innerHTML = DETAIL[e.kind](e);
}
$('aw-tl').innerHTML = run.events.map((e, i) => `<li tabindex="0" data-i="${i}"><span class="mono dim small">${ms(e.at)}</span><b>${e.kind.replaceAll('_', ' ')}</b><span class="dim small">${esc(e.actor)}</span></li>`).join('');
$('aw-tl').addEventListener('click', e => { const li = e.target.closest('li'); if (li) show(+li.dataset.i); });
$('aw-tl').addEventListener('keydown', e => { const li = e.target.closest('li'); if (li && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); show(+li.dataset.i); } });
show(1);
