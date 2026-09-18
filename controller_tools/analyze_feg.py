"""Read sampled FEG1/FEG2/FEG3/FEG4 evidence. Never claims entity-majority or real physical impact."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

def analyze(text:str)->dict:
    histories={};issued={};violations=[];failures=[];acks=[]
    for lineno,line in enumerate(text.splitlines(),1):
        if '[BETTER_SHIFT_COMMAND]' not in line:continue
        if 'CONTROLLER_FAIL' in line:failures.append({'line':lineno,'text':line})
        m=re.search(r'\b(FEG_[A-Z_]+)\b',line)
        if not m:continue
        event=m[1];kv=dict(re.findall(r'([A-Za-z_]+)=([^\s]+)',line))
        if event=='FEG_CONFIG':continue
        uid,gen=kv.get('uid'),kv.get('gen')
        if not uid or not gen:continue
        attack_issue=kv.get('attack_issue') if event in ('FEG_EXIT_ISSUED','FEG_EXIT_ACK') else kv.get('issue')
        key=uid+':'+gen+':'+str(attack_issue);h=histories.setdefault(key,{'uid':uid,'gen':gen,'attack_issue':attack_issue,'opens':[],'suppressed_samples':0,
            'last_sample':None,'relocks':0,'cancelled':False,'has_tail_seen':False})
        h['has_tail_seen'] |= kv.get('has_tail')=='true'
        def n(k,default=0.):
            try:return float(kv.get(k,default))
            except (TypeError,ValueError):return default
        if event=='FEG_OPEN':h['opens'].append({'ms':n('model_ms'),'reason':kv.get('reason'),'line':lineno})
        elif event=='FEG_SAMPLE':
            h['last_sample']={'line':lineno,**kv}
            if kv.get('gate_open')=='false' and n('eligible_ms')>0:
                violations.append({'line':lineno,'reason':'credit reported while gate closed'})
            if kv.get('gate_open')=='false' and kv.get('raw_eligible')=='true' and n('legacy_eligible_ms')>=3000:
                h['suppressed_samples']+=1
        elif event=='FEG_RELOCK':h['relocks']+=1
        elif event=='FEG_CANCEL':h['cancelled']=True
        elif event=='FEG_EXIT_ISSUED':
            if h['cancelled']:violations.append({'line':lineno,'reason':'exit issued after generation cancellation'})
            if n('hold_ms')<3000:violations.append({'line':lineno,'reason':'under-three-second exit'})
            if n('model_ms')-n('gate_open_ms')<3000:violations.append({'line':lineno,'reason':'confirmation/approach credited to three-second hold'})
            if not h['opens']:violations.append({'line':lineno,'reason':'no gate-open evidence before exit'})
            issued[(key,kv.get('issue'))]={'line':lineno,**kv}
        elif event=='FEG_EXIT_ACK':
            i=issued.get((key,kv.get('issue')))
            if not i:violations.append({'line':lineno,'reason':'exit ACK without matching issued event'})
            if h['cancelled']:violations.append({'line':lineno,'reason':'late ACK accepted after cancellation'})
            acks.append({'line':lineno,**kv})
    version=next((v for v in ('FEG4','FEG3','FEG2','FEG1') if 'FEG_CONFIG version='+v in text),'UNRECOGNIZED')
    ready=('FEG_CONFIG version='+version) in text
    return {'schema':2,'test':version,'evidence_kind':('SYNTHETIC_OFFLINE' if 'SYNTHETIC_OFFLINE_TEST' in text else 'SUPPLIED_RUNTIME_LOG_NOT_INDEPENDENTLY_AUTHENTICATED'),'test_loaded':ready,
            'sampled_gate_contract_pass':ready and bool(histories) and not violations and not failures,
            'timed_exit_command_pass':bool(acks) and not violations and not failures,
            'legacy_early_time_suppressed':any(h['suppressed_samples'] for h in histories.values()),
            'physical_majority_engagement':'UNASSESSED_NO_ENTITY_MEASUREMENT',
            'physical_disengagement':'UNASSESSED_COMMAND_ACK_IS_NOT_ARRIVAL',
            'case_count':len(histories),'exit_acks':acks,'cases':list(histories.values()),
            'violations':violations,'controller_failures':failures,
            'scope':'Reports sampled numeric conditions only. It cannot identify the true main body or prove most models attacked.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args();r=analyze(a.log.read_text(encoding='utf-8-sig',errors='replace'))
    s=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
    if a.out:a.out.write_text(s,encoding='utf-8')
    print(s)
if __name__=='__main__':main()
