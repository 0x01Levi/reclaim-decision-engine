# RECLAIM

### A Deterministic Revenue-Recovery Decision Engine

RECLAIM explores a simple question:

> **When is a revenue-recovery intervention actually worth taking?**

Instead of maximizing retry volume, RECLAIM models the expected economic value of an intervention and determines whether the correct action is to:

**ACT · WAIT · DO NOTHING · ESCALATE**

The project combines **decision theory, probability, expected value, simulation, policy constraints, batch evaluation, and auditability** into a deterministic revenue-recovery foundation.

---

## Why RECLAIM?

A failed payment does not automatically mean that another intervention is worthwhile.

An intervention may:

- recover revenue
- cost money
- have a low probability of success
- duplicate a previous action
- violate a cooldown policy
- create unnecessary customer friction
- produce less value than doing nothing

RECLAIM therefore treats revenue recovery as an **economic decision problem**, not simply a retry problem.

---

## The Core Idea

A simplified economic model is:

```text
Expected Net Value
=
P(recovery) × recoverable amount
− intervention cost
− expected downside
```
The economic calculation is then passed through deterministic policy constraints.

A positive expected value does not automatically mean that an action is allowed.

## Core Pipeline
```Revenue Event
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
┌─────┼────────────┬────────────┐
│     │            │            │
▼     ▼            ▼            ▼
ACT  WAIT      DO NOTHING   ESCALATE
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
```
## Design Principles
1. Optimize value, not activity

A recovery system should not be rewarded simply for performing more interventions.

RECLAIM evaluates whether an intervention is expected to create net economic value.

2. Deterministic money handling

Authoritative monetary calculations use Python's Decimal type rather than binary floating-point arithmetic.

This applies to:

transaction amounts
intervention costs
expected recovery values
downside estimates
recovered revenue
ROI
3. Policy beats recommendations

The decision engine is designed so that recommendations cannot bypass deterministic safeguards.
```Recommendation
      │
      ▼
Policy Engine
      │
 ┌────┼─────────┐
 ▼    ▼         ▼
ALLOW REJECT   ESCALATE
```
Policies can enforce:

confidence thresholds
intervention limits
cooldown periods
amount limits
cost ratios
economic viability
stopping rules
duplicate-action protection

4. DO NOTHING is a valid decision

A recovery system should be capable of deciding that intervention is not worthwhile.

For example:
```Expected recovery:       ₹120
Intervention cost:        ₹35
Expected downside:        ₹95

Decision:
DO_NOTHING
```
Automation should not exist merely for the sake of automation.

5. Auditability

Important decisions are represented through an audit trail containing information such as:

entity IDs
merchant IDs
timestamps
correlation IDs
causation IDs
decisions
interventions
outcomes

This makes it possible to investigate:

- What happened?

- Why was the decision made?

- What action was taken?

- What happened afterward?

## Architecture

```
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
```

## Components
| Component    | Responsibility                                    |
| ------------ | ------------------------------------------------- |
| `domain`     | Core entities, states, and monetary types         |
| `decision`   | Economic calculations and policy-driven decisions |
| `simulator`  | Reproducible synthetic revenue scenarios          |
| `evaluation` | Batch-level economic metrics                      |
| `audit`      | Persistent decision/event history                 |
| `api`        | Minimal FastAPI interface                         |
| `tests`      | Behavioral and edge-case testing                  |

## Decision Engine
The decision engine combines economic reasoning with deterministic policy enforcement.
```
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
```
Possible final decisions:
```
ACT
WAIT
DO_NOTHING
ESCALATE
```
The final decision is not simply the result of a mathematical formula. Policy constraints may override an otherwise attractive intervention.

## Synthetic Revenue Simulation
RECLAIM includes a reproducible synthetic-data generator for multiple recovery scenarios.

Current scenarios include:

transient payment failure
insufficient funds
repeated failure
customer action required
natural recovery
unrecoverable payment
intervention fatigue
escalation

The generator supports reproducible experiments through deterministic seeds.

Example:
```
generator = SyntheticDataGenerator(seed=42)
events = generator.generate(...)
```
This makes it possible to repeat experiments against the same underlying data.

## Evaluation

RECLAIM evaluates strategies over batches, rather than relying on isolated successful examples.

Current metrics include:

- total revenue at risk
- recovered revenue
- intervention cost
- net recovered value
- recovery rate
- intervention rate
- baseline recovery
- incremental recovered value
- ROI

A simplified comparison:
```
                    Baseline       RECLAIM
                   ----------      --------
Revenue at risk        ₹X             ₹X
Recovered revenue     ₹A             ₹B
Intervention cost      ₹0             ₹C
Net recovered value   ₹A             ₹B-C

Incremental value:
(B - C) - A
```

The current baseline is intentionally simple and should not be interpreted as a causal estimate.

## Current Status
### Implemented
- Decimal-based monetary model
- Core merchant, customer, revenue, failure, intervention, and outcome models
- Explicit decision states
- Expected-value economic engine
- Deterministic policy engine
- Intervention state transitions
- Idempotency protection
- Synthetic scenario generation
- Reproducible simulation
- Batch evaluation metrics
- Baseline comparison
- SQLite audit storage
- Correlation and causation tracking
- Minimal FastAPI application
- Automated test suite

### Test Suite

96 tests passing

## What RECLAIM Is Not

The current project is not:

- a production payment processor
- a live money-transfer system
- a production fraud detector
- a real-time merchant platform
- a causal inference framework
- an autonomous financial agent

It is a deterministic foundation for experimenting with revenue-recovery decision systems.

## Roadmap

### Phase 1 — Probabilistic / AI Decision Layer
Potential future work:

- failure-context classification
- recovery probability estimation
- intervention recommendation
- structured model outputs
- confidence calibration
- model evaluation

The deterministic economic and policy layers should remain authoritative.

## Phase 2 — Event Integration

### Potential future work:

- event ingestion
- webhook handling
- Razorpay Test Mode integration
- bounded intervention execution
- customer notification workflows
- idempotent external actions

## Phase 3 — Advanced Evaluation

### Potential future work:

- stronger counterfactual baselines
- controlled experiments
- causal analysis
- larger simulations
- sensitivity analysis
- calibration analysis

## Phase 4 — Interface

### Potential future work:

- merchant dashboard
- decision inspection
- recovery analytics
- audit explorer
- escalation monitoring

## Installation

Clone the repository:

```
git clone https://github.com/0x01Levi/reclaim-decision-engine
cd reclaim-decision-engine
```

Create a virtual environment:

```
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

## Running Tests

Run the complete test suite:
```
pytest
```

verbose output:
```
pytest -v
```

Run a specific test module:
```
pytest tests/test_money.py -v
```

## Running the API

Start the development server:
```
python main.py
```
Or with Uvicorn:
```
uvicorn src.api:app --reload
```
Health check:
```
GET /health
```
Interactive API documentation:
```
/docs
```

## Project Philosophy

- A good automated decision is not the one that acts the most. It is the one that creates the most value while respecting its constraints.

RECLAIM is built around the idea that intelligent automation should be able to justify four fundamentally different outcomes:
```
ACT
WAIT
DO_NOTHING
ESCALATE
```
The long-term goal is to combine probabilistic reasoning with deterministic economic and policy controls without allowing opaque model output to become the authority over financial state.

## Research & Learning Areas

RECLAIM provides a practical environment for exploring:

- decision theory
- expected value
- probability
- optimization
- simulation
- economic modeling
- policy engines
- state machines
- idempotency
- reproducible experiments
- evaluation methodology
- auditability
- AI-assisted decision systems

The deterministic components are intentionally useful on their own, even before an AI layer is introduced.

## License
### MIT
