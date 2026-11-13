# CampusPark product risk register

Team 25 confirmed all five baseline ratings on November 12, 2026. The four inputs are likelihood, cost, schedule and technical impact. The largest impact sets the overall impact. Likelihood times overall impact sets the score. See Innoslate project 13360, RK.0 and the EV.0 risk diagram.

| Model | Inputs | Score | Failure and affected boundary | Control or release check |
|---|---|---:|---|---|
| RK.1 | 4/2/3/5 | 20 | Two bookings share the final place. F.5.3 receives IO.21 and creates IO.8. | The direct SQLite guard checks and saves in one transaction. A refusal saves no row. Test competing connections, repeated requests and restarts. |
| RK.2 | 3/2/3/4 | 12 | Old rules or permits authorize a booking. F.5.2 reads IO.3 and IO.17. | Recheck the driver, permit, time window and current rules at booking. Block release if an invalid booking is saved. |
| RK.3 | 4/2/3/4 | 16 | A future assistant gives valid-looking advice that conflicts with the confirmed record. C.6 and SR.17. | Before enabling AI, compare protected facts with IO.8. Show the saved record when the facts differ. Check response schema changes with a fixed set of replies. |
| RK.4 | 3/2/3/3 | 9 | A permit, route or future model service is too slow or unavailable. C.3 and 2.1.6. | A missing permit blocks booking. A missing route leaves the booking intact. Check time limits and monitor support for dependencies. Review, replace or pin an abandoned dependency before release. |
| RK.5 | 3/4/4/5 | 15 | Untrusted source text reaches a future prompt, or driver data leaves the approved boundary. C.5, RS.2.1 and 2.1.3. | Keep permit and booking decisions in code. Before adding AI, allow only approved fields and destinations. Check the data sent by each adapter using synthetic records. |

RK.1 has the highest score. The team chose prevention because two confirmations for one place would give two drivers incompatible promises. Review the invariant at design review and on changes to F.5 or the database. Before release, run 100 bursts of 100 distinct requests for the last place, test replay after restart and inspect each round. Block release for an extra saved row, incorrect refusal or duplicate ID. Attach failed runs to RK.1 and INT.1, fix the cause and rerun the affected checks. A lower residual rating needs a new team review.

AI parking help remains deferred under ADR-0005. The AI-specific controls above are planned release checks. This register does not claim an AI feature or an AI test pass.
