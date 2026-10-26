# Reservation Subsystem Specification

Component specification for C.5 Reservation Subsystem, kept in the Innoslate model as its own document
("Reservation Subsystem Specification", Chapter 9) and copied here so code sessions can read it. The model is
the authority; if the two differ, the model wins and this file is updated.

C.5 performs F.5 Recheck and Record Reservation. Its four components each perform one second-level function:

| Component | Performs | Description |
| --- | --- | --- |
| C.5.1 Booking Request Screener | F.5.1 Screen Reservation Request | Check that the reservation request has a request ID, a pool, the driver's identity reference and a valid booked period (end after start). A request that fails goes straight to the refusal function with the reason missing_data. |
| C.5.2 Booking Eligibility Checker | F.5.2 Recheck Booking Eligibility | Recheck the driver's permit result and the approved permit list, time rules and closures for the whole booked period. Unknown, missing, failed or invalid eligibility never counts as permission. |
| C.5.3 Capacity Ledger | F.5.3 Commit Capacity Hold | In one step, check that the pool has a free place for every minute of the booked period and save the reservation with its hold. A request ID that is already saved returns the saved reservation and adds no second hold. Publishes the saved records. |
| C.5.4 Refusal Notice Builder | F.5.4 Issue Booking Refusal | Turn a refusal reason into the notice the driver sees, stating the specific reason in plain words. No record is created and no capacity is held. |

Second-level flows: IO.20 Screened Booking Request (F.5.1 to F.5.2), IO.21 Eligible Booking Request
(F.5.2 to F.5.3), IO.22 Booking Refusal Reason (F.5.1, F.5.2 and F.5.3 to F.5.4). Shapes are in
`contracts/api-v1.yaml` version 1.1.

## 1 Functional Requirements

### RS.1.1 Input Requirements

**RS.1.1.1 Accept Reservation Request.** The Reservation Subsystem shall accept Reservation Request from the Campus Driver.  
Satisfied by: C.5, IO.7, F.5.1. Traced from: 1.1.5.  
Rationale: The booking request is the only thing that starts a commitment.  
Measure of performance: Requests accepted with every field intact (100%). Verification: Submit complete and incomplete requests through the web interface; complete ones reach F.5.1 unchanged.

**RS.1.1.2 Accept Identity and Permit Eligibility.** The Reservation Subsystem shall accept Identity and Permit Eligibility from the Campus Identity & Permit System.  
Satisfied by: C.5, IO.3, F.5.2. Traced from: 1.1.3.  
Rationale: The permit system, not CampusPark, decides who may park where.  
Measure of performance: Eligibility results used for the matching driver only (100%). Verification: Send eligible, denied, unknown, missing and failed results; only an eligible result for the same driver passes.

**RS.1.1.3 Accept Approved Parking Rules and Capacity.** The Reservation Subsystem shall accept Approved Parking Rules and Capacity from the Parking Control Subsystem.  
Satisfied by: C.5, IO.17, F.5.2, F.5.3. Traced from: 1.4.1.8.  
Rationale: Bookings must be decided under the same rule set every other subsystem uses.  
Measure of performance: Booking decisions made under the latest rule version (100%). Verification: Publish a new rule version and book; the decision follows the new version.

### RS.1.2 Output Requirements

**RS.1.2.1 Provide Confirmed Reservation Record.** The Reservation Subsystem shall provide Confirmed Reservation Record to the Confirmation Subsystem.  
Satisfied by: C.5, IO.8, F.5.3. Traced from: 1.4.1.5.  
Rationale: The confirmation can only be built from what was actually saved.  
Measure of performance: Confirmations that match a saved record (100%). Verification: Compare every confirmation in a test run with the saved records.

**RS.1.2.2 Provide Booking Refusal Notice.** The Reservation Subsystem shall provide Booking Refusal Notice to the Campus Driver.  
Satisfied by: C.5, IO.13, F.5.4. Traced from: 1.2.3.  
Rationale: A refused driver needs to know why, and nothing may be saved.  
Measure of performance: Refusals with a specific reason and no record (100%). Verification: Trigger each refusal reason; each gives its own notice and no saved record.

**RS.1.2.3 Provide Reservation Records.** The Reservation Subsystem shall provide Reservation Records to the Option Selection Subsystem and the Reporting Subsystem.  
Satisfied by: C.5, IO.18, F.5.3. Traced from: 1.4.1.11.  
Rationale: Options and reports are only right if they read the records the ledger saved.  
Measure of performance: Saved reservations missing from options or reports (0). Verification: After a test run, every saved reservation is counted by options and listed by reports.

### RS.1.3 External Interface Requirements

**RS.1.3.1 Driver Web Interface.** The Reservation Subsystem shall interface with the Campus Driver through the Driver Web Interface.  
Satisfied by: C.5, X.C.1, conduit: Driver Web Interface. Traced from: 1.3.2.  
Rationale: Booking requests and refusal notices travel over the driver's web interface.  
Measure of performance: Requests and notices carried without loss (100%). Verification: Book and get refused through the web page.

**RS.1.3.2 Permit Eligibility Data Link.** The Reservation Subsystem shall interface with the Campus Identity & Permit System through the Permit Eligibility Data Link.  
Satisfied by: C.5, X.C.3, conduit: Permit Eligibility Data Link. Traced from: 1.3.1.  
Rationale: The eligibility result used at commitment comes over this link.  
Measure of performance: Timeouts that end in a refusal (100%). Verification: Simulate a permit timeout during booking; the booking is refused.

**RS.1.3.3 Parking Control to Reservation.** The Reservation Subsystem shall interface with the Parking Control Subsystem through the Parking Control to Reservation link.  
Satisfied by: C.5, C.1, conduit: Parking Control to Reservation. Traced from: 1.4.1.8.  
Rationale: The approved rules and capacity arrive over this internal link.  
Measure of performance: Rule versions received in order (100%). Verification: Contract conformance test plus a rule-change booking test.

**RS.1.3.4 Reservation to Option Selection.** The Reservation Subsystem shall interface with the Option Selection Subsystem through the Reservation to Option Selection link.  
Satisfied by: C.5, C.4, conduit: Reservation to Option Selection. Traced from: 1.4.1.4.  
Rationale: Options need the places already held.  
Measure of performance: Options shown for a pool with no free place (0). Verification: Fill a pool, then search; the pool is not offered.

**RS.1.3.5 Reservation to Confirmation.** The Reservation Subsystem shall interface with the Confirmation Subsystem through the Reservation to Confirmation link.  
Satisfied by: C.5, C.6, conduit: Reservation to Confirmation. Traced from: 1.4.1.6.  
Rationale: Confirmed records reach the confirmation over this link.  
Measure of performance: Confirmed records delivered (100%). Verification: Book; the confirmation shows the saved reference.

**RS.1.3.6 Reservation to Reporting.** The Reservation Subsystem shall interface with the Reporting Subsystem through the Reservation to Reporting link.  
Satisfied by: C.5, C.7, conduit: Reservation to Reporting. Traced from: 1.4.1.7.  
Rationale: Reports and affected-booking lists read the saved records over this link.  
Measure of performance: Saved records missing from reports (0). Verification: Close a pool after bookings; every overlapping reservation is listed.

### RS.1.4 Function Requirements

**RS.1.4.1 Screen Reservation Request.** The Reservation Subsystem shall screen each reservation request for a request ID, a pool, the driver's identity reference and a booked period that ends after it starts.  
Satisfied by: C.5, C.5.1, F.5.1. Traced from: 1.4.1.5.  
Rationale: Nothing should be read or held for a request that cannot be decided (SR.15).  
Measure of performance: Incomplete requests that reach the eligibility check (0). Verification: Send requests missing each field in turn; each is refused with missing_data before any rule is read.

**RS.1.4.2 Recheck Booking Eligibility.** The Reservation Subsystem shall recheck the driver's permit result and the approved permit list, time rules and closures for the whole booked period.  
Satisfied by: C.5, C.5.2, F.5.2. Traced from: 1.4.1.5.  
Rationale: Rules can change between the search and the commitment (SR.2).  
Measure of performance: Bookings confirmed that break a permit, time rule or closure (0). Verification: A permit-rule test table including periods that cross a closure.

**RS.1.4.3 Commit Capacity Hold.** The Reservation Subsystem shall check capacity and save the reservation with its capacity hold in one step, and shall return the saved reservation for a request ID it has already saved.  
Satisfied by: C.5, C.5.3, F.5.3. Traced from: 1.4.1.5, 1.4.1.11.  
Rationale: Checking and saving separately lets two drivers take the last place (SR.4).  
Measure of performance: Overbookings in 100 rounds of 100 concurrent requests (0). Verification: Concurrency test on the last free place, plus a repeated request ID.

**RS.1.4.4 Issue Booking Refusal.** The Reservation Subsystem shall issue a booking refusal notice that states the specific reason whenever a request is refused.  
Satisfied by: C.5, C.5.4, F.5.4. Traced from: 1.2.3.  
Rationale: A refusal without a reason sends the driver back to guessing (SR.15).  
Measure of performance: Refusal notices without a specific reason (0). Verification: Trigger missing_data, not_eligible, closed and pool_full; each notice names its reason.

## 2 System-wide Requirements

**RS.2.1 Limited Personal Data.** The Reservation Subsystem shall store only the reservation ID, request ID, identity reference, pool, booked period and status for each reservation.  
Flowed down from 2.1.3 by equivalence. Satisfied by: C.5.  
Rationale: The system rule applies unchanged: the Reservation Subsystem is the main store of driver data, so it inherits the approved field list as it is. The list here is the SPEC's proposed closed booking record.  
Verification: Schema inspection and an export of a test run show no other field.

**RS.2.2 Timely Parking Controls.** The Reservation Subsystem shall apply a newly published rule set to every booking attempt it receives more than 10 seconds after publication.  
Flowed down from 2.1.5 by apportionment. Satisfied by: C.5.  
Rationale: The 60 s system budget is split across the chain: Parking Control publishes within 10 s, the Reservation Subsystem picks the new set up within 10 s, Reporting lists affected bookings within 30 s, and 10 s is held in reserve. The same unit (seconds) is kept at every level.  
Verification: Publish a closure, then book the closed pool 10 s later; the booking is refused.

**RS.2.3 Safe Handling of Source Failures.** The Reservation Subsystem shall refuse confirmation whenever the eligibility or capacity data for any part of the booked period are missing, failed or unknown.  
Flowed down from 2.1.6 by equivalence. Satisfied by: C.5.  
Rationale: The refusal half of the system rule happens entirely inside this subsystem, so it is carried down word for word. The route-failure half belongs to the Confirmation Subsystem and is not repeated here.  
Verification: Fault injection on eligibility and capacity during booking; every case is refused with no record.

**RS.2.4 Booking Response Time.** The Reservation Subsystem shall return a confirmed record or a refusal within 2 seconds for at least 95% of booking attempts.  
Flowed down from 2.1.8 by apportionment. Satisfied by: C.5.  
Rationale: Of the 5 s system budget, 1.5 s goes to the browser and network, 2 s to the Reservation Subsystem, 1 s to the Confirmation Subsystem, and 0.5 s is reserve. The Reservation Subsystem gets the largest share because it does the recheck and the write.  
Verification: Timed booking calls against the subsystem; 95th percentile 2 s or less.

**RS.2.5 Capacity Safety Under Concurrent Use.** The Reservation Subsystem shall serialize capacity holds for each pool so that the holds for any minute never exceed the approved capacity, and shall keep at most one reservation per request ID, with at least 100 requests arriving at once.  
Flowed down from 2.1.9 by synthesis. Satisfied by: C.5.  
Rationale: The system rule (never overbook) does not say how. It is met by combining three design properties that together give the outcome: holds serialized per pool, check and save in one step, and request IDs that make repeats harmless. None of the three alone meets the system rule.  
Verification: 100 rounds of 100 simultaneous requests for the last place, plus repeated request IDs; exactly one confirmation per round and no duplicates.

**RS.2.6 Internal Interface Contract.** The Reservation Subsystem shall accept and produce IO.7, IO.3, IO.17, IO.8, IO.13 and IO.18 only in the forms defined by the internal interface contract, version 1.  
Flowed down from 2.4.2 by equivalence. Satisfied by: C.5.  
Rationale: Every subsystem is bound by the same contract; for this subsystem the rule is narrowed to the six flows it touches.  
Verification: Contract conformance test in continuous integration.

**RS.2.7 Accessible Refusal Notices.** The Reservation Subsystem shall word every booking refusal notice as plain text of no more than two sentences that names the reason without relying on color or layout.  
Flowed down from 2.1.2 by synthesis. Satisfied by: C.5.  
Rationale: The accessible main flow is a system outcome. This subsystem's share of it is a refusal notice a screen reader can read on its own; the keyboard and page structure belong to the web interface.  
Verification: Screen-reader walkthrough of every refusal reason.

