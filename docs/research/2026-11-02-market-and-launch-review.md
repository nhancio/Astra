# Astra: market research, business-plan review, and launch simulation

Research date: **2 November 2026**. Geography: India first; global founder-marketing alternatives included. This compares the current WhatsApp personal assistant with the proposed founder-marketing agent, following the founder's instruction to compare both.

## Decision

**Validate a narrow founder-marketing service before committing to a full pivot. Do not fund a broad consumer launch or an advertising network yet.**

The assistant can attract curiosity, but its combination of free substitutes, small subscriptions, integration trust, free-user costs, and channel dependence makes profitable distribution difficult. The marketing direction has more room to charge for a useful result. However, its proposed headline capability is already offered by Google Pomelli, Predis, Canva, and Jasper. A successful Astra must own a particular customer's repeat workflow and improve the result enough to justify switching.

Recommended first customer hypothesis: **Indian bootstrapped B2B software founders who already have a product and paying customers, publish on LinkedIn, and personally assemble their weekly marketing.** Start with one campaign type, one brand, and two channels: LinkedIn and email. This is a research recommendation, not demonstrated product-market fit.

Suggested offer to test: **“Turn your shipped feature into a week of approved LinkedIn and email content, using your actual product screenshots and brand.”** Sell a paid pilot, deliver it with existing tools, and measure whether the founder publishes and returns. Treat advanced generated video as a separately priced option.

## What was actually reviewed

Local sources reviewed:

- `LAUNCH_PLAN.md`: the October 30 evaluation, job-outreach proposal, channel decisions, and forecast criticisms.
- `docs/product/2026-10-30-marketing-agent-reshape.md`: proposed brief-to-campaign marketing product.
- Current `frontend/src/app/page.tsx`, FAQ, onboarding/account components, and `backend/app/config.py`.
- Backend task prompts, WhatsApp action wiring, tool-run approval service, ad service, and hardening/verification reports.
- `README.md`, `context.md`, `READINESS.md`, and social strategy documents, which disagree on the product's purpose.

The original workbook **`Astra_AI_Business_Plan_Financial_Model.xlsx` is referenced by the old plan but was not found** in the project, relevant local file searches, or connected searches. No business-plan Page was identified. Therefore this is a review of the accessible plans and current commercial implementation, **not an audit of that workbook's formulas or every in-app business-plan screen**. The live Astra URLs could not be read through the research browser. No production customer, revenue, retention, advertising contract, or provider-billing export was available; none is invented here.

Source inspection establishes intended behavior, not a fresh end-to-end production test. Existing tests and security improvements do not establish live onboarding, delivery, payment, or retention.

## Business-plan corrections

| Finding | Evidence and business implication |
|---|---|
| Current plans differ from the earlier review | Homepage and backend defaults agree on Free **5/day**, Pro **₹99, 10/day**, Business **₹299, 30/day**. The earlier critique of 1,000 paid replies/day is no longer an accurate description of current defaults. Environment overrides and production behavior remain unverified. |
| “Business” currently sells volume | The shown Business plan adds a larger message allowance. It does not establish team features, approval roles, an SLA, or a business outcome. Rename or substantiate the promise in a future product decision. |
| Paid caps still do not guarantee profit | The config comment assumes roughly ₹0.30/reply. At full Pro usage, 300 replies cost ₹90 before support, free-tier subsidy, acquisition, and fixed costs. That is greater than modeled net receipts after fee/refund/tax allowances. Measure costs rather than relying on the comment. |
| Ad inventory is not advertiser demand | The ad service seeds named-brand campaigns, rupee CPMs, and ₹5,000 wallet budgets. These are code fixtures/default records, not proof of brand authorization, funded campaigns, receivables, or collected cash. Put zero advertising revenue in the base forecast. |
| Product direction is unresolved | Documentation describes a personal assistant, NanoClaw launcher, review-management SaaS, job agent, and marketing agent. Customers need one main promise, buyer, activation event, and pricing unit. |
| Current action scope is narrower than the connector grid | WhatsApp action handling supports specific Gmail, Calendar, Todoist, and Google Tasks actions with approval. Other task prompts often return drafts. A connector listed on a landing page is not evidence of a reliable autonomous workflow. |
| Marketing is a proposal | The marketing brief explicitly says media execution, jobs, assets, versions, metering, and campaign storage still need implementation. Model its build cost and launch delay separately. |
| Previous competitor claims have aged | Poke's official docs now say worldwide availability and list WhatsApp, RCS, Telegram, and Apple Messages. Backdoor's retrieved homepage currently displays plans from **$1.10/day**, not the older ₹20/day assertion. Neither website establishes Astra's eligibility or local checkout price. [Poke docs](https://poke.com/docs), [Backdoor](https://backdoorai.app/). |

Keep the useful assets: the Astra brand, phone-friendly intake, UPI checkout, specific approved actions, connector ownership controls, and conversational refinement. Do not treat already-built features as reasons to pursue a weak revenue model.

## What market evidence says

India is willing to spend on digital products, but large reach does not ensure monetization. Sensor Tower reports H1 2026 Indian app downloads up 3% year over year and IAP revenue up 34%. It also reports a large acquisition effect from Airtel's free Perplexity bundle. These are estimated app-store figures, excluding advertising and non-store payments; they do not directly estimate Astra's UPI demand. The implication is to find an audience with a concrete paid need rather than multiply India's WhatsApp population by an assumed penetration rate. [Sensor Tower, October 2026](https://sensortower.com/blog/indias-new-growth-playbook-2026).

Retention is a major uncertainty. RevenueCat's August 2026 study covers 3,519 AI apps. First monthly renewals were 57.9% in its high-retention group and 30.2% in its low-retention group. The often-repeated **6.1% figure means retention after a year for monthly subscriptions**, not one-month retention or day-30 product usage. This is a global mobile subscription sample, not an India B2B benchmark. It motivates the first-renewal stress test below; it does not calibrate Astra's conversion or churn. [RevenueCat study](https://www.revenuecat.com/blog/growth/ai-app-retention-study).

## Competitive landscape: personal assistant

Prices and capabilities below are public vendor claims, checked during this research. No paid competitor trials were performed. No funding or user-count claim is used as verified traction.

| Alternative | Verified public offer | Why a customer chooses it | What Astra would have to prove |
|---|---|---|---|
| Meta AI | AI available in WhatsApp and other Meta surfaces. | Familiar distribution and general assistance without adding Astra. | A repeat task completed better than the customer's existing assistant. [Meta](https://about.fb.com/news/2025/04/introducing-meta-ai-app-new-way-access-ai-assistant/) |
| Puch AI | Official About page describes a free WhatsApp launch; current site emphasizes Indian languages, voice, images, and video. | Indian-language access and low adoption friction. | Language support and WhatsApp access alone are insufficient differentiation. [Puch](https://puch.ai/), [About](https://puch.ai/about) |
| Poke | Free; Pro **$19/month**; Ultra **$199/month**, as displayed. Email/calendar, reminders, connected apps, and background automations. | Established execution-oriented assistant with integrations. | Reliability and useful local workflows, not a similar landing page. [Pricing](https://poke.com/pricing), [docs](https://poke.com/docs) |
| Instinct | Text/call assistant that uses a phone/computer for errands. No public price observed on the official homepage. | Delegating real-world errands and administration. | Demonstrated execution with transparent limitations. Do not compare against an invented Instinct subscription price. [Instinct](https://instinct.com/) |
| Backdoor | Dedicated startup job outreach: matching, Gmail drafts/sending with approval, follow-ups and reply tracking; homepage says from **$1.10/day**. | A specific valuable job-search outcome. | A distinct segment and better interview results if Astra chooses a job wedge. [Backdoor](https://backdoorai.app/) |
| Existing ChatGPT/Gemini workflow | Established general AI products are substitutes for drafting and planning; local paid promotions and bundle eligibility vary. | Existing habit, broad capability, and familiarity. | Material time saved after signup, connection, approval, and correction—not just answer quality. No region-specific price is assumed here. |

**Likely market reaction, inferred:** many visitors will understand “AI on WhatsApp” immediately, try a few prompts, then compare it with an assistant they already use. More committed users will ask whether it actually sends, schedules, and remembers reliably. Permissions and uncertain execution can reduce activation; small limits can constrain the very users most likely to form a habit. A low price helps checkout only after value is clear.

This is a hypothesis about customer behavior, not measured sentiment from an Astra survey. It should be tested with observed task completion and renewal, not agreement in interviews.

## Competitive landscape: founder marketing

| Alternative | Public commercial reference | Competitive advantage | Implication for Astra |
|---|---|---|---|
| Google Pomelli | Google describes a **free** Labs tool: website-derived brand context, campaign ideas/assets, plus product-photo generation/editing. Current India availability was not independently established. | Almost the same entry promise as Astra's proposed URL-to-brand-to-campaign flow. | “Understands your brand from a URL” is already available; win on a workflow, controllability, and published output. [Launch](https://blog.google/innovation-and-ai/models-and-research/google-labs/pomelli/), [Photoshoot](https://blog.google/innovation-and-ai/models-and-research/google-labs/pomelli-photoshoot/) |
| Predis | Retrieved default annual offers: Core **$230/year**, Rise **$474/year**, Enterprise+ **$2,540/year**. The page also shows monthly/discount reference prices; verify checkout. Credits, social creatives/video, competitor tools, scheduling/approval features depending on plan. | Broad creative-production and distribution workflow. | Competing on a list of images, videos, and captions will be difficult. [Pricing](https://predis.ai/pricing/) |
| Canva | Free; retrieved USD pricing: Pro **$144/year/person**, Business **$250/year/person**. AI allowances/add-ons vary. India checkout was not verified. | Editing, reusable brand assets, collaboration, familiar production environment. | Editable exports and revisions matter. A pretty initial generation is a weak switching reason. [Pricing](https://www.canva.com/pricing/) |
| Jasper | Pro **$69/seat/month**, or **$59/month billed annually**; Business custom. Brand context and marketing workflows. | Established brand-governed content creation. | Target a narrower founder workflow rather than enterprise governance breadth. [Pricing](https://www.jasper.ai/pricing) |
| AdCreative.ai | Retrieved Starter shows **$39/month**, 20 credits, one brand; lower displayed prices require quarterly/annual billing. | Ad assets, product imagery/video, integrations and creative analysis. Performance claims are vendor claims. | Do not promise conversion uplift without Astra-controlled experiments. [Official site/pricing section](https://www.adcreative.ai/) |
| Founder + existing tools / freelancer | No universal price; obtain quotes from the chosen segment. | Familiar judgment, editing control, and someone responsible for finishing. | The main competitor can be the current process. Measure total time and rework, not generations per minute. |

A small review sample supports a useful product distinction: **generation speed and usable final output are different things**. G2's retrieved Predis page contains praise for time savings and complaints about editing; an October 7 review specifically describes incorrect product-name pronunciation and limited audio editing. This is anecdotal, selected feedback, not evidence of how common those failures are. Test revisions, brand fidelity, and correction cost directly. [G2 review page](https://www.g2.com/products/predis-ai/reviews).

**Likely market reaction, inferred:** founders will try a URL-to-campaign demo, then compare the exports with Canva, Pomelli, or their existing AI setup. They will pay if the result reflects their actual product, requires little correction, and gets published. They may cancel after a launch unless Astra also solves a weekly task. More sophisticated teams will demand editable files and control; founders with no customers may have little budget or usable source material.

## Where differentiation could hold

Start with one repeatable package: **one shipped feature → three LinkedIn posts, one email, and three screenshot-led visuals**, all grounded in supplied product facts. Include a brand fact sheet, approval, one defined revision round, and editable/downloadable outputs.

The potential advantage is the accumulated approved context: actual features, customer language, founder voice, corrections, accepted assets, and performance feedback. Context becomes valuable when it measurably improves subsequent work. Storage alone is not a moat; customers must prefer Astra's next campaign to a competent alternative using the same brief.

Local payment and relevant Indian-language variants may improve adoption, but each requires user evidence. Do not enter SaaS founders, D2C sellers, agencies, and local shops simultaneously: their channels, content needs, budgets, and approval processes differ.

Avoid “autonomous growth,” guaranteed leads, unlimited video, and large connector counts as the launch promise. The defensible initial metric is **time to an approved, published campaign**. Revenue attribution comes later through tagged links and controlled tests.

## Platform and cost risks

**Eligibility is unresolved, not assumed.** The European Commission documents Meta's exclusion of third-party general assistants and subsequent EU interventions. That establishes a material access risk; it does not establish a current Indian exemption or Astra's classification. The primary WhatsApp legal page redirected to a login wall during research. Obtain a provider determination for the actual use case and countries before committing distribution spend. A specialized product name alone does not establish compliance. [Commission April statement](https://europa.eu/newsroom/ecpc-failover/pdf/ip-26-805_en.pdf), [Commission June announcement](https://germany.representation.ec.europa.eu/nachrichten-und-veranstaltungen/pressemitteilungen/ki-assistenten-bei-whatsapp-kommission-verhangt-einstweilige-massnahmen-gegen-meta-2026-06-10_de).

**Pricing evidence conflicts.** Meta's accessible public pricing page says service replies within the customer window are free. Recent Indian reporting says service messages beyond an allowance are charged from October 1, 2026. The detailed developer page was login-gated, so an exact applicable India rate was not reconciled. The model therefore uses **₹0.05 / ₹0.15 / ₹0.30 all-in reply-cost sensitivity**, not a purported verified tariff. Marketing templates, outbound notifications, BSP fees, AI execution, and tax may have different treatment. Check actual WhatsApp Manager rate cards and invoices. [Meta public pricing](https://business.whatsapp.com/products/platform-pricing), [Moneycontrol October report](https://www.moneycontrol.com/technology/whatsapp-business-platform-pricing-changes-from-october-1-here-s-what-businesses-need-to-know-article-14042527.html).

Marketing's web workspace can reduce dependency on messaging eligibility. Messaging may remain useful for intake and approvals if approved; RCS/iMessage are separate integrations and approvals, not instantaneous substitutes.

Generation expenses depend on model, reasoning, grounding, resolution, attempts, and revisions. Google's API pricing explicitly charges several of those separately. Do not extrapolate from a short text response to a multi-step agent or a finished campaign. The **₹500 marketing delivery budget below is an assumption to validate with job-level invoices**. [Google API pricing](https://ai.google.dev/gemini-api/docs/pricing).

The model reserves **3% of gross collections for processing**, rather than asserting a particular merchant rate. Razorpay's retrieved pricing contains promotions and payment-specific rates. Confirm Astra's contract and recurring-payment fees. The **18% tax allowance is a modeling assumption**, not a determination of registration, tax liability, input credits, or accounting treatment. [Razorpay pricing](https://razorpay.com/pricing/).

## Unit economics

All calculations use 30-day months. Illustrative net receipts reserve 3% refunds, assume displayed prices include the 18% tax allowance, and deduct a further 3% processing allowance on original gross collections. Provider taxes/input credits are not separately modeled; delivery inputs must eventually be entered on a consistent basis.

`Net available = price × (0.97 / 1.18 − 0.03)`

| Plan | Gross price | Modeled net available | Replies at current full cap | Delivery at ₹0.15/reply | Delivery at ₹0.30/reply |
|---|---:|---:|---:|---:|---:|
| Pro | ₹99 | ₹78.41 | 300 | ₹45 | ₹90 |
| Business | ₹299 | ₹236.82 | 900 | ₹135 | ₹270 |
| Free | ₹0 | ₹0 | 150 | ₹22.50 | ₹45 |

These delivery columns exclude support, acquisition, and fixed overhead. Ten extra daily replies are not inherently profitable just because a cap exists. At ₹0.30/reply, both paid plans lose contribution at full usage before those other costs.

Advertising cannot be assumed to fix this. For a hypothetical ₹80 collected CPM, 20% ad opportunity rate and 30% paid fill, advertising earns **₹0.0048 per assistant reply**. A user consuming 150 replies produces ₹0.72 ad revenue against ₹22.50 delivery at ₹0.15/reply. Required CPM just to cover that delivery at the same density/fill is **₹2,500**, before selling, attribution, fraud, support, and acquisition. These ad inputs are stress-test assumptions, not measured market rates. More frequent ads may change churn and message categorization; the code's seeded CPM is not market evidence.

Marketing at **₹1,999/month** leaves about **₹1,583** after the modeled deductions. Subtract assumed ₹500 delivery and ₹200 support: **₹883 contribution per billed customer-month**, before trials, acquisition and overhead. At **₹999**, the same cost structure leaves only **₹91**. A lower price requires a meaningfully smaller package; price testing cannot hold value and demand constant in reality.

## Launch simulation

The adjacent Python model and CSV expose every input and all 12 months. It is a **deterministic cohort simulation**, not Monte Carlo, an empirically calibrated forecast, or a probability of success. Downside/base/upside are coherent planning bundles, not confidence intervals. There is no defensible percentage probability of Astra succeeding without actual cohorts and acquisition data.

Both directions assume **₹20,000/month acquisition + ₹20,000/month fixed cash overhead**. Founder salary, initial product build, prelaunch delay, financing, corporate tax, and working-capital/tax settlement timing are excluded. “Operating cash” below is a simplified planning surplus/deficit, not audited cash flow or profit. Upfront build cost must be deducted separately.

Consumer ARPPU is **₹139**, assuming 80% Pro and 20% Business. Marketing's **₹1,999** is a test price, not an existing plan. Starting traffic represents **qualified landing visits**, not social impressions. Traffic is assumed partly earned/partner-led because the acquisition budget stays fixed as visits grow. Founder acquisition labor is not priced into that budget. Visits and conversions are not comparable audience pools across the two markets.

### Assumptions by scenario

| Direction / case | Month 1 visits | Signup | Activation of signup | Paid conversion of activated | First renewal / later monthly renewal | Monthly visit growth |
|---|---:|---:|---:|---:|---:|---:|
| Assistant downside | 2,000 | 15% | 40% | 5% | 35% / 70% | 0% |
| Assistant base | 5,000 | 20% | 50% | 10% | 50% / 80% | 10% |
| Assistant upside | 10,000 | 25% | 65% | 16% | 65% / 90% | 15% |
| Marketing downside | 250 | 10% | 35% | 15% | 50% / 80% | 0% |
| Marketing base | 500 | 16% | 55% | 25% | 65% / 90% | 10% |
| Marketing upside | 1,000 | 20% | 70% | 35% | 80% / 95% | 15% |

The marketing base assumes stronger renewal than RevenueCat's high-retention mobile first-renewal benchmark. That is a demanding **business-workflow hypothesis**, not a sourced category average. Measure it before investing against it. Upside needs all its favorable conditions together; it is not the target budget.

Assistant delivery: 126 replies per payer/month (90 Pro, 270 Business, weighted 80:20), ₹0.15/reply, ₹10 support/payer, 30 replies per active free user. Free-user month-to-month retention is 40% / 55% / 65% by scenario. New paid users leave that month's free pool. Later conversion of existing free users and reactivation are omitted; churned payers are assumed to leave.

Marketing delivery: ₹500/payer/month + ₹200 support; ₹40 trial cost for every activated signup, including eventual payers. Trials do not persist as an ongoing free plan. Human production beyond the support allowance is excluded: a concierge pilot must separately log and price that time.

### Results: third month and first year

Payers are expected cohort equivalents, rounded for display; they are not observed people. MRR is **gross billed subscription run rate before refunds, tax and fees**.

| Direction / case | M3 paying customers | M3 gross MRR | 90-day cumulative operating deficit/surplus | M12 gross MRR | 12-month cumulative operating deficit/surplus |
|---|---:|---:|---:|---:|---:|
| Assistant downside | 10 | ₹1,330 | −₹1.20 lakh | ₹1,788 | −₹4.79 lakh |
| Assistant base | 108 | ₹15,012 | −₹1.10 lakh | ₹51,883 | −₹3.62 lakh |
| Assistant upside | 690 | ₹95,952 | −₹37,354 | ₹5.76 lakh | +₹9.43 lakh |
| Marketing downside | 2 | ₹4,985 | −₹1.16 lakh | ₹8,619 | −₹4.49 lakh |
| Marketing base | 28 | ₹55,192 | −₹74,719 | ₹2.44 lakh | +₹1.39 lakh |
| Marketing upside | 147 | ₹2.94 lakh | +₹1.18 lakh | ₹20.56 lakh | +₹40.42 lakh |

The upside rows are mechanical consequences of sustained growth, conversion and renewal with limited overhead; they do **not** establish a scalable company. Marketing's upside reaches roughly 1,028 billed customers in month 12, which needs real support/production capacity. Budget more staff and operating systems if service time exceeds the per-customer allowance.

In the **base** cases:

- Assistant: month 6 gross MRR about ₹26,052; month 12 operating deficit about ₹21,247/month. It never reaches monthly operating break-even in this 12-month run.
- Marketing: month 6 gross MRR about ₹1.08 lakh, with about ₹5,023 monthly operating surplus; month 12 about ₹2.44 lakh gross MRR and ₹62,883 monthly surplus. Monthly break-even occurs in month 6, cumulative break-even in month 10. Peak modeled cumulative funding need is about **₹87,958**, before build and founder salary.
- If a marketing build costs an additional **₹1 lakh**, its base first-year cumulative surplus falls from about ₹1.39 lakh to **₹38,800**, ignoring build delay. Its first-90-day funding need rises from ₹74,719 to **₹1.75 lakh**. The commercial opportunity does not remove implementation risk.

### What changes the result

Assistant base month-12 operating result remains negative at every modeled reply cost: **−₹8,842 at ₹0.05**, **−₹21,247 at ₹0.15**, and **−₹39,853 at ₹0.30**. Consequently, cheaper WhatsApp delivery alone does not rescue the base acquisition/retention model.

Marketing base month-12 operating result, holding demand fixed purely to isolate arithmetic: **−₹33,875 at ₹999**, **+₹62,883 at ₹1,999**, **+₹1,59,642 at ₹2,999**. Price changes will affect conversion in practice. If delivery rises from ₹500 to **₹1,000/customer/month**, the ₹1,999 base surplus falls to only **₹1,801/month**. Uncontrolled retries or human editing can erase the advantage.

Month-1 blended acquisition spending per new payer is **₹400 assistant / ₹1,818 marketing**. This includes a mix of earned and paid traffic, excludes founder labor, and is not a paid-channel CAC benchmark. Under stationary base renewal, assistant expected billed life is 3.5 months; marketing is 7.5. Approximate contribution life before free/trial subsidy is **₹284 assistant / ₹6,624 marketing**. These are assumption-driven uncapped lifetime calculations, not measured LTV. They explain why ₹400 CAC is already difficult for the assistant, even before subsidizing free users.

At ₹883 marketing contribution, roughly **46 billed customers** cover ₹40,000 monthly acquisition plus fixed overhead before trial spend. Trials raise that threshold. For the assistant, ₹81 contribution per payer before free-user subsidy would require about **493 payers** for the same overhead; free users raise it substantially.

## How launch would likely unfold

The following are behavioral hypotheses to test, not predictions from customer interviews.

| Stage | Broad WhatsApp assistant | Narrow founder-marketing service |
|---|---|---|
| First exposure | Easy to explain; curiosity demos can attract many low-intent users. | Smaller relevant audience; needs visible before/after work for a recognisable founder problem. |
| Signup | Phone verification, app handoff, and permissions may lose users. | Product URL and sample output may activate users; a long brand questionnaire may lose them. |
| First value | Fast useful answer; action execution is where trust will be tested. | Accurate product-specific assets that the founder approves and can edit. |
| First payment | “What do I get beyond my free AI?” and “Why only 10 messages?” | “Will I publish this?” and “Does it save more than ₹1,999 of effort?” |
| First renewal | General chat may lose novelty; repeated completed tasks are needed. | A launch-only user may cancel; a recurring weekly content job can retain. |
| Referral | Needs a shareable completed task, not just an amusing response. | Real campaign examples and a credible founder introduction can attract similar buyers. |
| Scale | Free usage and support can outgrow subscription contribution. | Quality/revision costs and acquisition capacity can outgrow subscription contribution. |

No evidence supports assuming virality, press coverage, app-store featuring, or Product Hunt rank. Earned channels must still produce qualified visits and paid renewals. A quiet launch that retains 20 relevant buyers is better evidence than a large transient signup spike.

## Validation plan and budget

**2–8 November: understand switching.** Interview 10 founders already doing their own marketing and 10 potential assistant power users. Observe their last real task, current tools, time spent, corrections, payments, and what they would stop using. Do not count stated enthusiasm as a purchase. Run a blind comparison on the same 10 briefs against a competent current-tool workflow, including Pomelli if accessible.

**9–15 November: sell two small pilots.** Assistant: 20 relevant users, one permitted repeat workflow, existing pricing. Marketing: 10 real businesses, a clearly described paid campaign package at **₹999–₹1,999**, with manual help disclosed. Test prices in small sequential batches; this sample cannot establish price elasticity statistically. Do not promise a nonexistent automated video or publishing system. Use current tools to deliver before building the full platform.

**16–29 November: measure actual use.** Track signed-up, activated, completed, published, paid and repeated outcomes separately. Conduct exit interviews for non-payers. Record all provider attempts and human minutes. Measure retention by acquisition cohort, use case and channel.

**30 November checkpoint:** select the workflow worth continuing based on payments, actual outputs and repeat use. A complete monthly-renewal result will not yet exist for all November cohorts. Review first monthly renewals around **15 December**; do not label week-two reuse as monthly paid retention.

Proposed pilot cash ceiling: **₹40,000 total**, excluding founder time: ₹5k interviews/recruiting, ₹10k qualified distribution, ₹10k tools/generation/fulfilment, ₹5k infrastructure/payment/support, ₹10k contingency. These are founder planning allowances, not vendor quotations. Pause spending when a funnel or delivery problem is clear; do not spend to hit an arbitrary signup target.

### Decision gates chosen for Astra

These thresholds are management choices for a small pilot, not universal benchmarks or statistical proof:

| Gate | Assistant | Marketing |
|---|---|---|
| Eligibility and truth | Provider accepts actual use case; all sold actions work as described. | Real brief-to-export delivery; sample previews identified. |
| Activation | At least 12/20 finish the chosen useful task within 24h. | At least 7/10 approve a usable campaign. |
| Value | At least 8/20 reuse the task in week two. | At least 6/10 publish an asset within 7 days; median founder time saved ≥2 hours. |
| Payment | At least 5/20 actually pay; report warm-network bias. | At least 5/10 pay for the pilot and at least 3 order a second paid campaign. |
| Delivery quality | ≥95% success over at least 100 approved real tasks; inspect all failures. | ≥70% asset acceptance with no more than one defined revision round; no invented product claims. |
| Economics | Positive contribution after delivery/support, plus a credible free-user subsidy and CAC payback. | Delivery plus support ≤35% of net receipts; paid acquisition payback ≤3 months once enough renewals exist. |
| Renewal | Aim for ≥50% first monthly renewal, evaluated after the due date. | Aim for ≥60% first monthly renewal; treat tiny-sample results as provisional. |

Stop or reshape if users only like demonstrations, do not publish/use the work, will not pay without founder friendship, or require extensive invisible manual labor. If neither direction clears the gates, keep searching for a narrower paid job rather than increasing ad spend.

## What Astra needs to succeed

1. **One paying customer definition and repeat job.** Choose who loses time today and what finished result they buy.
2. **A clear improvement over existing alternatives.** Compare on the same real tasks, total correction time, and published/used results.
3. **Reliable execution and honest scope.** Recover from failures, preserve approvals and versions, and never claim an action happened when it did not.
4. **A viable channel.** Establish messaging eligibility where relevant and keep a working web workflow rather than depending on a single gatekeeper.
5. **Measured contribution.** Record actual costs including retries, failed jobs, free use, refunds and human support. Credits must correspond to real cost exposure.
6. **Repeat purchase before growth spend.** Prove the second campaign or renewed task before optimizing signup volume.
7. **Proof from customers.** Real exported/published campaigns, time savings and later attributable business results, shared with consent.

The evidence favors **testing marketing first**, while preserving useful assistant infrastructure. It does not justify a full all-in-one marketing build yet. The next decisive evidence is a set of paying founders who publish Astra's work and buy again.

## Model files and checks

- `2026-11-02-launch-simulation.py`: editable assumptions, cohort formulas, small self-checks.
- `2026-11-02-launch-simulation.csv`: all six scenarios, 12 monthly rows each.
- `2026-11-02-launch-simulation.json`: the same outputs plus input metadata.

Reproduce with `python3 docs/research/2026-11-02-launch-simulation.py`. Self-checks verify first-month conversion, cohort renewal arithmetic, free-user accumulation, cost sensitivity, and cumulative totals. The interactive comparison uses the same formulas; default outputs were checked against this model. Actual acquisition, usage, renewals, provider bills, advertiser receipts, and the missing original workbook remain the evidence needed to replace assumptions.
