from __future__ import annotations
from itertools import combinations
from typing import List, Dict, Tuple, FrozenSet, Union, Iterable, Optional
from collections import defaultdict

# -----------------------------
# I/O: leser lokale resultater
# -----------------------------

def read_local_scores(path: str) -> Dict[str, Dict[FrozenSet[str], float]]:
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    i = 0
    if lines:
        # Noen scorefiler starter med én linje med n=|V|, andre gjør ikke det.
        try:
            int(lines[0])
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

# -----------------------------
# Første Fase: Best-Parents DP
# -----------------------------

def GetBestParents(
    V: List[str],
    v: str,
    LS: Dict[str, Dict[FrozenSet[str], float]],
) -> Dict[FrozenSet[str], FrozenSet[str]]:
    """
    For hvert kandidatmengde C ⊆ V\{v}, returner foreldremengden P ⊆ C som maksimerer LS[v][P].
    Klassisk DP (dynamisk programmering) over delmengder:
       bss[C] = max_{Z ⊆ C} LS[v][Z]
       bps[C] = argmax_{Z ⊆ C} LS[v][Z]
    """
    cand = tuple(sorted(x for x in V if x != v))
    bps: Dict[FrozenSet[str], FrozenSet[str]] = {}
    bss: Dict[FrozenSet[str], float] = {}

    empty = frozenset()                   
    bps[empty] = empty
    bss[empty] = LS[v].get(empty, float("-inf"))

    for r in range(1, len(cand) + 1):
        for C in map(frozenset, combinations(cand, r)):
            best_set = C
            best_score = LS[v].get(C, float("-inf"))
            # DP: sjekk for  all  sub-subsets C\{x}
            for x in C:
                c1 = C - {x}
                s1 = bss.get(c1, float("-inf"))
                if s1 > best_score:
                    best_score = s1
                    best_set = bps.get(c1, empty)
            bps[C], bss[C] = best_set, best_score

    if frozenset() not in bps:
        bps[frozenset()] = frozenset()
    return bps

# -----------------------------
# Andre fase: classic (alle subsets)
# -----------------------------

def powersets_by_size(items: Iterable[str]):
    items = tuple(sorted(items))
    yield frozenset()
    for r in range(1, len(items) + 1):
        for comb in combinations(items, r):
            yield frozenset(comb)

def GetBestSinks(
    V: List[str],
    bps_all: Dict[str, Dict[FrozenSet[str], FrozenSet[str]]],
    LS: Dict[str, Dict[FrozenSet[str], float]]
) -> Tuple[Dict[FrozenSet[str], Optional[str]], Dict[FrozenSet[str], float]]:

    Vset = frozenset(V)
    sinks: Dict[FrozenSet[str], Optional[str]] = {frozenset(): None}
    scores: Dict[FrozenSet[str], float] = {frozenset(): 0.0}

    for W in powersets_by_size(Vset):
        if not W:
            continue
        best_score = float("-inf")
        best_sink: Optional[str] = None

        for sink in W:
            upvars = W - {sink}
            if upvars not in bps_all.get(sink, {}):
                bps_all[sink] = GetBestParents(V, sink, LS)

            base = scores[upvars]                          # beste score for mengden W uten sink
            parents = bps_all[sink][upvars]                # beste foreldre til sink blant upvars 
            local = LS[sink].get(parents, float("-inf"))   # lokal/hat score
            total = base + local

            if total > best_score:
                best_score = total
                best_sink = sink

        scores[W] = best_score
        sinks[W] = best_sink

    return sinks, scores

def Sink2ord(V: List[str], sinks: Dict[FrozenSet[str], Optional[str]]) -> List[str]:
    """
    Rekonstruerer en topologisk rekkefølge fra sinks-tabellen (klassisk eller PO-variant).
    Fyller ord fra høyre til venstre: siste valg av sink ender bakerst.
    """
    left = frozenset(V)
    n = len(V)
    ord_list: List[Optional[str]] = [None] * n

    for i in range(n - 1, -1, -1):
        s = sinks.get(left)
        if s is None:
            raise RuntimeError(f"fant ingen sink for delmengde {left}")
        ord_list[i] = s
        left = left - {s}

    return [x for x in ord_list if x is not None]

def Ord2net(
    V: List[str],
    order: List[str],
    bps_all: Dict[str, Dict[FrozenSet[str], FrozenSet[str]]],
) -> Dict[str, FrozenSet[str]]:
    if set(order) != set(V) or len(order) != len(V):
        raise ValueError("order må være en permutasjon av V")

    parents: Dict[str, FrozenSet[str]] = {}
    predecs: FrozenSet[str] = frozenset()

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

def getOptimalNetwork(data: Union[str, Dict[str, Dict[FrozenSet[str], float]]]):
    LS = read_local_scores(data) if isinstance(data, str) else data
    V = sorted(LS.keys())

    bps_all: Dict[str, Dict[FrozenSet[str], FrozenSet[str]]] = {
        v: GetBestParents(V, v, LS) for v in V
    }

    sinks, scores = GetBestSinks(V, bps_all, LS)
    order = Sink2ord(V, sinks)
    parents = Ord2net(V, order, bps_all)
    total = scores[frozenset(V)]
    return order, parents, total

# -----------------------------
# Partial Order approach
# -----------------------------

class PartialOrder:
    """
    Partial order P som presedenspar (x, y) som betyr x ≺ y.
Bygger bitmasker for forgjengere/etterfølgere og enumererer idealer.
"""
    def __init__(self, nodes: List[str], relations: List[Tuple[str, str]]):
        self.nodes = list(nodes)
        self.idx = {v: i for i, v in enumerate(self.nodes)}
        n = len(nodes)
        self.pred_mask = [0] * n
        self.succ_mask = [0] * n
        for x, y in relations:
            ix, iy = self.idx[x], self.idx[y]
            self.succ_mask[ix] |= (1 << iy)
            self.pred_mask[iy] |= (1 << ix)

    def is_ideal(self, Ymask: int) -> bool:
        # Y is an ideal iff for all v in Y, pred[v] ⊆ Y.
        n = len(self.nodes)
        for v in range(n):
            if (Ymask >> v) & 1:
                if self.pred_mask[v] & ~Ymask:
                    return False
        return True

    def maximal_in(self, Ymask: int) -> int:
        # Maximal elements in Y (no successor inside Y\{v})
        maxmask = 0
        for v in range(len(self.nodes)):
            if (Ymask >> v) & 1:
                if (self.succ_mask[v] & (Ymask ^ (1 << v))) == 0:
                    maxmask |= (1 << v)
        return maxmask

    def enumerate_ideals(self) -> List[int]:
        n = len(self.nodes)
        allmask = (1 << n) - 1
        ideals: List[int] = []

        def dfs(Ymask: int, avail: int):
            ideals.append(Ymask)
        
            can = 0
            for v in range(n):
                if (avail >> v) & 1 and (self.pred_mask[v] & ~Ymask) == 0:
                    can |= (1 << v)
            # branch by including addable elements, one by one
            while can:
                v = (can & -can).bit_length() - 1  # index of lowest set bit
                can &= can - 1
                dfs(Ymask | (1 << v), avail & ~(1 << v))

        dfs(0, allmask)
        ideals.sort(key=lambda m: m.bit_count())
        return ideals

def GetBestSinks_PO(
    V: List[str],
    bps_all: Dict[str, Dict[FrozenSet[str], FrozenSet[str]]],
    LS: Dict[str, Dict[FrozenSet[str], float]],
    P: PartialOrder
) -> Tuple[Dict[FrozenSet[str], Optional[str]], Dict[FrozenSet[str], float]]:

    n = len(V)
    var2idx = {v: i for i, v in enumerate(V)}
    idx2var = {i: v for v, i in var2idx.items()}

    ideals_masks = P.enumerate_ideals()  # includes 0, sorted by size

    sinks: Dict[FrozenSet[str], Optional[str]] = {frozenset(): None}
    scores: Dict[FrozenSet[str], float] = {frozenset(): 0.0}

    for Ymask in ideals_masks:
        if Ymask == 0:
            continue

        # Build set of variable names for dict keys
        W = frozenset(idx2var[i] for i in range(n) if (Ymask >> i) & 1)

        # Only maximal elements in Y can be sinks (v ∈ Yˇ)
        Yhat_mask = P.maximal_in(Ymask)

        best_score = float("-inf")
        best_sink: Optional[str] = None

        m = Yhat_mask
        while m:
            v = (m & -m).bit_length() - 1
            m &= m - 1

            sink = idx2var[v]
            upmask = Ymask & ~(1 << v)
            upvars = frozenset(idx2var[i] for i in range(n) if (upmask >> i) & 1)

            if upvars not in bps_all.get(sink, {}):
                bps_all[sink] = GetBestParents(V, sink, LS)

            base = scores[upvars]
            parents = bps_all[sink][upvars]
            local = LS[sink].get(parents, float("-inf"))
            total = base + local

            if total > best_score:
                best_score = total
                best_sink = sink

        scores[W] = best_score
        sinks[W] = best_sink

    return sinks, scores

def getOptimalNetwork_with_PO(
    data: Union[str, Dict[str, Dict[FrozenSet[str], float]]],
    relations: List[Tuple[str, str]]
):
    """
    Løs OBN begrenset til DAG-er som er kompatible med én delvis orden P gitt av «relations».
    """
    LS = read_local_scores(data) if isinstance(data, str) else data
    V = sorted(LS.keys())

    # Reuse simple full best-parents tables (correct; can later be sparsified)
    bps_all: Dict[str, Dict[FrozenSet[str], FrozenSet[str]]] = {
        v: GetBestParents(V, v, LS) for v in V
    }

    P = PartialOrder(V, relations)
    sinks, scores = GetBestSinks_PO(V, bps_all, LS, P)
    order = Sink2ord(V, sinks)
    parents = Ord2net(V, order, bps_all)
    total = scores[frozenset(V)]
    return order, parents, total

def getOptimalNetwork_with_POS_cover(
    data: Union[str, Dict[str, Dict[FrozenSet[str], float]]],
    posets: List[List[Tuple[str, str]]]
):
    """
   # Kjør PO-DP for hver partial-order i et POS-cover og returner den beste.
    """
    LS = read_local_scores(data) if isinstance(data, str) else data
    V = sorted(LS.keys())

    bps_all: Dict[str, Dict[FrozenSet[str], FrozenSet[str]]] = {
        v: GetBestParents(V, v, LS) for v in V
    }

    best: Optional[Tuple[List[str], Dict[str, FrozenSet[str]], float]] = None
    for rel in posets:
        P = PartialOrder(V, rel)
        sinks, scores = GetBestSinks_PO(V, bps_all, LS, P)
        order = Sink2ord(V, sinks)
        parents = Ord2net(V, order, bps_all)
        total = scores[frozenset(V)]
        if (best is None) or (total > best[2]):
            best = (order, parents, total)
    if best is None:
        raise RuntimeError("ingen partial orders gitt.")
    return best

# -----------------------------
# Demo / Entry point
# -----------------------------

if __name__ == "__main__":
    path = r"C:\\Users\\adhan\\OneDrive\Skrivebord\\Jobb\\pygobnilp\\asia.scores"

    # 1) Classic full DP
    order, parents, total = getOptimalNetwork(path)
    print("\n[Classic DP] Optimal rekkefølge:")
    print(order)
    print("\n[Classic DP] Foreldre pr. node:")
    for v in order:
        print(f"  {v}: {sorted(parents[v])}")
    print(f"\n[Classic DP] Total beste score: {total}")

    # 2) Partial Order approach til en poset
# Eksempel: 3-bøtte-poset: B1 ≺ B2 ≺ B3.
# Bytt disse ut med variabelnavnene fra score-filen.
# For en generell demo bygger vi bøtter fra den faktiske V etter innlesing:
    LS_demo = read_local_scores(path)
    V_demo = sorted(LS_demo.keys())
    if len(V_demo) >= 5:
        # del opp i ~3 bøtter
        k1 = len(V_demo) // 3
        k2 = (2 * len(V_demo)) // 3
        B1, B2, B3 = V_demo[:k1], V_demo[k1:k2], V_demo[k2:]
        relations = []
        for x in B1:
            for y in B2 + B3:
                relations.append((x, y))
        for x in B2:
            for y in B3:
                relations.append((x, y))

        order_po, parents_po, total_po = getOptimalNetwork_with_PO(path, relations)
        print("\n[PO DP] Optimal rekkefølge (given poset):")
        print(order_po)
        print("\n[PO DP] Foreldre pr. node:")
        for v in order_po:
            print(f"  {v}: {sorted(parents_po[v])}")
        print(f"\n[PO DP] Total beste score (poset-begrenset): {total_po}")

    