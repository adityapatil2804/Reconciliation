"""
A small reference implementation of the reconciliation protocol described
in "Reconciling Independently-Maintained Symbolic World Models in
Multi-Agent Systems".

States are plain Python sets of positive predicate tuples under the
closed-world assumption standard in PDDL/STRIPS: a predicate not present
in a state is taken to be false. This is a minimal, dependency-free
implementation of the kitchen worked example; it does not use an
external PDDL planner, since the example only needs single-step
precondition checking and replanning-by-waiting. Extending this to a
general-purpose planner such as Fast Downward is left as future work
(see Discussion).
"""

from dataclasses import dataclass, field


@dataclass
class Action:
    name: str
    preconditions: set
    effects_add: set
    effects_del: set


@dataclass
class Agent:
    name: str
    state: set = field(default_factory=set)
    # provenance[predicate] = True once this agent has directly caused or
    # observed a change to that predicate's truth value.
    provenance: dict = field(default_factory=dict)

    def apply(self, action: Action):
        missing = [p for p in action.preconditions if p not in self.state]
        if missing:
            raise RuntimeError(
                f"{self.name} cannot execute {action.name}: missing preconditions {missing}"
            )
        for p in action.effects_del:
            self.state.discard(p)
            self.provenance[p] = True
        for p in action.effects_add:
            self.state.add(p)
            self.provenance[p] = True


def inconsistency_set(state_a: set, state_b: set, relevant: set):
    """Under closed-world semantics: p is in conflict if one state
    contains it and the other does not, restricted to `relevant`."""
    return {p for p in relevant if (p in state_a) != (p in state_b)}


def check_before_action(acting_agent: Agent, other_agent: Agent, action: Action):
    relevant = set(action.preconditions)
    return inconsistency_set(acting_agent.state, other_agent.state, relevant)


def resolve(acting_agent: Agent, other_agent: Agent, conflicts: set):
    """Whichever agent has direct provenance over a predicate wins;
    the other agent's belief is overwritten to match."""
    resolved = []
    for p in conflicts:
        if other_agent.provenance.get(p, False):
            if p in other_agent.state:
                acting_agent.state.add(p)
            else:
                acting_agent.state.discard(p)
            resolved.append((p, "resolved_in_favor_of", other_agent.name))
        elif acting_agent.provenance.get(p, False):
            resolved.append((p, "kept_by", acting_agent.name))
        else:
            resolved.append((p, "unresolved_no_provenance", None))
    return resolved


def run_kitchen_example():
    log = []

    stove_clear = ("clear", "stove")
    pot_on_table = ("on", "pot", "table")

    agent_c = Agent("Agent C (cook)", state={stove_clear, pot_on_table})
    agent_l = Agent("Agent L (cleaner)", state={stove_clear, pot_on_table})

    place_pot_on_stove = Action(
        name="place-pot-on-stove",
        preconditions={stove_clear, pot_on_table},
        effects_add={("on", "pot", "stove")},
        effects_del={pot_on_table, stove_clear},
    )
    pick_up_pot = Action(
        name="pick-up-pot",
        preconditions={pot_on_table},
        effects_add={("holding", "pot", "L")},
        effects_del={pot_on_table},
    )

    log.append("t=0: both agents' states match.")
    log.append(f"  S_C = {sorted(agent_c.state)}")
    log.append(f"  S_L = {sorted(agent_l.state)}")

    agent_l.apply(pick_up_pot)
    log.append("\nAgent L executes pick-up-pot (removes on(pot,table), adds holding(pot,L)).")
    log.append(f"  S_L (updated) = {sorted(agent_l.state)}")
    log.append(f"  S_C (stale)   = {sorted(agent_c.state)}")

    log.append("\n--- Without the protocol ---")
    agent_c_naive = Agent("Agent C (no check)", state=set(agent_c.state))
    agent_c_naive.apply(place_pot_on_stove)
    log.append(f"  Agent C executed place-pot-on-stove on its stale belief. "
               f"Resulting (incorrect) state: {sorted(agent_c_naive.state)}")
    log.append("  The pot is not physically on the stove; this state is fictional.")

    log.append("\n--- With the protocol ---")
    conflicts = check_before_action(agent_c, agent_l, place_pot_on_stove)
    log.append(f"  I(S_C, S_L) restricted to preconditions of place-pot-on-stove = {conflicts}")

    if conflicts:
        resolution = resolve(agent_c, agent_l, conflicts)
        log.append(f"  Resolution: {resolution}")
        log.append(f"  S_C (corrected) = {sorted(agent_c.state)}")
        missing = [p for p in place_pot_on_stove.preconditions if p not in agent_c.state]
        if missing:
            log.append(f"  Agent C cannot execute place-pot-on-stove: missing {missing}.")
            log.append("  Agent C replans (waits for pot_on_table to become true again).")
        else:
            log.append("  Agent C's plan is still valid; proceeding.")
    else:
        log.append("  No conflict found; Agent C proceeds as planned.")

    # Agent L puts the pot back down; Agent C's belief becomes valid again.
    put_down_pot = Action(
        name="put-down-pot",
        preconditions={("holding", "pot", "L")},
        effects_add={pot_on_table},
        effects_del={("holding", "pot", "L")},
    )
    agent_l.apply(put_down_pot)
    log.append("\nAgent L executes put-down-pot.")
    log.append(f"  S_L = {sorted(agent_l.state)}")

    conflicts2 = check_before_action(agent_c, agent_l, place_pot_on_stove)
    if conflicts2:
        resolve(agent_c, agent_l, conflicts2)
    log.append(f"  S_C (re-synced) = {sorted(agent_c.state)}")
    missing2 = [p for p in place_pot_on_stove.preconditions if p not in agent_c.state]
    if not missing2:
        agent_c.apply(place_pot_on_stove)
        log.append(f"  Agent C now executes place-pot-on-stove successfully: {sorted(agent_c.state)}")

    return "\n".join(log)


if __name__ == "__main__":
    print(run_kitchen_example())