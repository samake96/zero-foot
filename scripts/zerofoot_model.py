#!/usr/bin/env python3
"""ZEROFOOT V3: leak-free, per-league Poisson backtest; stdlib only."""
import argparse, json, math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CODES={'PL':'Premier League','PD':'La Liga','BL1':'Bundesliga','SA':'Serie A','FL1':'Ligue 1'}

def outcome(h,a): return 'H' if h>a else ('A' if h<a else 'D')
def poisson(k,lam): return math.exp(-lam)*lam**k/math.factorial(k)
def probs(lh,la,cap=12):
    ph=[poisson(i,lh) for i in range(cap+1)];pa=[poisson(i,la) for i in range(cap+1)]
    result={'H':0.,'D':0.,'A':0.}
    for i,x in enumerate(ph):
        for j,y in enumerate(pa): result[outcome(i,j)]+=x*y
    norm=sum(result.values());return {k:v/norm for k,v in result.items()}

def rates(history,home_id,away_id):
    # Shrink toward league means to avoid unstable early-season estimates.
    n=len(history)
    league_home=(sum(m['home_goals'] for m in history)+1.45*20)/(n+20)
    league_away=(sum(m['away_goals'] for m in history)+1.15*20)/(n+20)
    h=[m for m in history if m['home_id']==home_id]
    a=[m for m in history if m['away_id']==away_id]
    prior=5
    hf=(sum(m['home_goals'] for m in h)+prior*league_home)/(len(h)+prior)
    hc=(sum(m['away_goals'] for m in h)+prior*league_away)/(len(h)+prior)
    af=(sum(m['away_goals'] for m in a)+prior*league_away)/(len(a)+prior)
    ac=(sum(m['home_goals'] for m in a)+prior*league_home)/(len(a)+prior)
    lam_h=max(.15,min(4.5,hf*ac/max(.2,league_home)))
    lam_a=max(.15,min(4.5,af*hc/max(.2,league_away)))
    return lam_h,lam_a

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',default='data/historical_matches.json');p.add_argument('--output',default='data/model_validation.json');p.add_argument('--min-history',type=int,default=60)
    args=p.parse_args();source=json.loads(Path(args.input).read_text(encoding='utf-8'))
    raw=source.get('matches',[]);valid=[];ids=set()
    for m in raw:
        try:
            if m['competition'] not in CODES or m['id'] in ids: continue
            if not all(isinstance(m[k],int) and m[k]>=0 for k in ('home_goals','away_goals')): continue
            datetime.fromisoformat(m['utc_date'].replace('Z','+00:00'))
            ids.add(m['id']);valid.append(m)
        except (KeyError,TypeError,ValueError): continue
    valid.sort(key=lambda m:(m['utc_date'],m['id']))
    byleague=defaultdict(list)
    for m in valid: byleague[m['competition']].append(m)
    report={}
    for code,items in sorted(byleague.items()):
        # Group simultaneous kickoffs to prevent using contemporaneous outcomes.
        history=[]; predictions=[];i=0
        while i<len(items):
            j=i+1
            while j<len(items) and items[j]['utc_date']==items[i]['utc_date']: j+=1
            batch=items[i:j]
            if len(history)>=args.min_history:
                for m in batch:
                    lh,la=rates(history,m['home_id'],m['away_id']);pr=probs(lh,la)
                    actual=outcome(m['home_goals'],m['away_goals']);pick=max(pr,key=pr.get)
                    predictions.append({'id':m['id'],'date':m['utc_date'],'actual':actual,'pick':pick,'probabilities':{k:round(v,5) for k,v in pr.items()},'brier':sum((pr[k]-(k==actual))**2 for k in ('H','D','A')),'log_loss':-math.log(max(1e-12,pr[actual]))})
            history.extend(batch);i=j
        n=len(predictions)
        report[code]={'name':CODES[code],'historical_matches':len(items),'evaluated_matches':n,'accuracy':round(sum(x['pick']==x['actual'] for x in predictions)/n,4) if n else None,'brier_score':round(sum(x['brier'] for x in predictions)/n,4) if n else None,'log_loss':round(sum(x['log_loss'] for x in predictions)/n,4) if n else None,'baseline_accuracy':round(max(sum(x['actual']==k for x in predictions) for k in ('H','D','A'))/n,4) if n else None}
    total=sum(v['evaluated_matches'] for v in report.values())
    output={'model':'poisson_v0_experimental','created_at':datetime.now(timezone.utc).isoformat(),'source':source.get('source'),'input_matches':len(raw),'valid_matches':len(valid),'min_prior_league_matches':args.min_history,'method':'Chronological walk-forward; simultaneous fixtures excluded from each other; smoothed league and team home/away scoring rates; independent Poisson','warning':'Experimental historical validation, not calibrated or suitable for guaranteed returns. Historical season only; no current predictions.','evaluated_matches':total,'competitions':report}
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'evaluated_matches':total,'competitions':report},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
