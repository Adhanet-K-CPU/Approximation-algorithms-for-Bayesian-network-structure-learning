

# Bayesian Network Structure Learning with Dynamic Programming

This project implements algorithms for **exact Bayesian network structure learning** using dynamic programming.

The goal is to find the **optimal Bayesian network structure** given precomputed local scores for each variable and possible parent sets.
Implementations of Bayesian network (BN) structure learning algorithms using dynamic programming.

This was developed as part of my work as a research assistant at University of Bergen (UiB)- Machine Learning Department. 
The project explores exact Bayesian network structure learning and includes implementations of the classic dynamic programming algorithm as well as a partial-order based approach for reducing the search space when learning optimal Bayesian networks.

The implementation is based on ideas from:

- **Silander & Myllymäki (2006)** – dynamic programming for optimal Bayesian networks  
- **Parviainen & Koivisto (2013)** – partial order based dynamic programming  

The project was mainly an exploration of how exact structure learning algorithms work and how the search space can be reduced using **partial orders**.

---

# What the Project Does

The project contains three main components.

## 1. Classic Dynamic Programming

A classic DP algorithm that searches over **all subsets of variables**.

Main steps:

1. Compute the best parent set for each node.
2. Use dynamic programming to find the best sink node for each subset.
3. Reconstruct the optimal node ordering.
4. Build the optimal Bayesian network.

**Functions used:**

- `GetBestParents`
- `GetBestSinks`
- `Sink2ord`
- `Ord2net`
- `getOptimalNetwork`

---

## 2. Partial Order Dynamic Programming

To reduce the search space, the algorithm can restrict the search to DAGs that respect a **partial order**.

Instead of enumerating all subsets, the algorithm only considers **ideals of the partial order**.

**Main components:**

- `PartialOrder`
- `GetBestSinks_PO`
- `getOptimalNetwork_with_PO`

---

## 3. POS Cover Approach

The algorithm can also run the partial-order DP on **multiple partial orders** and select the best result.

**Function:**

- `getOptimalNetwork_with_POS_cover`

---

# Local Score Generation

The local scores used in this project were generated using **pygobnilp**, a Python implementation of the GOBNILP system by **James Cussens**.

Repository:

https://bitbucket.org/jamescussens/pygobnilp

`pygobnilp` computes local scores (such as **BDeu** or **BIC**) from data, which are then used as input for the dynamic programming algorithms.

---

# Workflow

The workflow used in this project:
Dataset
↓
pygobnilp (compute local scores)
↓
score file
↓
Dynamic programming algorithm (this project)
↓
Optimal Bayesian Network


---

# Example Usage

Example using a score file:

```python
order, parents, total = getOptimalNetwork("asia.scores")

print(order)
print(parents)
print(total)
