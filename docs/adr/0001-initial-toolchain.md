# ADR-0001: Initial toolchain

Status: Accepted (recorded on 2026-10-26 for a choice made on 2026-09-24)

Context: The walking skeleton needed a web API, a page for the driver, a test runner and automatic
checks on every push. The decision was made when the repository was created but never written down;
this record catches up so later records have something to number from.

Decision: Python with FastAPI and uvicorn for the API, a single static HTML page for the driver,
pytest for every test suite, and GitHub Actions for continuous integration. Python 3.12 in CI.

Consequences: Every function module is plain Python that can be tested without starting the server.
The page has no build step. The local development venv is Python 3.9, so generated code avoids
syntax newer than 3.9 (for example `X | None` at run time).

Model entities affected: none.
