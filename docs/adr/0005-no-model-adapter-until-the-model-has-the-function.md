# ADR-0005: No model adapter until the model has an AI function

Status: Accepted (2026-10-26)

Context: Chapter 8 of the Lab Manual asks for a model adapter that calls the product's language
model, and authorizes it only when the Innoslate model has an interface definition for that model.
Ours does not. AI parking help (SR.17, SR.18, system-wide requirement 2.1.7) has no use case, no
function and no asset yet; it is recorded as candidate function F.9 in the Chapter 6 and 7 report
and again in the Chapter 8 and 9 report. `docs/SPEC.md` already holds a proposed response contract
(one `message` field and a fixed fallback built from the approved record), but nothing in the model
calls for it.

Decision: Do not build the adapter in this increment. The gap is in the model, so it is fixed there
first: a use case step for AI help, a function F.9 with its ICOMs, an asset, and the interface to the
model as an external system. The adapter is built after that, from the SPEC response contract, with
the schema-violation path (missing reply, invalid JSON, wrong or blank `message`) going to the fixed
fallback and tested before the happy path.

Consequences: The Chapter 8 "Done When" item for the model is open, deliberately. No project data is
sent to any model. 2.3.2 Approved Language Model Use stays untested until the adapter exists.

Model entities affected: candidate F.9, 2.1.7, 2.3.2, SR.17, SR.18.
