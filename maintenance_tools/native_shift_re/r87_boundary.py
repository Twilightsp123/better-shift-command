"""R87 type-aware focus verification; reuses the exact SHA/PE guard from R86."""
from pathlib import Path
import json
from audit_r86_spatial import verify as verify_native
HERE=Path(__file__).resolve().parent
def audit_bytes(data,m=None):
    m=m or json.loads((HERE/'r87_boundary_pins.json').read_text())
    result=verify_native(data,m)
    must={
     '0305a800':'e80fa90200', '03059f4e':'48398380000000',
     '0305a7c1':'4c8bc6', '0308529d':'498d8dd8010000',
     '030852a7':'ff5010', '0308d857':'4883b9e802000000',
     '0308d865':'8b816c020000','0308da23':'488d93e0010000',
     '03147199':'f30f118b3c010000','031471a1':'f30f11a344010000',
     '0314745d':'f30f118340010000','03147465':'f30f11933c010000',
     '0314746d':'f30f119b44010000',
     '0314720b':'f30f118388000000','03147223':'f30f118b8c000000',
     '0314723b':'f30f118390000000'}
    for site,raw in must.items():
        if m['pins'][site]['hex']!=raw:raise ValueError('R87_SEMANTIC_'+site)
    result.update({'native_contact_virtual_handoff_not_direct_member_XYZ_store':True,
       'independent_integrator_pending_delta_sources_verified':True,
       'ordinary_Shift_runtime_impact_proven':False,'live_hook_authorized':False})
    return result
def post_gate(has_30,has_2e8,code,passes_extra):
    return bool(has_30 and has_2e8 and code in (0x78,0x79) and passes_extra)
