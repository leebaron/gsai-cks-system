---------------------------- MODULE Invariants ----------------------------
(* Invariant definitions for the Consensus CI system.
These are checked by verify_model.py in the absence of TLC. *)

EXTENDS ConsensusSystem

(* Prove: no COMMIT with invalid execution *)
INVARIANT Safety

(* Prove: type safety across all states *)
INVARIANT TypeSafety

(* Prove: consistent hashes when COMMIT is reached *)
INVARIANT Consistency
=====================================================================