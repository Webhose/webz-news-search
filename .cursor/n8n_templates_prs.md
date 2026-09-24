# n8n template PR comments

Last updated: 2026-09-24 (funding-rounds-tracker added)

User review comments for PRs that change files under `n8n/templates/`.
Apply these before submitting or copying layout from a verified template
to a sibling.

Related PRs:

- [#23](https://github.com/Webhose/webz-news-search/pull/23) news research agent layout (verified by n8n)
- [#24](https://github.com/Webhose/webz-news-search/pull/24) ticker monitor layout

Templates:

- `news-research-agent.json` — two agents (quick + deep); verified
- `daily-news-digest-slack.json` — one agent + fan-out; verified-pattern sibling
- `ticker-monitor.json` — one agent + fan-out; same structure as digest
- `funding-rounds-tracker.json` — one agent + fan-out; digest/ticker geometry
- `news-to-sheet.json` — community node, no LLM agent

---

## What n8n rejected before

- Agent templates that were **too basic**: trigger → agent → destination
  with no real logic in between. Each template now needs a durable
  destination and honest intermediate work (fan-out, structured output,
  corroboration, dedupe, fail-loudly).
- **Sticky text overlapping nodes** and **text cut off** inside a sticky.
- **Nodes overflowing** the sticky that is supposed to frame them.
- **Sub-node documentation overlapping the sub-nodes** themselves.

Layout-only PRs must not change connections, prompts, or node names.

---

## Comments from local canvas review (ticker monitor)

These are the comments given while checking the imported workflow in
local n8n (`n8n-webz` on `localhost:5678`).

### Do not copy the research-agent three-row layout onto a one-agent template

The research agent needs three rows because it **has two agent rows**
(quick at y=120, deep at y=360) and sub-nodes underneath at y=600.

Ticker-monitor and the digest have **one agent**. Copying y=600 for
sub-nodes left:

- a large empty hole in the middle of the canvas
- long dangling connectors from the agent down to the model / MCP / parser
- `Report the failure` floating on a mid row with the error connector
  crossing under `Drop stories already alerted`

**Correct reference for one-agent templates is the digest**, not the
research agent:

| Node | Position |
| --- | --- |
| Main flow | y=120, left to right |
| OpenAI Chat Model | (0, 380) |
| Webz.io news search | (160, 380) |
| Structured output parser | (320, 380) |
| Report the failure | (500, 380) |

Sub-nodes sit **directly under the agent**, same as the digest.

The one thing to take from the research agent is the **text-only
Sub-node note** for credentials — not the y=600 row.

### Sticky notes must not be cut

n8n renders nodes **on top of** stickies. If sticky text wraps down to
the node row, the last lines disappear behind the node.

This happened on ticker-monitor **Step 4 note**: width 260px, long
paragraph, text bottom reached y≈120 and hid behind
`Drop stories already alerted`.

Fix by shortening the wording **or** widening the sticky. Do not just
make the sticky taller — height does not help if the text already
collides with a node painted over it.

Leave **~380px of text headroom** from sticky top (y=-260) to the first
node row (y=120). Estimated text bottom must stay above y≈100.

### Visual import is required

A geometry script is not enough. Import into the local n8n instance and
look at the canvas the way a reviewer would. “Looks like the JSON is
fine” is not verification.

Re-import after every layout edit:

```bash
# add a workflow id for CLI import; templates on disk stay without id
docker cp n8n/templates/<file>.json n8n-webz:/tmp/import.json
docker exec n8n-webz n8n import:workflow --input=/tmp/import.json
```

Open `http://localhost:5678/workflow/<id>` and check:

1. No empty hole between the main row and sub-nodes.
2. No long dangling connectors.
3. No sticky text disappearing behind a node.
4. Adjacent stickies do not overlap.
5. Sub-node note is text-only and covers no nodes.

---

## Layout conventions that passed n8n review

### Rows

- **Main flow** left-to-right at **y=120**.
- **Error / empty branch** on a secondary row at **y≈300** only when
  that branch is a real main-flow node (e.g. `Suggest a different
  angle`). Stop-and-error next to sub-nodes stays at **y=380**.
- **Sub-nodes** (chat model, MCP tool, output parser, memory, Think):
  - one-agent templates: **y=380** under the agent (digest / ticker)
  - two-agent templates: **y=600** under both agents (research agent)

### Stickies

- Yellow **Template overview** on the far left; tall enough that the
  full description is visible (research agent overview is 480×1840).
- Grey **step notes** (color 7) start at **y=-260**. They are section
  bands around their nodes, not floating captions.
- **No sticky-to-sticky overlap.** ~20px gutter between adjacent step
  notes.
- Step stickies may cover their own nodes as a background band. They
  must **not** cover nodes from another step, and their **text** must
  not run into any node.
- Credentials and tool docs live in a **Sub-node note** placed **beside**
  the sub-node row so no node sits in its text zone. Do not bury
  “Credentials to add below” inside Step 3.

### What to copy from which template

| Change | Copy from |
| --- | --- |
| One agent, fan-out, Slack, fail-loudly | `daily-news-digest-slack.json` or `ticker-monitor.json` or `funding-rounds-tracker.json` geometry |
| Two agents, classifier, merge | `news-research-agent.json` three-row geometry |
| Credentials / Tools to Include = All | research-agent **Sub-node note** copy, not its coordinates |

---

## Geometry checks before opening a PR

Run a script against the JSON:

1. No two sticky rectangles overlap.
2. Sub-node note rectangle does not intersect any non-sticky node.
3. Estimated rendered text height of every step sticky ends above the
   node row (sticky top y=-260, nodes at y=120 → text bottom < ~100).
4. Positions rounded to the same 10/20 grid as the siblings.

Then import and look. If the screenshot still shows cut text or a hole
in the canvas, it is not ready.

---

## Scope of layout PRs

- Touch only `position`, sticky `content` / `height` / `width`, and new
  sticky nodes.
- Do not change connections, prompts, Code node JS, or credentials.
- One template per PR when n8n is reviewing canvas layout — the
  research-agent fix was #23; ticker-monitor is #24. Do not reopen a
  squash-merged branch; rebase new work onto `master`.
