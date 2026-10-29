import itertools,json,pathlib,math
D=json.load(open('hardware/pcb/output/design.json'));P={p['id']:p for p in D['parts']}
def val(role):
 x=P[role]['value'].split()[0]
 return float(x[:-1])*{'k':1e3,'M':1e6,'R':1}[x[-1]] if x[-1] in 'kMR' else float(x)
def corners(role,tol=.001):
 x=val(role);return x*(1-tol),x*(1+tol)
def monitor(v33):
 pos=[];neg=[]
 for rp1,rp2,rn1,rn2,rr1,rr2,e1,e2,ip,imn,iref1,iref2 in itertools.product(corners('RPMON1'),corners('RPMON2'),corners('RNMON1'),corners('RNMON2'),corners('RMONREF1'),corners('RMONREF2'),(-.004,.004),(-.004,.004),(0,50e-9),(0,50e-9),(0,50e-9),(0,50e-9)):
  # LM393B PNP input bias is negative (current out of pins), max50nA per input.
  ref=v33*rr2/(rr1+rr2)+(iref1+iref2)*(rr1*rr2/(rr1+rr2))
  pos.append((ref+e1)*((rp1+rp2)/rp2)-ip*rp1)
  # SENSE_NEG = (Vneg/rn1 + v33/rn2 + Ibias)*Rparallel.
  neg.append((ref+e2)*(1+rn1/rn2)-v33*rn1/rn2-imn*rn1)
 return {'v33':v33,'positive_trip':[min(pos),max(pos)],'negative_trip':[min(neg),max(neg)]}
f5=[];rise5=[]
for top,bot,vref,bias in itertools.product(corners('R5MON1'),corners('R5MON2'),(.405*.98,.405*1.02),(-25e-9,25e-9)):
 f5.append(vref*(1+top/bot)+bias*top)
 # Hysteresis is max3% of actual VIT; use1.03 conservative worstcase.
 rise5.append(vref*1.03*(1+top/bot)+bias*top)
rows=[monitor(v) for v in [3.3,3.201,3.399,2.86]]
ro=1000*.99
print(json.dumps({'monitor5':{'falling_nominal':.405*(1+109e3/10e3),'falling_corners':[min(f5),max(f5)],'max_release':max(rise5),'conditions':'TPS3808G01 ±2% VIT,3% max hysteresis,±25nA sense,0.1% R'},'rail_monitors':rows,'output_collisions':[{'driver':d,'external':e,'I_max_mA':1000*abs(d-e)/ro,'P_max_W':(d-e)**2/ro} for d,e in [(5,-12),(-5,12),(5,-5),(11.5,-12),(12,-12)]]},indent=2))
assert .29<(5+12)**2/ro<.3
assert (12+12)**2/ro>.5
assert min(f5)<4.75 and max(rise5)>5
