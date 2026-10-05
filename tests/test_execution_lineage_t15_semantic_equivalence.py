from pathlib import Path
import re,itertools
ROOT=Path(__file__).resolve().parents[1]
old=(ROOT/'archive/tpol_t15_pre_execution_lineage/source/better_shift_command.lua').read_text(encoding='utf-8')
new=(ROOT/'source/better_shift_command.lua').read_text(encoding='utf-8')

def fail(msg):
    print('FAIL '+msg);raise SystemExit(1)

def function_block(text, signature, next_marker):
    a=text.find(signature)
    if a<0: fail('missing '+signature)
    b=text.find(next_marker,a+len(signature))
    if b<0: fail('missing end marker '+next_marker)
    return text[a:b]

# T1.5 must not alter the shared policy engine or the geometry gates it consumes.
for signature,next_marker in [
    ('function R1.TransitionPolicy.evaluate(', '\nlocal function attack_metrics'),
    ('local function route_handoff_ready(', '\nlocal function transition_handoff_ready'),
    ('local function attack_geometry(', '\nlocal function attack_brake_state'),
]:
    if function_block(old,signature,next_marker)!=function_block(new,signature,next_marker):
        fail(signature+' changed during behavior-neutral T1.5')

# All scalar CFG assignments must be identical. T1.5 cannot tune a gameplay threshold.
def cfg_scalars(text):
    start=text.find('local CFG=')
    if start<0: fail('CFG missing')
    end=text.find('\n}',start)
    block=text[start:end+2]
    return dict(re.findall(r'([A-Za-z0-9_]+)\s*=\s*([-+]?[0-9]+(?:\.[0-9]+)?)',block))
if cfg_scalars(old)!=cfg_scalars(new):
    fail('CFG scalar values changed')

# Model the old action_execution_identity() and the new adapter. For every shape
# of captured vs accepted identity, the authoritative seq/receipt/lifetime/reason
# must stay identical. New lineage is extra metadata only.
def valid(x): return isinstance(x,str) and x.isdigit() and 0<len(x)<=10 and (len(x)==1 or x[0]!='0') and (len(x)<10 or x<='4294967295')
def old_id(a):
    rt=a.get('runtime',{})
    seq=rt.get('accepted_seq') if rt.get('accepted_receipt') else a.get('seq')
    if rt.get('accepted_receipt') and not rt.get('accepted_seq'):
        return None,None,None,'ACCEPTED_WITHOUT_NATIVE_SEQUENCE'
    receipt=rt.get('accepted_receipt') or a.get('serial')
    lifetime=rt.get('accepted_lifetime') or a.get('unit_lifetime')
    if not (valid(seq) and valid(receipt) and valid(lifetime)):
        return None,None,None,'ACTION_IDENTITY_INCOMPLETE'
    return seq,receipt,lifetime,'OK'
def new_id(a):
    rt=a.get('runtime',{})
    issued=rt.get('issued_identity')
    if issued is not None:
        if issued.get('receipt') and not issued.get('seq'):
            return None,None,None,'ACCEPTED_WITHOUT_NATIVE_SEQUENCE'
        vals=(issued.get('seq'),issued.get('receipt'),issued.get('lifetime') or a.get('unit_lifetime'))
        if not all(valid(x) for x in vals): return None,None,None,'ACTION_IDENTITY_INCOMPLETE'
        return *vals,'OK'
    if rt.get('accepted_receipt'):
        if not rt.get('accepted_seq'): return None,None,None,'ACCEPTED_WITHOUT_NATIVE_SEQUENCE'
        vals=(rt.get('accepted_seq'),rt.get('accepted_receipt'),rt.get('accepted_lifetime') or a.get('unit_lifetime'))
        if not all(valid(x) for x in vals): return None,None,None,'ACTION_IDENTITY_INCOMPLETE'
        return *vals,'OK'
    cap=a.get('capture_identity')
    vals=(cap.get('seq'),cap.get('receipt'),rt.get('accepted_lifetime') or cap.get('lifetime') or a.get('unit_lifetime')) if cap else (a.get('seq'),a.get('serial'),rt.get('accepted_lifetime') or a.get('unit_lifetime'))
    if not all(valid(x) for x in vals): return None,None,None,'ACTION_IDENTITY_INCOMPLETE'
    return *vals,'OK'

vals=[None,'1','17','0001','4294967295']
checked=0
for seq,serial,life,aseq,areceipt,alife in itertools.product(vals, repeat=6):
    a={'seq':seq,'serial':serial,'unit_lifetime':life,'capture_identity':{'seq':seq,'receipt':serial,'lifetime':life},
       'runtime':{'accepted_seq':aseq,'accepted_receipt':areceipt,'accepted_lifetime':alife}}
    # Runtime T1.5 creates issued_identity exactly when an own ACK populated accepted_*.
    if areceipt is not None:
        a['runtime']['issued_identity']={'seq':aseq,'receipt':areceipt,'lifetime':alife}
    if old_id(a)!=new_id(a): fail('identity semantics changed for '+repr(a))
    checked+=1
print(f'PASS: T1.5 semantic equivalence; policy/geometry/CFG unchanged and {checked} identity states equivalent')