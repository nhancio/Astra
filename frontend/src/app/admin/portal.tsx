"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { adminApi, type AdminUser, type Analytics, type Audit, type Campaign, type Config, type ConfigValues, type Count, type Flow, type Integrations, type Overview, type UserDetail } from "@/lib/admin";
import s from "./portal.module.css";

const sections = ["Overview", "Users", "Behavior", "Model routing", "Activity", "Campaigns", "Settings"] as const;
type Section = typeof sections[number];
const symbols = ["◈", "♙", "⌁", "⇄", "≋", "⚑", "⚙"];
const stages = ["preview", "onboarding", "ready", "active", "dormant", "paid"];
const models = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"];
const num = (value: number) => value.toLocaleString("en-IN");
const date = (value: string | null) => value ? new Date(value.includes("T") ? `${value}${/[Z+]/.test(value) ? "" : "Z"}` : `${value}T00:00:00Z`).toLocaleString("en-IN", { timeZone: "UTC", dateStyle: "medium", ...(value.includes("T") ? { timeStyle: "short" as const } : {}) }) : "—";
const label = (text: string) => text.replaceAll("_", " ");

function Empty({ children }: { children: React.ReactNode }) { return <p className={s.empty}>{children}</p>; }
function Pill({ children }: { children: React.ReactNode }) { return <span className={s.pill}>{children}</span>; }
function Breakdown({ title, items }: { title: string; items: Count[] }) {
  const max = Math.max(1, ...items.map(item => item.count));
  return <section className={s.card}><h2>{title}</h2>{items.length ? items.map(item => <div className={s.breakdown} key={item.label || "unknown"}>
    <div><span>{label(item.label || "Unknown")}</span><strong>{num(item.count)}</strong></div><div className={s.track}><i style={{ width: `${item.count / max * 100}%` }} /></div>
  </div>) : <Empty>No recorded activity yet.</Empty>}</section>;
}
function Chart({ data }: { data: Analytics["daily"] }) {
  const max = Math.max(1, ...data.map(item => item.queries));
  return <div><div className={s.chart} role="img" aria-label={`Daily queries: ${data.map(d => `${d.date}: ${d.queries}`).join(", ")}`}>
    {data.map(item => <div key={item.date} className={s.barColumn} title={`${item.date} · ${item.queries} queries · ${item.active_users} active users`}><i style={{ height: `${Math.max(item.queries ? 2 : 0, item.queries / max * 100)}%` }} /></div>)}
  </div><div className={s.chartLabels}><span>{date(data[0]?.date || null)}</span><span>Daily queries · UTC</span><span>{date(data.at(-1)?.date || null)}</span></div>
  <details className={s.chartData}><summary>View daily figures</summary><div className={s.tableWrap}><table><thead><tr><th>Date (UTC)</th><th>Queries</th><th>Active users</th></tr></thead><tbody>{data.map(d => <tr key={d.date}><td>{d.date}</td><td>{num(d.queries)}</td><td>{num(d.active_users)}</td></tr>)}</tbody></table></div></details></div>;
}

export default function AdminPortal() {
  // The admin credential exists only in memory and is cleared on sign-out or page reload.
  const [key, setKey] = useState("");
  const [inputKey, setInputKey] = useState("");
  const [section, setSection] = useState<Section>("Overview");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [draft, setDraft] = useState<ConfigValues | null>(null);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [integrations, setIntegrations] = useState<Integrations | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [stage, setStage] = useState("");
  const [plan, setPlan] = useState("");
  const [offset, setOffset] = useState(0);
  const [days, setDays] = useState(30);
  const [flows, setFlows] = useState<Flow[]>([]);
  const [flowStatus, setFlowStatus] = useState("");
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [detail, setDetail] = useState<UserDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const requestVersion = useRef(0);
  const dialog = useRef<HTMLDialogElement>(null);
  const detailVersion = useRef(0);
  const dirty = !!config && JSON.stringify(config.values) !== JSON.stringify(draft);

  const refresh = useCallback(async () => {
    if (!key) return;
    const version = ++requestVersion.current;
    setBusy(true); setError("");
    try {
      const api = <T,>(path: string) => adminApi<T>(key, path);
      if (section === "Overview" || section === "Behavior" || section === "Model routing") {
        const [o, a] = await Promise.all([api<Overview>("/api/admin/overview"), api<Analytics>(`/api/admin/analytics?days=${days}`)]);
        if (version !== requestVersion.current) return;
        setOverview(o); setAnalytics(a);
      }
      if (section === "Users") {
        const result = await api<{ items: AdminUser[]; total: number }>(`/api/admin/users?${new URLSearchParams({ q: search, ...(stage ? { stage } : {}), ...(plan ? { plan } : {}), limit: "25", offset: String(offset) })}`);
        if (version !== requestVersion.current) return;
        setUsers(result.items); setTotal(result.total);
      }
      if (section === "Model routing" || section === "Settings") {
        const [c, changes, services] = await Promise.all([api<Config>("/api/admin/config"), api<Audit[]>("/api/admin/audit"), api<Integrations>("/api/admin/integrations")]);
        if (version !== requestVersion.current) return;
        setConfig(c); setDraft(c.values); setAudit(changes); setIntegrations(services);
      }
      if (section === "Activity") {
        const result = await api<Flow[]>(`/api/admin/flows?limit=100&offset=${offset}${flowStatus ? `&status=${flowStatus}` : ""}`);
        if (version !== requestVersion.current) return;
        setFlows(result);
      }
      if (section === "Campaigns") {
        const result = await api<{ campaigns: Campaign[] }>("/api/brands/campaigns");
        if (version !== requestVersion.current) return;
        setCampaigns(result.campaigns);
      }
    } catch (err) { if (version === requestVersion.current) setError(err instanceof Error ? err.message : "Could not load data."); }
    finally { if (version === requestVersion.current) setBusy(false); }
  }, [key, section, days, search, stage, plan, offset, flowStatus]);

  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (dirty) event.preventDefault(); };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  useEffect(() => {
    if (detail) dialog.current?.showModal();
  }, [detail]);

  async function login(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const result = await adminApi<Overview>(inputKey.trim(), "/api/admin/overview");
      setOverview(result); setKey(inputKey.trim()); setInputKey("");
    } catch (err) { setError(err instanceof Error ? err.message : "Sign-in failed."); }
    finally { setBusy(false); }
  }
  function navigate(next: Section) {
    if (dirty && !window.confirm("Discard unsaved settings changes?")) return;
    setDraft(config?.values || null); setSection(next); setOffset(0); setError(""); setMessage("");
  }
  async function save() {
    if (!config || !draft) return;
    setSaving(true); setError(""); setMessage("");
    const values = Object.fromEntries(Object.entries(draft).filter(([k, value]) => value !== config.values[k as keyof ConfigValues]));
    try {
      const result = await adminApi<Config>(key, "/api/admin/config", { method: "PATCH", body: JSON.stringify({ revision: config.revision, values }) });
      setConfig(result); setDraft(result.values); setMessage("Saved. Changes apply to the next request across all instances.");
      setAudit(await adminApi<Audit[]>(key, "/api/admin/audit"));
    } catch (err) { setError(err instanceof Error ? err.message : "Save failed."); }
    finally { setSaving(false); }
  }
  async function openUser(id: number) {
    const version = ++detailVersion.current;
    try { const user = await adminApi<UserDetail>(key, `/api/admin/users/${id}`); if (version === detailVersion.current) setDetail(user); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not load user."); }
  }
  function closeDetail() { dialog.current?.close(); setDetail(null); }
  function signOut() {
    if (dirty && !window.confirm("Discard unsaved changes and sign out?")) return;
    requestVersion.current++; detailVersion.current++; setKey(""); setInputKey(""); setOverview(null); setAnalytics(null);
    setUsers([]); setDetail(null); setConfig(null); setDraft(null); setAudit([]); setFlows([]); setCampaigns([]); setIntegrations(null); setMessage(""); setError(""); setSection("Overview");
  }

  if (!key) return <main className={s.loginPage}><div className={s.loginBrand}><span className={s.logo}>✳</span><span>astra<span className={s.adminLabel}>ADMIN</span></span></div><div className={s.loginCard}>
    <span className={s.eyebrow}>THE OPERATIONS ROOM</span><h1>A little clarity.<br />A lot of control.</h1><p>Users, intelligence, and every moving part of Astra. All in one place.</p>
    <form onSubmit={login}><label htmlFor="admin-key">Admin access key</label><input id="admin-key" type="password" autoComplete="off" autoFocus value={inputKey} onChange={event => setInputKey(event.target.value)} required minLength={32} placeholder="Enter your private admin key" />
    {error && <p className={s.error} role="alert">{error}</p>}<button className={s.primary} disabled={busy}>{busy ? "Verifying access…" : "Open mission control  →"}</button></form>
    <small>Your key stays in this tab’s memory. Reloading signs you out.</small></div><footer className={s.loginFooter}>ASTRA AI <span>PRIVATE WORKSPACE · NHANCIO</span></footer></main>;

  const paid = overview?.stages.find(item => item.stage === "paid")?.count || 0;
  return <div className={s.shell}><aside className={s.sidebar}><a href="/" className={s.brand} aria-label="Astra admin home"><span className={s.logo}>✳</span><span>astra<span className={s.adminLabel}>ADMIN</span></span></a>
    <div className={s.workspace}><span className={s.workspaceIcon}>A</span><div>Astra AI<small>Operations workspace</small></div><span className={s.liveDot} /></div>
    <span className={s.navLabel}>WORKSPACE</span><nav aria-label="Admin navigation">{sections.map((item, i) => <button key={item} onClick={() => navigate(item)} className={section === item ? s.activeNav : ""} aria-current={section === item ? "page" : undefined}><span aria-hidden="true">{symbols[i]}</span>{item}{item === "Model routing" && <i aria-hidden="true">3</i>}</button>)}</nav>
    <div className={s.sidebarBottom}><p><span className={s.liveDot} />Protected admin session</p><button onClick={signOut}>Sign out <span>↗</span></button></div></aside>
    <div className={s.main}><header className={s.topbar}><span>Workspace <b>/</b> <strong>{section}</strong></span><span className={s.topbarRight}><span className={s.liveDot} /> Live backend data <span className={s.avatar}>A</span></span><button className={s.mobileSignOut} onClick={signOut}>Sign out ↗</button></header>
      <main className={s.content}><div className={s.heading}><div><span className={s.eyebrow}>ASTRA MISSION CONTROL</span><h1>{section === "Overview" ? "The big picture" : section === "Behavior" ? "Understand your users" : section === "Model routing" ? "The intelligence layer" : section === "Users" ? "People behind the messages" : section === "Activity" ? "Every signal, in view" : section === "Campaigns" ? "Your brand ecosystem" : "Make Astra yours"}</h1><p>{section === "Overview" ? "A pulse on your people, conversations, and intelligence." : section === "Users" ? "Follow each user from their first hello to their next milestone." : section === "Model routing" ? "Choose which model handles each part of the conversation." : section === "Settings" ? "Manage usage, access, and the services that keep Astra running." : "Measured activity from your app. Reporting boundaries use UTC."}</p></div><div className={s.headingActions}>{["Overview", "Behavior", "Model routing"].includes(section) && <select aria-label="Analytics period" value={days} onChange={e => { if (!dirty || window.confirm("Discard unsaved settings changes?")) setDays(Number(e.target.value)); }}><option value={7}>Last 7 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option></select>}<button className={s.secondary} onClick={() => { if (!dirty || window.confirm("Discard unsaved changes and reload?")) void refresh(); }} disabled={busy || saving}>{busy ? "Loading…" : "↻ Refresh"}</button></div></div>
      {error && <div className={s.error} role="alert">{error}</div>}{message && <div className={s.success} role="status">{message}</div>}
      {busy && <div className={s.loading} role="status">Fetching the latest from Astra…</div>}

      {section === "Overview" && overview && <><div className={s.metrics}>{[["Total users", num(overview.total_users), `${num(overview.new_users_24h)} joined in the last 24 hours`, "♙"], ["Queries today", num(overview.today_queries), `${num(overview.active_today)} active users today`, "↗"], ["Paid members", num(paid), "Current, unexpired subscriptions", "✧"], ["Delivery success", overview.success_percent === null ? "—" : `${overview.success_percent}%`, "Successful vs. failed flows · 24h", "✓"]].map(([name, value, note, icon]) => <div className={s.metric} key={name}><div>{name}<span>{icon}</span></div><strong>{value}</strong><small>{note}</small></div>)}</div>
        <div className={s.overviewGrid}><section className={s.card}><div className={s.cardTitle}><div><h2>Conversation pulse</h2><p>Daily queries and the people asking them</p></div><Pill>{days} days</Pill></div>{analytics && <Chart data={analytics.daily} />}</section><section className={`${s.card} ${s.stageCard}`}><div className={s.cardTitle}><div><h2>The user journey</h2><p>Current lifecycle distribution</p></div><span>↗</span></div>{stages.map((stageName, i) => { const count = overview.stages.find(item => item.stage === stageName)?.count || 0; return <button key={stageName} className={s.stageRow} onClick={() => { setStage(stageName); navigate("Users"); }}><span className={s.stageNumber}>0{i + 1}</span><div><span>{label(stageName)}</span><div className={s.track}><i style={{ width: `${count / Math.max(1, overview.total_users) * 100}%` }} /></div></div><strong>{num(count)}</strong></button>; })}<small>Active: used Astra in the last 7 UTC dates. Paid takes precedence.</small></section></div>
        <div className={s.threeGrid}>{analytics && <><Breakdown title="What people come for" items={analytics.intents.slice(0, 5)} /><Breakdown title="Connected apps" items={analytics.connectors} /><section className={`${s.card} ${s.callout}`}><span className={s.eyebrow}>INTELLIGENCE, YOUR WAY</span><h2>Right task.<br />Right model.</h2><p>One classifier. Two reply routes. A fallback when it matters.</p><button onClick={() => navigate("Model routing")}>Manage model routing <span>↗</span></button></section></>}</div></>}

      {section === "Users" && <section className={s.card}><form className={s.filters} onSubmit={e => { e.preventDefault(); setOffset(0); setSearch(q); }}><input aria-label="Search users by name or phone" placeholder="Search name or phone number…" value={q} onChange={e => setQ(e.target.value)} /><button className={s.secondary}>Search</button><select aria-label="Lifecycle stage" value={stage} onChange={e => { setStage(e.target.value); setOffset(0); }}><option value="">All stages</option>{stages.map(v => <option key={v} value={v}>{label(v)}</option>)}</select><select aria-label="Plan" value={plan} onChange={e => { setPlan(e.target.value); setOffset(0); }}><option value="">All plans</option>{["free", "pro", "max", "business"].map(v => <option key={v} value={v}>{label(v)}</option>)}</select></form><div className={s.tableWrap}><table><thead><tr><th>User</th><th>Stage</th><th>Plan</th><th>Today / total</th><th>Apps</th><th>Last active (UTC)</th></tr></thead><tbody>{users.map(user => <tr key={user.id}><td><button className={s.userButton} onClick={() => void openUser(user.id)}>{user.name || "Unnamed user"}<small>+{user.phone_number}</small></button></td><td><Pill>{label(user.stage)}</Pill></td><td>{label(user.plan_tier)}</td><td>{num(user.used_today)} <span className={s.muted}>/ {num(user.total_queries)}</span></td><td>{user.connected_apps}</td><td>{date(user.last_active)}</td></tr>)}</tbody></table></div>{!users.length && !busy && <Empty>No users match these filters.</Empty>}<div className={s.pagination}><span>{total ? `${offset + 1}–${Math.min(offset + 25, total)}` : "0"} of {num(total)} users</span><div><button className={s.secondary} disabled={!offset || busy} onClick={() => setOffset(offset - 25)}>← Previous</button><button className={s.secondary} disabled={offset + 25 >= total || busy} onClick={() => setOffset(offset + 25)}>Next →</button></div></div></section>}

      {section === "Behavior" && analytics && <><section className={s.card}><h2>Usage over time</h2><Chart data={analytics.daily} /></section><div className={s.twoGrid}><Breakdown title="User intents" items={analytics.intents} /><Breakdown title="Conversation emotions" items={analytics.emotions} /><Breakdown title="Connected apps · all time" items={analytics.connectors} /><Breakdown title="Action outcomes" items={analytics.tools} /></div><p className={s.footnote}>{analytics.telemetry_note}</p></>}

      {section === "Model routing" && draft && config && <><section className={s.routingIntro}><span>01 <b>Understand</b><small>Intent + emotion + action checks</small></span><i>→</i><span>02 <b>Choose a route</b><small>Simple task or complex reasoning</small></span><i>→</i><span>03 <b>Respond</b><small>10s complex-call limit · one retry</small></span></section><div className={s.threeGrid}>{([{ key: "json_model", title: "Classification", subtitle: "Read between the lines", copy: "Structured JSON for intent, emotion, crisis detection, and action decisions." }, { key: "fast_model", title: "Fast replies & fallback", subtitle: "Keep the conversation moving", copy: "Everyday tasks and quick answers. Also retries a failed or slow complex reply once." }, { key: "reply_model", title: "Complex replies", subtitle: "Give deeper work more room", copy: "Multi-step analysis, coding, financial math, resume rewriting, and cold outreach." }] as const).map((role, i) => <section className={s.card} key={role.key}><span className={s.routeNumber}>0{i + 1} / {role.title}</span><h2 className={s.routeTitle}>{role.subtitle}</h2><p>{role.copy}</p><label className={s.fieldLabel} htmlFor={role.key}>Assigned model</label><select id={role.key} className={s.modelSelect} disabled={busy || saving} value={draft[role.key]} onChange={e => setDraft({ ...draft, [role.key]: e.target.value })}>{models.map(model => <option value={model} key={model}>{model}</option>)}</select><div className={s.routeMeta}><span>Thinking</span><Pill>{draft[role.key].includes("lite") ? "Minimal" : "Low"}</Pill></div></section>)}</div><div className={s.savebar}><span>Revision {config.revision} · {dirty ? "Unsaved changes" : "Configuration is up to date"}</span><button className={s.primary} disabled={!dirty || saving || busy} onClick={() => void save()}>{saving ? "Saving…" : "Save routing"}</button></div><section className={s.card}><h2>Model performance</h2><p>Actual provider calls in the selected period. Average latency includes failed attempts.</p><div className={s.tableWrap}><table><thead><tr><th>Model</th><th>Route</th><th>Outcome</th><th>Calls</th><th>Avg. latency</th><th>Input / output tokens</th></tr></thead><tbody>{analytics?.models.map((m, i) => <tr key={i}><td className={s.mono}>{m.model}</td><td>{m.route}</td><td><Pill>{m.status}</Pill></td><td>{num(m.calls)}</td><td>{Math.round(m.latency_ms)} ms</td><td>{m.input_tokens === null ? "—" : num(m.input_tokens)} / {m.output_tokens === null ? "—" : num(m.output_tokens)}</td></tr>)}</tbody></table></div>{!analytics?.models.length && <Empty>No model calls recorded in this period yet.</Empty>}</section><p className={s.footnote}>{analytics?.telemetry_note} Total generation timeout: 20 seconds.</p></>}

      {section === "Activity" && <section className={s.card}><div className={s.cardTitle}><div><h2>Message flow</h2><p>Delivery and processing metadata. Message payloads stay private.</p></div><select aria-label="Flow status" value={flowStatus} onChange={e => { setFlowStatus(e.target.value); setOffset(0); }}><option value="">All outcomes</option>{["success", "error", "ignored"].map(v => <option value={v} key={v}>{v}</option>)}</select></div><div className={s.tableWrap}><table><thead><tr><th>Flow</th><th>Direction</th><th>Sender</th><th>Status</th><th>Time</th></tr></thead><tbody>{flows.map(flow => <tr key={flow.id}><td className={s.mono}>#{flow.id}</td><td>{flow.direction}</td><td>{flow.sender || "—"}</td><td><Pill>{flow.status}</Pill>{flow.has_error && <small className={s.muted}> · error recorded</small>}</td><td>{date(flow.created_at)}</td></tr>)}</tbody></table></div>{!flows.length && !busy && <Empty>No flows found.</Empty>}<div className={s.pagination}><span>Page {offset / 100 + 1}</span><div><button className={s.secondary} disabled={!offset || busy} onClick={() => setOffset(offset - 100)}>← Previous</button><button className={s.secondary} disabled={flows.length < 100 || busy} onClick={() => setOffset(offset + 100)}>Next →</button></div></div></section>}

      {section === "Campaigns" && <section className={s.card}><h2>Sponsored campaigns</h2><p>Wallet and engagement figures from Astra’s ad service. Amounts below are INR.</p><div className={s.tableWrap}><table><thead><tr><th>Brand</th><th>Status</th><th>Impressions</th><th>Clicks / CTR</th><th>Budget / spent</th></tr></thead><tbody>{campaigns.map(c => <tr key={c.id}><td><strong>{c.brand_name}</strong><small className={s.subtext}>{c.category}</small></td><td><Pill>{c.is_active ? "Active" : "Paused"}</Pill></td><td>{num(c.impressions)}</td><td>{num(c.clicks)} / {c.impressions ? (c.clicks / c.impressions * 100).toFixed(1) : "0"}%</td><td>₹{num((c.budget_paise || 0) / 100)} / ₹{num((c.spent_paise || 0) / 100)}</td></tr>)}</tbody></table></div>{!campaigns.length && !busy && <Empty>No sponsored campaigns yet.</Empty>}</section>}

      {section === "Settings" && draft && config && <><div className={s.twoGrid}><section className={s.card}><h2>Usage & access</h2><p>Daily message limits reset at the UTC day boundary.</p>{([{ key: "FREE_DAILY_LIMIT", title: "Free daily messages", max: 10000 }, { key: "PAID_DAILY_LIMIT", title: "Pro daily messages", max: 10000 }, { key: "MAX_DAILY_LIMIT", title: "Max / Business daily messages", max: 10000 }, { key: "SIGNUP_PREVIEW_MESSAGES", title: "Lifetime preview messages", max: 100 }] as const).map(field => <label className={s.settingRow} key={field.key}><span>{field.title}<small>0–{num(field.max)}</small></span><input type="number" disabled={busy || saving} min={0} max={field.max} step={1} value={draft[field.key]} onChange={e => setDraft({ ...draft, [field.key]: Number(e.target.value) })} /></label>)}<label className={s.settingRow}><span>Sponsored messages<small>Eligible free-tier replies only</small></span><input type="checkbox" disabled={busy || saving} checked={draft.ADS_ENABLED} onChange={e => setDraft({ ...draft, ADS_ENABLED: e.target.checked })} /></label></section><section className={s.card}><div className={s.cardTitle}><h2>Connected infrastructure</h2><Pill>{integrations?.environment || "Unknown"}</Pill></div>{Object.entries(integrations?.services || {}).map(([service, configured]) => <div key={service} className={s.settingRow}><span>{service}</span><Pill>{configured ? "Configured" : "Not configured"}</Pill></div>)}<p className={s.footnote}>{integrations?.note}</p><div className={s.tags}>{integrations?.configured_toolkits.map(toolkit => <Pill key={toolkit}>{toolkit}</Pill>)}</div><p className={s.footnote}>Subscription products and billing prices are managed in the payment provider. Credentials, webhook secrets, database URLs, CORS, and connector versions stay in server configuration.</p></section></div><div className={s.savebar}><span>Revision {config.revision} · {dirty ? "Unsaved changes" : "Configuration is up to date"}</span><button className={s.primary} disabled={!dirty || saving || busy} onClick={() => void save()}>{saving ? "Saving…" : "Save settings"}</button></div><section className={s.card}><h2>Change history</h2><p>Every saved operational change is recorded with its previous value.</p>{audit.length ? audit.map(item => <div className={s.auditRow} key={item.id}><div><Pill>{item.action}</Pill><small>{date(item.created_at)}</small></div>{Object.entries(item.changes).map(([name, values]) => <p className={s.mono} key={name}>{name}: {String(values.before)} → {String(values.after)}</p>)}</div>) : <Empty>No configuration changes yet.</Empty>}</section></>}
      <footer className={s.footer}><span>✳ ASTRA AI <b>Operations, with perspective.</b></span><span>{overview ? `Last snapshot ${date(overview.generated_at)}` : "Private admin workspace"}</span></footer>
    </main></div>
    <dialog ref={dialog} className={s.dialog} onCancel={() => setDetail(null)} onClick={e => { if (e.target === e.currentTarget) closeDetail(); }}>{detail && <div><div className={s.cardTitle}><div><span className={s.eyebrow}>USER #{detail.id}</span><h2>{detail.name || "Unnamed user"}</h2><p>+{detail.phone_number}</p></div><button className={s.secondary} autoFocus onClick={closeDetail} aria-label="Close user details">✕</button></div><div className={s.tags}><Pill>{detail.stage}</Pill><Pill>{detail.plan_tier}</Pill><Pill>{detail.preferred_language}</Pill></div><div className={s.detailFacts}><p>Joined<strong>{date(detail.created_at)}</strong></p><p>Setup step<strong>{detail.setup_step || "Not started"}</strong></p><p>Queries today / total<strong>{detail.used_today} / {detail.total_queries}</strong></p><p>Subscription expiry<strong>{date(detail.premium_expires_at)}</strong></p></div><h3>Interests</h3><p>{detail.interests.map(label).join(", ") || "No interests saved."}</p><h3>Connected apps</h3>{detail.connections.length ? detail.connections.map(c => <div className={s.settingRow} key={c.toolkit}><span>{c.toolkit}</span><Pill>{c.status}</Pill></div>) : <Empty>No connected apps.</Empty>}<h3>Recent activity</h3>{detail.events.length ? detail.events.map((e, i) => <p key={i}>{label(e.intent)} · {e.emotion || "—"}<small className={s.subtext}>{date(e.created_at)}</small></p>) : <Empty>No classification events recorded yet.</Empty>}<h3>Recent actions</h3>{detail.actions.length ? detail.actions.map((action, i) => <p key={i}>{action.toolkit} · {action.tool_slug} <Pill>{action.status}</Pill><small className={s.subtext}>{date(action.created_at)}</small></p>) : <Empty>No external actions recorded.</Empty>}<h3>Recent daily usage</h3>{detail.usage.length ? detail.usage.map(u => <div className={s.settingRow} key={u.date}><span>{date(u.date)}</span><strong>{u.query_count} queries</strong></div>) : <Empty>No usage recorded.</Empty>}</div>}</dialog>
  </div>;
}
