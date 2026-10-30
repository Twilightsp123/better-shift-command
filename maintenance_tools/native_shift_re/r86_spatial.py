"""R86 public synthetic same-time clearance contracts. Not WH3 physics."""
from dataclasses import dataclass
from math import hypot,pi,sin,cos,isfinite,sqrt
from itertools import combinations
@dataclass(frozen=True)
class Track:
    name:str
    times:tuple
    positions:tuple
    def __post_init__(self):
        if not self.name or len(self.times)!=len(self.positions) or len(self.times)<2:raise ValueError("SHAPE")
        if any(y<=x for x,y in zip(self.times,self.times[1:])):raise ValueError("TIME_ORDER")
        if any(len(p)!=2 or not all(isfinite(v) for v in p) for p in self.positions):raise ValueError("COORDINATES")
    def at(self,t):
        if not self.times[0]<=t<=self.times[-1]:raise ValueError("TIME_BOUNDS")
        for i in range(len(self.times)-1):
            if t<=self.times[i+1]:
                s=(t-self.times[i])/(self.times[i+1]-self.times[i]);a,b=self.positions[i:i+2]
                return (a[0]*(1-s)+b[0]*s,a[1]*(1-s)+b[1]*s)
        return self.positions[-1]
def closest_same_time(a,b):
    lo=max(a.times[0],b.times[0]);hi=min(a.times[-1],b.times[-1])
    if lo>=hi:raise ValueError("NO_OVERLAP")
    knots=sorted({lo,hi}|{v for v in a.times+b.times if lo<v<hi})
    best=(float("inf"),None)
    for t,u in zip(knots,knots[1:]):
        p,q=a.at(t),b.at(t);r,s=a.at(u),b.at(u)
        x=p[0]-q[0];z=p[1]-q[1];vx=r[0]-s[0]-x;vz=r[1]-s[1]-z
        d=vx*vx+vz*vz;alpha=0 if d<1e-12 else max(0,min(1,-(x*vx+z*vz)/d))
        dist=hypot(x+alpha*vx,z+alpha*vz)
        if dist<best[0]:best=(dist,t+alpha*(u-t))
    return best
def transverse_crossings(a,b):
    crossings=[]
    for i in range(len(a.times)-1):
        p,q=a.positions[i:i+2];u=(q[0]-p[0],q[1]-p[1])
        for j in range(len(b.times)-1):
            r,s=b.positions[j:j+2];v=(s[0]-r[0],s[1]-r[1])
            den=u[0]*v[1]-u[1]*v[0]
            if abs(den)<1e-12:continue
            w=(r[0]-p[0],r[1]-p[1])
            x=(w[0]*v[1]-w[1]*v[0])/den;y=(w[0]*u[1]-w[1]*u[0])/den
            if -1e-9<=x<=1+1e-9 and -1e-9<=y<=1+1e-9:
                ta=a.times[i]+x*(a.times[i+1]-a.times[i])
                tb=b.times[j]+y*(b.times[j+1]-b.times[j])
                crossings.append((ta,tb))
    return crossings
def grid():return [((c-1)*3.,(r-1)*3.) for r in range(3) for c in range(3)]
def rot(p,a):return(p[0]*cos(a)-p[1]*sin(a),p[0]*sin(a)+p[1]*cos(a))
def members(kind,t):
    out=[]
    for p in grid():
        if kind=="straight180":q=((1-2*t)*p[0],(1-2*t)*p[1])
        elif kind=="rigid":q=rot(p,pi*t)
        elif kind=="lagged":q=rot(p,pi*max(0,min(1,t+(-.18 if p[0]<0 else .18 if p[0]>0 else 0))))
        elif kind=="two90":
            s=2*t if t<=.5 else 2*t-1
            a=p if t<=.5 else rot(p,pi/2);b=rot(p,pi/2) if t<=.5 else rot(p,pi)
            q=(a[0]*(1-s)+b[0]*s,a[1]*(1-s)+b[1]*s)
        else:raise ValueError("KIND")
        out.append(q)
    return out
def grid_tracks(kind,steps=100):
    times=tuple(i/steps for i in range(steps+1))
    return [Track(str(i),times,tuple(members(kind,t)[i] for t in times)) for i in range(9)]
def closest_group(tracks):
    return min(closest_same_time(a,b)[0] for a,b in combinations(tracks,2))
def crossing_fixtures():
    later=(Track("H",(0,.5,1),((-2.,0.),(2.,0.),(2.,0.))),
           Track("V",(0,.5,1),((0.,-2.),(0.,-2.),(0.,2.))))
    same=(Track("H",(0,1),((-2.,0.),(2.,0.))),
          Track("V",(0,1),((0.,-2.),(0.,2.))))
    near=(Track("H",(0,1),((-2.,0.),(2.,0.))),
          Track("P",(0,1),((-2.,.7),(2.,.7))))
    return later,same,near
def world_xyz(local,mat,translate):
    if len(local)!=3 or len(mat)!=3 or any(len(row)!=3 for row in mat) or len(translate)!=3:raise ValueError("XYZ_MATRIX")
    return tuple(translate[i]+sum(mat[i][j]*local[j] for j in range(3)) for i in range(3))
def radius(R,H):
    if min(R,H)<=0 or not isfinite(R) or not isfinite(H):raise ValueError("R_H")
    return 1-H/R,1+H/R
