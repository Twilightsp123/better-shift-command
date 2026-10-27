"""R77 purely synthetic turn kinematics; not WH3 motion, collision radii or physics."""
from itertools import combinations
import math
def grid():
 return [((c-1)*3.,(r-1)*3.) for r in range(3) for c in range(3)]
def rot(p,d):
 a=math.radians(d);x,y=p
 return x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)
def lerp(a,b,t):
 return [((1-t)*x+t*u,(1-t)*y+t*v) for (x,y),(u,v) in zip(a,b)]
def gap(points):
 return min(math.dist(a,b) for a,b in combinations(points,2))
def rigid(p,angle,t):return [rot(x,angle*t) for x in p]
def staged(p,t):
 if not 0<=t<=1:raise ValueError("t")
 mid=[rot(x,90) for x in p]
 return lerp(p,mid,t*2) if t<=.5 else lerp(mid,[rot(x,180) for x in p],2*t-1)
def phase_lag(p,t):
 return [rot(x,180*max(0,min(1,t+(-.18 if x[0]<0 else .18 if x[0]>0 else 0)))) for x in p]
def curvature(radius,halfwidth):
 if not all(math.isfinite(v) and v>0 for v in (radius,halfwidth)):
  raise ValueError("invalid size")
 return {"inner":1-halfwidth/radius,"outer":1+halfwidth/radius,
   "positive_forward_rigid_motion_compatible":radius>halfwidth}
def evaluate():
 p=grid();end=[rot(x,180) for x in p]
 return {"initial_min":gap(p),"straight_180_middle":gap(lerp(p,end,.5)),
    "straight_90_middle":gap(lerp(p,[rot(x,90) for x in p],.5)),
    "two_staged_90_min":min(gap(staged(p,i/100)) for i in range(101)),
    "smooth_rigid_180_min":min(gap(rigid(p,180,i/100)) for i in range(101)),
    "member_phase_lag_example_min":min(gap(phase_lag(p,i/100)) for i in range(101)),
    "tight_curvature":curvature(2.,3.),"wide_curvature":curvature(12.,3.),
    "evidence":"SYNTHETIC_ONLY_NOT_WARHAMMER_GAMEPLAY","cause_proven":False}
