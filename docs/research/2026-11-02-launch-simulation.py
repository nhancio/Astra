"""Conditional planning model, not a statistically calibrated forecast. Stdlib only.

Run from any directory. Outputs JSON/CSV next to this file. All prices INR.
Month 1 starts AFTER a direction has a working, eligible product.
"""
import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
SHARED = dict(acquisition=20000, fixed=20000, gst=.18, fee=.03, refund=.03)
CONFIG = {
    "assistant": dict(price=139, paid_replies=126, reply_cost=.15,
                      paid_support=10, free_replies=30, trial_cost=0,
                      delivery_cost=0, ad_per_free=0),
    "marketing": dict(price=1999, paid_replies=0, reply_cost=0,
                      paid_support=200, free_replies=0, trial_cost=40,
                      delivery_cost=500, ad_per_free=0),
}
# visits, signup, activation, activated-to-paid, first renewal, later renewal,
# monthly visit growth, free-user monthly retention. ALL are planning hypotheses.
SCENARIOS = {
    "assistant": {
        "downside": (2000,.15,.40,.05,.35,.70,0,.40),
        "base": (5000,.20,.50,.10,.50,.80,.10,.55),
        "upside": (10000,.25,.65,.16,.65,.90,.15,.65),
    },
    "marketing": {
        "downside": (250,.10,.35,.15,.50,.80,0,0),
        "base": (500,.16,.55,.25,.65,.90,.10,0),
        "upside": (1000,.20,.70,.35,.80,.95,.15,0),
    },
}


def run(direction, scenario, months=12, overrides=None):
    c = {**SHARED, **CONFIG[direction], **(overrides or {})}
    visits, signup, activation, convert, first, later, growth, free_ret = SCENARIOS[direction][scenario]
    cohorts, rows, free, cash = [], [], 0., 0.
    for month in range(1, months+1):
        v = visits * (1+growth)**(month-1)
        registrations = v*signup
        activated = registrations*activation
        new = activated*convert
        cohorts.append(new)
        paid = sum(n if month-1-i == 0 else n*first*later**(month-2-i)
                   for i,n in enumerate(cohorts))
        free = free*free_ret + activated-new
        gross = paid*c['price']
        refunds = gross*c['refund']
        net_sales = (gross-refunds)/(1+c['gst'])
        fees = gross*c['fee']  # conservative: no processing-fee refunds assumed
        paid_cost = paid*(c['delivery_cost']+c['paid_support']+c['paid_replies']*c['reply_cost'])
        free_cost = free*c['free_replies']*c['reply_cost']
        trial_cost = activated*c['trial_cost']
        ads = free*c['ad_per_free']
        contribution = net_sales-fees-paid_cost-free_cost-trial_cost+ads
        operating = contribution-c['acquisition']-c['fixed']
        cash += operating
        rows.append(dict(direction=direction, scenario=scenario, month=month,
                         visits=v, signups=registrations, activated=activated,
                         new_payers=new, active_payers=paid, active_free=free,
                         gross_mrr=gross, refunds=refunds, net_sales=net_sales,
                         fees=fees, paid_cost=paid_cost, free_cost=free_cost,
                         trial_cost=trial_cost, ad_revenue=ads, contribution=contribution,
                         acquisition=c['acquisition'], fixed=c['fixed'],
                         operating_cash=operating, cumulative_cash=cash,
                         blended_acquisition_cost=c['acquisition']/new if new else None))
    return rows


def check():
    r=run('assistant','base')
    assert r[0]['new_payers'] == 50
    assert abs(r[1]['active_payers']-80) < 1e-8  # 55 new + 25 retained
    assert abs(r[2]['active_payers']-108) < 1e-8  # 60.5 + 27.5 + 20
    assert r[0]['active_free'] == 450
    assert run('assistant','base',overrides={'reply_cost':.30})[0]['operating_cash'] < r[0]['operating_cash']
    for d in CONFIG:
        for s in SCENARIOS[d]:
            rr=run(d,s)
            assert abs(sum(x['operating_cash'] for x in rr)-rr[-1]['cumulative_cash']) < 1e-7
            assert all(x['active_payers'] >= x['new_payers'] for x in rr)
    assert run('marketing','base')[0]['gross_mrr'] == 11*1999


if __name__ == '__main__':
    check()
    rows=[r for d in CONFIG for s in SCENARIOS[d] for r in run(d,s)]
    payload=dict(metadata=dict(date='2026-11-02',currency='INR',
                warning='Assumed inputs; no probabilities or real Astra cohorts. Excludes build cost and founder salary.',
                shared=SHARED, product=CONFIG, scenarios=SCENARIOS), rows=rows)
    (OUT/'2026-11-02-launch-simulation.json').write_text(json.dumps(payload,indent=2)+'\n')
    with (OUT/'2026-11-02-launch-simulation.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for d in CONFIG:
        for s in SCENARIOS[d]:
            rr=run(d,s)
            print(d,s, 'M3 payers/MRR/cumulative cash:',*(round(rr[2][k]) for k in ('active_payers','gross_mrr','cumulative_cash')),
                  'M12 payers/MRR/cumulative cash:',*(round(rr[11][k]) for k in ('active_payers','gross_mrr','cumulative_cash')))
