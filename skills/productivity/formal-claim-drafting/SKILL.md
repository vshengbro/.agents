---
name: formal-claim-drafting
description: 'Use when drafting complaints or claim letters to win.'
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Legal, Dispute, Complaint, Claim, Refund, Chargeback, Drafting]
    category: productivity
    related_skills: [grounded-citations, blocked-page-recovery, vision-analysis]
---

# Formal Claim Drafting

Drafting a document whose entire purpose is to extract the maximum lawful
remedy from an opposing party: consumer complaints, demand letters, refund
grievances, chargeback narratives, contract dispute notices.

The value is not eloquent prose. It is **what the document locks down before
the other side gets to frame the facts** — a contradicted claim, an unverified
statute number, or a demand that reads as inflated gets the whole filing
knocked down.

## When to Use

Use when the user asks to draft, strengthen, or maximize the position in:

- a consumer complaint / 市场监管投诉举报 filing
- a demand or claim letter to a business (refund, warranty, chargeback)
- a grievance escalating an existing refusal or bad-faith denial
- any document whose purpose is extracting a remedy from an opposing party

Triggers include: "投诉", "举报", "索赔", "退款", "帮我争取最大权益", "怎么投诉",
"写个投诉信", complaint, demand letter, chargeback dispute, refund grievance.

Also use it when an existing draft needs strengthening — the value is in the
evidence-reconciliation and claim-stacking passes, not only in writing from
scratch.

Skip it for pure legal *advice* ("is this action legal") with no document to
produce, and for contracts or policies where the goal is drafting the rules
themselves rather than asserting a claim under them.

## Standing user preference

When the user asks for maximum rights, **stack claims, do not pick one**. Offer
alternative bases in parallel (full remedy OR partial remedy), each with its
own legal footing. Preserve the ceiling even when the realistic floor is much
lower, then say plainly which range to expect.

## Procedure

### ① Inventory and READ every piece of evidence BEFORE writing anything

List every screenshot, receipt, chat log, and document the user has. Run
`vision_analyze` on each one and ask for **verbatim transcription**, not
summary. Write the claim text only after this pass.

Order matters: a user narrates their grievance from memory, and memory is
looser than their own receipts. The documents are the version that survives
scrutiny.

### ② Reconcile the narrative against the evidence — and fix the claim

This is the step that decides whether the document holds up. For every factual
assertion in the user's narrative, ask: **does their own evidence say this?**

Where they conflict, the document loses credibility in its entirety, not just
on that point — an opposing party who spots one overstatement will treat the
whole filing as unreliable.

Two directions, and the second is usually better:

- **Evidence contradicts the claim** → restate the claim so it is still true
  but is not the contradicted version. A screenshot saying "your quota is not
  used up" does not kill a claim that the quota was misleadingly advertised; it
  kills the claim that the quota ran out. Find the stronger adjacent truth.
- **Evidence supports a claim the user did not make** → lead with it. An
  opponent's own admission is worth more than the user's assertion, and it is
  the one thing they cannot walk back.

Never quietly drop the conflict. Tell the user which line was removed and why,
in one sentence, next to the change.

### ③ Verify every statute by fetching it

Never cite an article number from memory. Fetch the text and confirm the
number matches the content you are relying on. See
`references/chinese-law-verification.md` for the source ladder, the
TOC-drift trap, and the fetch workaround.

Also confirm the **substantive law fits the facts** — a real article number
that does not support the sentence next to it is worse than no citation,
because it advertises that the citation was not checked.

### ④ Compute every amount explicitly, and show the arithmetic

Write the formula inline (`total ÷ days × remaining days = X`). An unexplained
figure invites an opposing expert to substitute their own. Where two
reasonable methods exist, state both and take **the one more favorable to the
client**, with a note saying so.

### ⑤ Stack parallel claims, each with an independent legal basis

| Layer | What it does |
|---|---|
| Primary remedy | The best available outcome on the strongest theory |
| Alternative remedy | A lesser outcome on a separate theory — marked as an alternative, not an addition |
| Punitive/statutory uplift | Statutory multiplier or fee-shifting, cited to its own article |
| Interest/costs | Computed separately so a denial of the main claim does not kill it |
| Non-monetary relief | Investigation, disclosure, records preservation — survives even if every money claim fails |

Write alternate claims as explicit alternatives with a sentence stating they do
not double-count. Never present mutually exclusive theories as cumulative.

### ⑥ Give the honest recovery range

State plainly which claims typically survive administrative mediation and which
depend on litigation, and what the realistic settlement band looks like. The
user is deciding whether to spend money and time — a document that implies the
ceiling is probable is a document they will later distrust.

### ⑦ Produce paired artifacts in escalation order

The demand letter and the complaint are two stages of one strategy, not two
documents:

1. **Claim/demand letter** → sets a response deadline and names the escalation
   path. This is the pressure that often resolves it.
2. **Formal complaint** → produced *after* the deadline, with the refusal
   attached as evidence.

Cross-reference the second file from the first, and vice versa. If a document
names a companion file, create it in the same pass — a dangling reference is a
broken instruction the user will follow and hit.

## Pitfalls

- **Writing claims from the user's narration before reading their receipts.**
  The narration is the hypothesis; the screenshots are the record. Reorder
  these and every later step inherits an unchecked premise.
- **Leaving a contradicted claim in because the user asked for it.** They asked
  for the best outcome, not for a specific sentence. Deliver the stronger
  version that survives their own evidence and say what changed.
- **Citing statutes from memory.** Article numbers drift between versions and
  a misnumber is trivially caught.
- **Trusting a table of contents.** Aggregator pages list articles out of
  order or from superseded versions; extracting by TOC position silently returns
  the wrong text. Verify the extracted text reads like the article you wanted.
- **Fetching statutes with the default extractor.** Chinese government and
  legal-text hosts often reject it; the curl-with-browser-UA path in
  `references/chinese-law-verification.md` is the reliable route.
- **Repairing CJK text with a byte-level rewrite.** Patching a large Chinese
  document can silently substitute replacement characters. After any write,
  scan for U+FFFD and re-verify section numbering stayed contiguous.
- **Renumbering sections by hand after an insert.** Shift all downstream
  headings in one reverse-order pass and then assert the sequence is contiguous.
- **Overclaiming the punitive tier.** Inflated demands invite rejection of the
  whole filing. Cap the stated total at the sum of the primary tier, label the
  punitive tier as litigation-dependent.
- **Unsourced assertions of fact about the opponent's systems** (usage data,
  internal logs, quota mechanics) — state these as the client's account and
  request disclosure, rather than asserting them as established.

## Verification

Before delivering:

- Every statute cited was fetched and its text matches the claim it supports.
- Every factual assertion traces to user-supplied evidence or is labeled as
  the user's account.
- No assertion is contradicted by an attachment in the same document.
- All monetary figures recompute from the stated formula.
- Claim numbering is contiguous and alternative claims are marked non-cumulative.
- Every referenced attachment file exists.
- No replacement characters; document opens clean.
