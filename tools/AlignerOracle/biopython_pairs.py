import random, sys
from Bio import Align
from Bio.Align import substitution_matrices
random.seed(116)
R="ACDEFGHIKLMNPQRSTVWY"
def rs(n): return "".join(random.choice(R) for _ in range(n))
def mut(s):
    c=list(s)
    for k in range(len(c)):
        if random.random()<0.15: c[k]=random.choice(R)
    if len(c)>6 and random.random()<0.6:
        st=random.randrange(len(c)-5); del c[st:st+random.randint(1,5)]
    if random.random()<0.6:
        p=random.randrange(len(c)+1); c[p:p]=rs(random.randint(1,6))
    if random.random()<0.4: c=list(rs(random.randint(1,8)))+c
    if random.random()<0.4: c+=list(rs(random.randint(1,8)))
    return "".join(c)
out=open("pairs.tsv","w")
for free in (True,False):
    a=Align.PairwiseAligner(mode="global")
    a.substitution_matrix=substitution_matrices.load("BLOSUM62")
    a.open_gap_score=-12; a.extend_gap_score=-1   # first residue costs open+extend = 12
    if free: a.end_gap_score=0
    for _ in range(1500):
        s=rs(random.randint(1,80)); t=mut(s) if random.random()<0.8 else rs(random.randint(1,80))
        out.write(f"{int(free)}\t{s}\t{t}\t{int(a.score(s,t))}\n")
