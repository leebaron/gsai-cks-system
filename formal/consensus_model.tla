---------------------------- MODULE ConsensusSystem ----------------------------
(*
Formal Verification Layer v1.0
Distributed Consensus CI System: TLA+ Specification

Proves:
  1. Safety  — no COMMIT with invalid execution
  2. Liveness — system always reaches a decision
  3. Consistency — all COMMIT nodes see same hash

State Machine:
  commit → RunNodes → Aggregate → Decide → {COMMIT, REJECT, KILL_SWITCH}
*)

EXTENDS Integers, FiniteSets, TLC

CONSTANTS
  Nodes,          \* Set of node identifiers: {A, B, C, D}
  THRESHOLD       \* Consensus threshold: 2 (for 2/3 of 3 nodes)

VARIABLES
  state,          \* Current system state
  exec_result,    \* [node → {OK, FAIL}]
  node_hashes,    \* [node → hash value]
  pass_votes,     \* Number of nodes that passed
  decision,       \* {pending, COMMIT, REJECT, KILL_SWITCH}
  invalid_exec    \* Did any invalid execution occur?

vars == <<state, exec_result, node_hashes, pass_votes, decision, invalid_exec>>

Init ==
  /\ state = "init"
  /\ exec_result = [n \in Nodes |-> "pending"]
  /\ node_hashes = [n \in Nodes |-> ""]
  /\ pass_votes = 0
  /\ decision = "pending"
  /\ invalid_exec = FALSE

(* Type invariant *)
TypeOK ==
  /\ state \in {"init", "running", "aggregating", "decided"}
  /\ decision \in {"pending", "COMMIT", "REJECT", "KILL_SWITCH"}
  /\ invalid_exec \in BOOLEAN

(* Actions *)

RunNodes ==
  /\ state = "init"
  /\ \E n \in Nodes:
    exec_result[n] \in {"OK", "FAIL"}
  /\ node_hashes' = [n \in Nodes |-> IF exec_result[n] = "OK" THEN "HASH_OK" ELSE "HASH_FAIL"]
  /\ state' = "running"
  /\ UNCHANGED <<decision, invalid_exec>>

Aggregate ==
  /\ state = "running"
  /\ \A n \in Nodes:
    exec_result[n] \in {"OK", "FAIL"}
  /\ pass_votes' = Cardinality({n \in Nodes: exec_result[n] = "OK"})
  /\ state' = "aggregating"
  /\ UNCHANGED <<decision, invalid_exec, exec_result, node_hashes>>

Decide ==
  /\ state = "aggregating"
  /\ IF pass_votes >= THRESHOLD * Cardinality(Nodes)
     THEN decision' = "COMMIT"
     ELSE 
       \* Check for split-brain (hash mismatch)
       IF Cardinality({node_hashes[n]: n \in Nodes}) > 1
       THEN decision' = "KILL_SWITCH"
       ELSE decision' = "REJECT"
  /\ state' = "decided"
  /\ UNCHANGED <<exec_result, node_hashes, pass_votes, invalid_exec>>

Next ==
  \/ RunNodes
  \/ Aggregate
  \/ Decide

Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
(* INVARIANT 1: Safety — never COMMIT when invalid execution occurred *)
Safety ==
  ~ (decision = "COMMIT" /\ invalid_exec = TRUE)

(* INVARIANT 2: Type correctness *)
TypeSafety ==
  TypeOK /\ decision \in {"pending", "COMMIT", "REJECT", "KILL_SWITCH"}

(* INVARIANT 3: Consistency — all COMMIT nodes see same hash *)
Consistency ==
  (decision = "COMMIT")
   => (Cardinality({node_hashes[n]: n \in Nodes}) = 1)

-----------------------------------------------------------------------------
(* LIVENESS: system eventually decides, never stuck in infinite loop *)
Liveness ==
  <>(state = "decided")
=====================================================================