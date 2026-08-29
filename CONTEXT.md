# Forge

Forge is an agentic orchestration layer that connects a company's entire Stack — SaaS tools and internal systems — into a unified layer where AI Workers sense what is happening, make decisions, and take action in real time.

## Language

**AI Worker**:
A composition of multiple Agents that together handle one complete business function end to end. The customer-facing term for what Forge deploys.
_Avoid_: Bot, automation, assistant

**Agent**:
A discrete autonomous process with a specific responsibility inside an AI Worker.
_Avoid_: Service, microservice, worker (ambiguous with AI Worker)

**Stack**:
All of a company's connected systems — both third-party SaaS tools and internal APIs and databases.
_Avoid_: Tools, infrastructure, tech stack

**System**:
A single item within the Stack — one SaaS tool or one internal API/database that Forge connects to.
_Avoid_: Tool (has a specific meaning in agentic AI: a callable capability), integration, service

**Workflow**:
The business-level description of what a Pipeline accomplishes — expressed in terms the client understands.
_Avoid_: Process, procedure, automation

**Pipeline**:
The technical execution structure that implements a Workflow — the sequence of Agent calls, data transforms, and System interactions that run at runtime.
_Avoid_: Flow, chain, script

**Sense / Decide / Act**:
The three first-class phases of Agent execution. Every Agent in a Pipeline participates in one or more of these phases.
_Avoid_: Observe, reason, execute (use the canonical triad)

**Gap**:
A discrepancy between the stated state and the actual state of work across Systems — the primary signal a Sensing Agent surfaces.
_Avoid_: Issue, problem, inconsistency

**Signal**:
A raw data point collected from a System during the Sense phase — before cross-referencing or interpretation.
_Avoid_: Event, fact, data point

**Brief**:
The human-readable output of a completed Pipeline run — a structured summary of Gaps with prioritised next actions.
_Avoid_: Report, output, result, summary

**Stack Audit**:
A time-boxed Engagement in which Forge maps where intelligence is being lost between a client's Systems and designs the initial AI Workers to close those gaps.
_Avoid_: Assessment, discovery, onboarding

**Engagement**:
A client project — the unit of work Forge delivers. A Stack Audit is one type of Engagement.
_Avoid_: Project, contract, retainer
