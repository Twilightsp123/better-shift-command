"""BSC R95 offline world goal calculation. Never accesses a live process.

Machine-code evidence: nav ref at record+0x10 (0x03121F54), packet ref
at record+0x18 (0x0312214C), both transform via 0x02F3D668.
A correctly parsed record does not prove a valid Shift task or snapshot.
"""
import math
import struct

NAV_REF_OFF = 0x10
PACKET_REF_OFF = 0x18
FRAME_BYTES_MIN = 0x5c

class InvalidEvidence(ValueError):
    pass

def xyz(raw, offset):
    if len(raw) < offset + 12:
        raise InvalidEvidence("incomplete XYZ")
    vals = struct.unpack_from("<3f", raw, offset)
    if not all(math.isfinite(x) for x in vals):
        raise InvalidEvidence("nonfinite coordinate")
    return vals

def record(kind, raw):
    off = {"nav": NAV_REF_OFF, "packet": PACKET_REF_OFF}.get(kind)
    if off is None or len(raw) < off + 8:
        raise InvalidEvidence("unknown or truncated record")
    return xyz(raw, 0), struct.unpack_from("<Q", raw, off)[0]

def f32(v):
    return struct.unpack("<f", struct.pack("<f", v))[0]

def affine_world(local, ref_raw=None):
    if ref_raw is None:
        return tuple(local)
    if len(ref_raw) < FRAME_BYTES_MIN:
        raise InvalidEvidence("reference frame truncated")
    t = xyz(ref_raw, 0x18)
    rows = [xyz(ref_raw, 0x38 + 12*i) for i in range(3)]
    x, y, z = local
    result = []
    # Scalar SSE operation grouping from 0x02F3D668. No FTZ/DAZ guarantee.
    for (a,b,c),trans in zip(rows,t):
        xy = f32(f32(y*b) + f32(x*a))
        zt = f32(f32(z*c) + trans)
        result.append(f32(xy+zt))
    return tuple(result)

def resolve(kind, record_bytes, ref_by_ptr):
    local,ptr = record(kind,record_bytes)
    if ptr == 0:
        return affine_world(local)
    if ptr not in ref_by_ptr:
        raise InvalidEvidence("missing captured reference frame")
    return affine_world(local, ref_by_ptr[ptr])

def inspect_snapshot(source):
    """Only checks pre-captured byte records; labels output STRUCTURAL_ONLY."""
    if source.get("origin") not in ("synthetic", "externally_supplied_unverified"):
        raise InvalidEvidence("unsupported/unverified source")
    keys = ("root_generation","group_generation","route_generation","tick_id","reference_epoch")
    for key in keys:
        if source.get(key) is None:
            raise InvalidEvidence("missing identity or epoch: "+key)
    frames = {int(p, 16):bytes.fromhex(raw)
              for p,raw in source.get("reference_bytes_by_pointer",{}).items()}
    seen=set();members=[]
    for member in source.get("members", []):
        mid=member.get("member_id")
        if not mid or mid in seen:
            raise InvalidEvidence("duplicate/missing member")
        seen.add(mid)
        for key in keys:
            if member.get(key)!=source[key]:
                raise InvalidEvidence("mixed epoch: "+key)
        pos=resolve(member["record_kind"],bytes.fromhex(member["record_hex"]),frames)
        members.append({"id":mid,"world_xyz":list(pos)})
    if not members:
        raise InvalidEvidence("empty member list")
    return {"evidence_level":"STRUCTURAL_ONLY",
            "live_lifetime_proven":False,
            "shift_causality_proven":False,
            "members":members}
