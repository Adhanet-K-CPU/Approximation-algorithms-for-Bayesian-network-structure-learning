from __future__ import annotations
from itertools import combinations
from typing import List, Dict, Tuple, FrozenSet, Union, Iterable, Optional

#V: alle variabler (noder) i nettverket
#v: den noden vo skal finne de beste foreldren til
#LS: inneholder lokale score

def read_local_scores(path: str) -> Dict[str, Dict[FrozenSet[str], float]]:
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    i = 0
    if lines:
        try:
            int(lines[0])  # f.eks. "8"
            i = 1
        except ValueError:
            i = 0

    LS: Dict[str, Dict[FrozenSet[str], float]] = {}
    n = len(lines)
    while i < n:
        head = lines[i].split()
        if len(head) != 2:
            raise ValueError(f"Dårlig header på linje {i+1}: {lines[i]}")
        var, cnt_str = head
        try:
            count = int(cnt_str)
        except ValueError:
            raise ValueError(f"Dårlig count på linje {i+1}: {lines[i]}")
        i += 1

        LS[var] = {}
        for _ in range(count):
            if i >= n:
                raise ValueError(f"Uventet slutt mens vi leste blokken for {var}")
            parts = lines[i].split()
            i += 1
            if len(parts) < 2:
                raise ValueError(f"Dårlig scorerekke for {var}: {lines[i-1]}")

            score = float(parts[0])
            k = int(parts[1])
            if len(parts) != 2 + k:
                raise ValueError(f"For {var}: forventet {k} foreldre, fikk {len(parts)-2}: {parts}")
            parents = frozenset(parts[2:])  # tom når k == 0
            LS[var][parents] = score

    return LS

def GetBestParents(
    V: List[str],
    v: str,
    LS: Dict[str, Dict[FrozenSet[str], float]],) -> Dict[FrozenSet[str], FrozenSet[str]]:
    """bps, bss = {}, {} #bps (best parent set), bss ("best subset scores"): lagrer scorene til bps
    supp = set() # Lagrer tomt mengdeobject 
    for ps in LS[v]: # Går gjennom alle foreldresett som har en definert scor for v
        supp |= ps """
    cand = tuple(sorted(x for x in V if x != v))
    bps: Dict[FrozenSet[str], FrozenSet[str]] = {}
    bss: Dict[FrozenSet[str], float] = {} # Lagrer kandiadt variableene som er sortert tuppel (leksikografisk rekkkefølge)

    empty = frozenset # representerer det tomme foreldresettet som en frossen mengde, fordi vannlige mengder ikke kan brukes som nøkler i en ordbok
    bss[empty] = empty # tomme mengde = beste delmengden også tom
    bps[empty] = LS[v].get(empty, float("-inf")) # Setter scorene for det tomme foreldresettet, (inf) = ugyldig

    for r in range(1, len(cand) + 1): # Går gjennom alle mulige størrelser på kandidat mengder
        for C in map(frozenset, combinations(cand,r)): #Lagrer alle kombinasjoner (delmengder) av kandidat variablen av størekse r
            best_set = C
            best_score = LS[v].get(C, float("-inf")) # Starter med å anta at den beste løsningen for C er selve C, og bruker dens score. 
            #DP
            for x in C:
                c1 = C - {x}
                s1 = bss.get(c1, float("-inf"))
                if s1 > best_score:
                    best_score= s1
                    best_set = bps.get(c1,empty)
            bps[C], bss[C] = best_set, best_score
    if frozenset() not in bps:
        bps[frozenset()] = frozenset()
    return bps # bps (returere med beste foreldre-sett) og bss( returenere scorene )


"""
V: List av alle variabler
bps_all: dict for hver node s: bps_all[s][C] = beste foreldre for s gitt kandidater C
Ls: lokale scorer: LS[s][parents] -> float

sinks[w]: hvilken sink (node uten barn i W) som er best å velge i mengde W
score[W]: total beste nettverkscore for w

"""
def powersets_by_size(items: Iterable[str]):
    items = tuple(sorted(items))
    yield frozenset()
    for r in range(1, len(items) + 1):
        for comb in combinations(items,r):
            yield frozenset(comb)

def GetBestSinks(
    V: List[str],
    bps_all: Dict[str, Dict[FrozenSet[str], FrozenSet[str]]],
    LS: Dict[str, Dict[FrozenSet[str], float]]
) -> Tuple[Dict[FrozenSet[str], Optional[str]], Dict[FrozenSet[str], float]]:
    
    Vset = frozenset(V)
    sinks: Dict[FrozenSet[str], Optional[str]] = {frozenset(): None}
    scores: Dict[FrozenSet[str], float] = {frozenset(): 0.0}

#Base: tom mengde har score og ingen sink 
   # sinks[frozenset()] = None
    #scores[frozenset()] = 0.0

#økende delmengdestørrelse (leksigorafisk)
    for W in powersets_by_size(Vset):
        if not W: 
            continue #allerede håndtert
        best_score = float("-inf")
        best_sink: Optional[str] = None

        for sink in W:
            upvars = W - {sink} # W \ {sink}
            if upvars not in bps_all.get(sink, {}):
                bps_all[sink] = GetBestParents(V, sink, LS)
            base = scores[upvars] #score for beste nettverk på W uten sink
            parents = bps_all[sink][upvars] # beste foreldre for sink blant upvars
            local = LS[sink].get(parents, float("-inf"))
            skore = base + local  # total score hvis 'sink' er sink i W

            if skore > best_score:
                best_score = skore
                best_sink = sink
    
        scores[W] = best_score
        sinks[W] = best_sink

    return sinks, scores

def Sink2ord(V: List[str], sinks: Dict[FrozenSet[str], Optional[str]]) -> List[str]:
    """
    Lager en topologisk rekkefølge fra sinks-tabellebe 
    ord[i] fylles fra i=|V|-1 ned til 0 ( siste plass = første valgte sink)
    Returnerer ordning fra kilder 
    """
    left = frozenset(V)
    n = len(V)
    ord_list: List[Optional[str]] = [None] *n

    for i in range(n -1, -1, -1):
        s = sinks.get(left)
        if s is None:
            raise RuntimeError(f"fant ingen sink for delmengde {left}")
        
        ord_list[i] = s
        left = left - {s}

    return [x for x in ord_list if x is not None] # topologisk rekkefølge

def Ord2net(
    V: List[str], 
    order: List[str], 
    bps_all: Dict[str, Dict[FrozenSet[str], FrozenSet[str]]],
) -> Dict[str, FrozenSet[str]]:
    
    """
    V: alle variabler
    order: permutasjon av V ( topologisk rekkefølge)
    bps_all[v][C]: beste foreldre for v når kandidater er C (C ⊆ V\{v})
    retunerer:
        parents[v]: foreldre-mengden for hver node v
    """

    if set(order) != set(V) or len(order) != len(V):
        raise ValueError("order må være en permutasjon av V")
    
    parents: Dict[str, FrozenSet[str]] = {}
    predecs: FrozenSet[str] = frozenset() # Ø

    #for i = 1..|V|: parents[i] = bps[order[i]][predecs]; predec <- predecs U {order[i]}

    for v in order:
        try: 
            p = bps_all[v][predecs]
        except KeyError:
            raise KeyError(
                f"bps_all mangler oppslag for node {v} og predecs {sorted(predecs)}"
            )
        parents[v] = p 
        predecs = predecs | {v}
    return parents

def getOptimalNetwork(data: Union[str, Dict[str,Dict[FrozenSet[str], float]]]):
    LS = read_local_scores(data) if isinstance(data, str) else data
    V = sorted(LS.keys())

    bps_all: Dict[str, Dict[FrozenSet[str], FrozenSet[str]]] = {
        v: GetBestParents(V,v, LS) for v in V
    }

    sinks, scores = GetBestSinks(V, bps_all, LS)

    order = Sink2ord(V, sinks)
    
    parents = Ord2net(V, order, bps_all)
    total = scores[frozenset(V)]

   
    return order, parents, total

if __name__ == "__main__":
    
    path = r"C:\Users\adhan\OneDrive\Skrivebord\Jobb\pygobnilp\asia.scores"



    order, parents, total = getOptimalNetwork(path)

    print("\nOptimal rekkefølge:")
    print(order)
    print("\nForeldre pr. node:")
    for v in order:
        print(f"  {v}: {sorted(parents[v])}")
    print(f"\nTotal beste score: {total}")
