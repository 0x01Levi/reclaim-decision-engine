# RECLAIM

### A Deterministic Revenue-Recovery Decision Engine

RECLAIM is a decision-engineering project for evaluating **whether a revenue-recovery intervention is economically worth taking**.

Instead of optimizing for the number of retries or the percentage of failed payments touched, RECLAIM models the expected economic outcome of each intervention and can decide:

> **ACT · WAIT · DO_NOTHING · ESCALATE**

The project combines probability, expected value, policy constraints, simulation, batch evaluation, and auditable decision-making into a single deterministic system.

---

## Why RECLAIM?

A failed payment does not automatically mean that another intervention is useful.

A retry may recover money, but it may also:

- cost money to execute
- produce little chance of recovery
- duplicate an action
- annoy a customer
- violate a cooldown or policy
- generate less value than doing nothing

RECLAIM therefore treats revenue recovery as an **economic decision problem** rather than a simple retry problem.

A simplified form of the objective is:

```text
Expected Net Value
=
P(recovery) × recoverable amount
− intervention cost
− expected downside
The system then applies deterministic policy constraints before allowing an intervention.

Core Pipeline
Revenue Event
      │
      ▼
Revenue at Risk
      │
      ▼
Economic Analysis
      │
      ▼
Policy Evaluation
      │
      ▼
┌─────┼─────────┬────────────┐
│     │         │            │
▼     ▼         ▼            ▼
ACT  WAIT  DO_NOTHING   ESCALATE
│
▼
Intervention
│
▼
Observed Outcome
│
▼
Batch Evaluation
│
▼
Audit Trail
Design Principles
1. Optimize value, not activity

A recovery system should not be rewarded simply for performing more interventions.

RECLAIM evaluates whether an intervention is expected to create net economic value.

2. Deterministic money handling

All authoritative monetary calculations use Decimal rather than binary floating-point arithmetic.

This applies to:

transaction amounts
intervention costs
expected recovery values
downside estimates
ROI
recovered revenue
3. Policy beats recommendations

The decision layer is intentionally designed so that a recommendation cannot bypass deterministic safety rules.

Conceptually:

Recommendation
      │
      ▼
Policy Engine
      │
 ┌────┼─────────┐
 ▼    ▼         ▼
ALLOW REJECT   ESCALATE

The policy engine can enforce constraints such as:

confidence thresholds
intervention limits
cooldown periods
amount limits
cost ratios
stopping rules
economic viability
duplicate-action protection
4. "DO NOTHING" is a real decision

A recovery system should be capable of deciding that intervention is not worthwhile.

For example:

Expected recovery:      ₹120
Intervention cost:       ₹35
Expected downside:       ₹95

Decision:
DO_NOTHING

Doing nothing can be the correct economic decision.

5. Auditability

Every important decision can be traced through an audit trail.

Audit records support:

entity IDs
merchant IDs
timestamps
correlation IDs
causation IDs
decision information
intervention information
outcomes

The objective is to make it possible to answer:

What happened?

Why was the decision made?

What action was taken?

What happened afterward?

Architecture
src/
├── domain/
│   ├── enums.py
│   ├── models.py
│   └── money.py
│
├── decision/
│   ├── economic_engine.py
│   ├── engine.py
│   └── policy_engine.py
│
├── simulator/
│   ├── generator.py
│   └── simulator.py
│
├── evaluation/
│   └── metrics.py
│
├── audit/
│   └── store.py
│
├── api/
│   └── main.py
│
└── config/
    └── __init__.py

tests/
data/
docs/
Component overview
Component	Purpose
domain	Core entities and strongly typed state
decision	Economic calculations and policy-driven decisions
simulator	Reproducible synthetic revenue scenarios
evaluation	Batch-level economic metrics
audit	Persistent decision and event history
api	Minimal FastAPI interface
tests	Behavioral and edge-case testing
Decision Engine

The decision engine combines an economic model with deterministic policy enforcement.

A simplified flow is:

Inputs
  │
  ├── recoverable amount
  ├── recovery probability
  ├── intervention cost
  ├── downside probability
  ├── downside amount
  └── policy state
          │
          ▼
   Expected Net Value
          │
          ▼
    Policy Evaluation
          │
          ▼
      Final Decision

Possible final states:

ACT
WAIT
DO_NOTHING
ESCALATE

The final decision is not simply the output of a mathematical formula; policy constraints can override an otherwise attractive intervention.

Synthetic Revenue Simulation

RECLAIM includes a reproducible synthetic data generator designed to model multiple recovery scenarios.

Current scenarios include:

transient payment failure
insufficient funds
repeated failure
customer action required
natural recovery
unrecoverable payment
intervention fatigue
escalation cases

The simulator is deterministic when supplied with a fixed seed, making experiments reproducible.

Example:

generator = SyntheticDataGenerator(seed=42)
events = generator.generate(...)

This allows experiments to be repeated against the same underlying data.

Evaluation

RECLAIM evaluates recovery strategies over batches, rather than relying on individual cherry-picked examples.

Current metrics include:

total revenue at risk
recovered revenue
intervention cost
net recovered value
recovery rate
intervention rate
baseline recovery
incremental recovered value
ROI

A simplified comparison looks like:

                 Baseline       RECLAIM
                ----------      --------
Revenue risk       ₹X             ₹X
Recovered          ₹A             ₹B
Cost               ₹0             ₹C
Net value          ₹A             ₹B-C

Incremental value:
(B - C) - A

The current baseline implementation is intentionally simple and should not be interpreted as a causal estimate.

Current Status
Implemented
Decimal-based monetary model
Core revenue and customer domain models
Explicit decision states
Expected-value economic engine
Deterministic policy engine
Intervention state transitions
Idempotency protection
Synthetic scenario generation
Reproducible simulation
Batch evaluation metrics
Baseline comparison
SQLite audit storage
Correlation and causation tracking
Minimal FastAPI application
Comprehensive automated tests
Test status
96 tests passing
What This Project Is Not

RECLAIM is currently not:

a production payment processor
a live money-transfer system
a production fraud detector
a real-time merchant platform
a causal inference framework
an autonomous financial agent

The current implementation is a deterministic foundation for experimenting with revenue-recovery decision systems.

Roadmap

The project is intentionally designed to evolve in layers.

Phase 1 — Probabilistic / AI Decision Layer

Potential future work:

failure-context classification
recovery probability estimation
intervention recommendation
structured model outputs
confidence calibration
model evaluation

The deterministic economic and policy layers should remain authoritative.

Phase 2 — Event Integration

Potential future work:

event ingestion
webhook handling
Razorpay Test Mode integration
intervention execution
customer notification workflows
idempotent external actions
Phase 3 — Advanced Evaluation

Potential future work:

stronger counterfactual baselines
controlled experiments
causal analysis
larger simulations
sensitivity analysis
calibration analysis
Phase 4 — Interface

Potential future work:

merchant dashboard
decision inspection
recovery analytics
audit explorer
escalation monitoring
Installation

Clone the repository and create a virtual environment:

git clone <repository-url>
cd reclaim-decision-engine

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
Running Tests

Run the complete test suite:

pytest

Run with verbose output:

pytest -v

Run a specific test module:

pytest tests/test_money.py -v
Running the API

Start the development server:

python main.py

or:

uvicorn src.api:app --reload

Health check:

GET /health

Interactive API documentation:

/docs
Project Philosophy

RECLAIM is built around a simple principle:

A good automated decision is not the one that acts the most. It is the one that creates the most value while respecting its constraints.

That means the system must be able to justify all four outcomes:

ACT
WAIT
DO_NOTHING
ESCALATE

The long-term goal is to combine probabilistic reasoning with deterministic economic and policy controls without allowing opaque model output to become the authority over financial state.

Research / Learning Areas

This project serves as a practical exploration of:

decision theory
expected value
probability
optimization
simulation
economic modeling
policy engines
state machines
idempotency
reproducible experiments
evaluation methodology
auditability
AI-assisted decision systems

The project is intentionally structured so that the mathematical and deterministic components remain useful independently of any future AI integration.

