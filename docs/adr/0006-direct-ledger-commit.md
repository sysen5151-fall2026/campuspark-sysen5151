# ADR-0006. Call the persistent capacity ledger directly

The booking route needs a single decision for the last place. ADR-0004 already chose SQLite. This decision covers how F.5 calls C.5.3. TA.1 uses a direct call. TA.2 sends each request to a worker and waits for the result.

The October prototype tested 30 bursts of 100 requests per option. Each burst had one place. Each option saved one record in all 30 bursts. The 95th-percentile call took 0.0035 ms directly and 2.2177 ms through the worker. These measurements cover the in-memory component only. The 24-week effort estimates were 12 and 22 staff hours. Weights of 0.625 for delay and 0.375 for effort gave values of 0.9531 and 0.8082. The effort estimates and weights are planning assumptions.

The selected direct path calls F.5.3. The SQLite store takes a write transaction before it reads the saved request and checks the busiest part of the requested period. It writes the confirmed row before it releases the transaction. A repeated request returns the saved booking. A full pool returns IO.22 and the driver receives IO.13. This guard implements RS.1.4.3 and RS.2.5.

A worker would also need a queue limit, a rule for waiting and retries, and a way to restart and drain the queue. Reopen the choice if direct effort exceeds 24.36 hours with queue effort held at 22 hours under the baseline weights. Check disk-backed latency again before setting any new service target.

Tests: tests/test_data_access.py checks two connections on the same file. tests/test_skeleton.py checks a full pool, a retry and a restart through POST /api/reserve. The component suite checks 100 final-place bursts.
