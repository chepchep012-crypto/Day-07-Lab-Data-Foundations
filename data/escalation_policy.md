# Support Escalation Policy for the AI Knowledge Assistant

## Purpose

This policy tells support agents when to resolve an issue themselves and when to escalate to a specialized team. Following it keeps response times predictable and routes hard problems to the right owners.

## Severity levels

- **Sev-1 (Critical):** The product is fully down or customer data is exposed. Escalate to the on-call Engineering lead immediately by phone, then open an incident ticket.
- **Sev-2 (High):** A core feature such as search or document upload is broken for many users. Escalate to the Engineering queue within 30 minutes.
- **Sev-3 (Normal):** A single user is blocked but a workaround exists. The agent resolves it using the FAQ articles and updates the ticket.
- **Sev-4 (Low):** Cosmetic issues, feature requests, or how-to questions. The agent answers directly; no escalation.

## When to escalate to Billing

Escalate to the Billing team when a customer reports a charge they cannot explain, a failed refund older than 10 business days, or a tax or invoice correction. Agents must not issue refunds above 200 USD without Billing approval.

## When to escalate to Engineering

Escalate to Engineering for reproducible bugs, error codes the FAQ does not cover, API rate-limit problems that persist after a correct back-off, and any suspected data loss. Always attach the request ID and a screenshot.

## Response-time targets

First response is due within 1 hour for Sev-1 and Sev-2, within 8 working hours for Sev-3, and within 2 working days for Sev-4. The owning team, not the original agent, owns the clock once an issue is escalated.

## What never to escalate

Password resets, email verification, plan upgrades, and other self-service tasks documented in the FAQ should be solved on first contact. Escalating these slows the queue and frustrates the customer.
