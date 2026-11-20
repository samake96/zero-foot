#!/usr/bin/env python3
"""ZEROFOOT V3.1: chronological tuning and untouched holdout, stdlib only."""
import argparse, json, math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUTCOMES=('H','D','A')
def outcome(m):
    return 'H' if m['home_goals']>m['away_goals'] else ('A' if m['home_goals']<m['away_goals'] else 'D')
def poiss(k,lam): return math.exp(-lam)*lam**k/math.factorial(k)
def probabilities(lh,la):
    h=[poiss(i,lh) for i in range(13)];a=[poiss(i,la) for i in range(13)]
    p=dict.fromkeys(OUTCOMES,0.)
    for i,ph in enumerate(h):
        for j,pa in enumerate(a): p['H' if i>j else 'A' if i<j else 'D']+=ph*pa
    s=sum(p.values());return {k:v/s for k,v in p.items()}
def estimate(history,match,prior=5,decay=0):
    # All input observations must precede target kickoff.
    if any(x['utc_date']>=match['utc_date'] for x in history): raise ValueError('Chronological leakage detected')
    weights=[math.exp(-decay*(len(history)-1-i)/38) for i in range(len(history))]
    sw=sum(weights)
    lg_h=(sum(w*m['home_goals'] for w,m in zip(weights,history))+20*1.45)/(sw+20)
    lg_a=(sum(w*m['away_goals'] for w,m in zip(weights,history))+20*1.15)/(sw+20)
    def rate(which,ident,field,mean):
        rows=[(w,m) for w,m in zip(weights,history) if m[which]==ident]
        return (sum(w*m[field] for w,m in rows)+prior*mean)/(sum(w for w,_ in rows)+prior)
    hf=rate('home_id',match['home_id'],'home_goals',lg_h)
    hc=rate('home_id',match['home_id'],'away_goals',lg_a)
    af=rate('away_id',match['away_id'],'away_goals',lg_a)
    ac=rate('away_id',match['away_id'],'home_goals',lg_h)
    lh=max(.15,min(4.5,hf*ac/max(.2,lg_h)))
    la=max(.15,min(4.5,af*hc/max(.2,lg_a)))
    return probabilities(lh,la)
def score(rows):
    if not rows:return None
    n=len(rows)
    return {'matches':n,'accuracy':round(sum(max(p,key=p.get)==y for p,y in rows)/n,4),
            'brier':round(sum(sum((p[k]-int(y==k))**2 for k in OUTCOMES) for p,y in rows)/n,4),
            'log_loss':round(sum(-math.log(max(1e-12,p[y])) for p,y in rows)/n,4)}
def run(items,min_history,holdout_fraction):
    # Chronological 60% training, 20% tuning, 20% test by kickoff groups.
    batches=[]
    for m in items:
        if not batches or batches[-1][0]['utc_date']!=m['utc_date']:batches.append([])
        batches[-1].append(m)
    cut1=int(len(batches)*(1-holdout_fraction-0.2));cut2=int(len(batches)*(1-holdout_fraction))
    cut1=max(1,cut1);cut2=max(cut1+1,cut2)
    candidates=[(5,0),(3,0),(8,0),(5,0.6),(5,1.2),(8,0.6)]
    history=[];tuning={str(c):[] for c in candidates};test={str(c):[] for c in candidates};baseline=[]
    for i,batch in enumerate(batches):
        if len(history)>=min_history:
            if cut1<=i<cut2 or i>=cut2:
                for m in batch:
                    y=outcome(m)
                    for c in candidates:
                        p=estimate(history,m,*c)
                        (tuning if i<cut2 else test)[str(c)].append((p,y))
                    if i>=cut2:
                        counts={k:sum(outcome(x)==k for x in history) for k in OUTCOMES}
                        denom=len(history)+3
                        baseline.append(({k:(counts[k]+1)/denom for k in OUTCOMES},y))
        history.extend(batch)
    eligible=[c for c in candidates if tuning[str(c)]]
    if not eligible:return {'status':'insufficient_tuning_data','historical_matches':len(items)}
    chosen=min(eligible,key=lambda c:(score(tuning[str(c)])['log_loss'],str(c)))
    selected=test[str(chosen)]
    # Test scores for V0 use exact same untouched holdout fixtures.
    v0=test[str((5,0))]
    bins=[]
    for low in (0,.2,.4,.6,.8):
        entries=[(max(p.values()),int(max(p,key=p.get)==y)) for p,y in selected if low<=max(p.values())<(low+.2 if low<.8 else 1.00001)]
        bins.append({'range':f'{low:.1f}-{low+.2:.1f}','count':len(entries),'mean_confidence':round(sum(x for x,_ in entries)/len(entries),4) if entries else None,'observed_accuracy':round(sum(y for _,y in entries)/len(entries),4) if entries else None})
    return {'status':'ok','historical_matches':len(items),'tuning_matches':len(tuning[str(chosen)]),'test_matches':len(selected),'chosen_parameters':{'prior':chosen[0],'decay':chosen[1]},'tuning_log_loss':score(tuning[str(chosen)])['log_loss'], 'holdout_v31':score(selected),'holdout_v0':score(v0),'holdout_baseline':score(baseline),'confidence_calibration':bins}
def main():
    a=argparse.ArgumentParser();a.add_argument('--input',default='data/historical_matches.json');a.add_argument('--output',default='data/model_validation_v31.json');a.add_argument('--min-history',type=int,default=60);args=a.parse_args()
    source=json.loads(Path(args.input).read_text(encoding='utf-8'))
    leagues=defaultdict(list);seen=set()
    for m in source.get('matches',[]):
        try:
            if m['id'] in seen or any(type(m[k])!=int or m[k]<0 for k in ('home_goals','away_goals')):continue
            if not m['home_id'] or not m['away_id']:continue
            datetime.fromisoformat(m['utc_date'].replace('Z','+00:00'))
            seen.add(m['id']);leagues[m['competition']].append(m)
        except (KeyError,TypeError,ValueError):continue
    result={k:run(sorted(v,key=lambda m:(m['utc_date'],m['id'])),args.min_history,.2) for k,v in sorted(leagues.items())}
    report={'model':'poisson_v31_experimental','created_at':datetime.now(timezone.utc).isoformat(),'method':'Per-league chronological train/tune/test by kickoff; hyperparameters chosen on tuning only; final 20% holdout untouched; no future match data','warning':'Historical-only evaluation, not calibrated for live predictions or betting','competitions':result}
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    for k,v in result.items():print(k,v['status'],v.get('holdout_v31'), 'baseline',v.get('holdout_baseline'))
if __name__=='__main__':main()
