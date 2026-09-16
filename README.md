# Reconciliation

Reference implementation accompanying the paper *"Reconciling Independently-Maintained Symbolic World Models in Multi-Agent Systems"* (Patil, Chitnis, & Mahalle).

## What this is

A minimal, dependency-free implementation of the paper's kitchen worked example: two agents (a cooking robot and a cleaning robot) each maintain their own symbolic (PDDL-style) belief about a shared environment. One agent's action makes the other's belief stale. This code demonstrates the paper's reconciliation protocol catching and correcting that stale belief before it causes an unsafe action.

## Contents

- `reconciliation.py` — the full implementation: `Agent` and `Action` classes, `inconsistency_set()` (Section 3), `check_before_action()` and `resolve()` (Section 4), and a runnable version of the kitchen scenario (Section 5).

## Running it

No dependencies beyond the Python standard library.

```bash
python3 reconciliation.py
```

This prints a trace showing:
1. Both agents' states matching at t = 0
2. Agent L's action making Agent C's belief stale
3. What happens *without* the protocol (an unsafe action succeeds silently on a false belief)
4. What happens *with* the protocol (the conflict is detected, resolved via the provenance/entrenchment rule, and Agent C correctly replans)

## Paper

See the paper for the full formalization, the protocol's theoretical grounding in Katsuno-Mendelzon update semantics, and a discussion of the approach's current limitations.
