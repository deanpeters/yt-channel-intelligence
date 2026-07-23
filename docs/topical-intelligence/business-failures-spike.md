# Business Failures Topical Intelligence Spike

**Status:** Provisional workup for review

**Captured:** 2026-07-23

**Corpus:** Michael Girdley's *The rise and fall* playlist
**Source:** <https://www.youtube.com/playlist?list=PLZ6vahBdAJ3iArMOb5Mrpav98SjW9dsaz>

## Purpose

Test whether the existing YouTube capture pipeline can become the front end of a trustworthy topical knowledge base without forcing company-intelligence questions onto the material.

This spike grew deliberately from three to twenty videos. Its job is to expose
useful patterns, weak assumptions, taxonomy drift, and retrieval limits before
the full playlist is indexed.

## What was captured

| Order | Case | Duration | Published | Source |
|---|---|---:|---|---|
| 1 | Pizza Hut | 19:02 | 2026-07-22 | [Why Pizza Hut is still totally screwed](https://www.youtube.com/watch?v=CU3xYnICJ0s) |
| 2 | American Airlines | 21:00 | 2026-07-20 | [Why American Airlines keeps getting worse](https://www.youtube.com/watch?v=KhoAf9K9JC8) |
| 3 | NASA | 25:41 | 2026-07-17 | [What happened to NASA?](https://www.youtube.com/watch?v=eX9ZC5k7XdI) |
| 4 | Tesla | 19:24 | 2026-07-13 | [Why Tesla Sales are Falling Short in the U.S.](https://www.youtube.com/watch?v=JwqbWp3738o) |
| 5 | FTX | 22:34 | 2026-07-10 | [What really caused FTX to collapse](https://www.youtube.com/watch?v=3470164O6p8) |
| 6 | McDonald's | 19:55 | 2026-07-08 | [Why Nobody's Eating McDonald's Anymore](https://www.youtube.com/watch?v=v8w6djdUt1U) |
| 7 | Snapchat | 17:31 | 2026-07-06 | [Why nobody uses Snapchat anymore](https://www.youtube.com/watch?v=zmp7kFYYL6U) |
| 8 | Doritos | 21:47 | 2026-07-03 | [Why nobody buys Doritos anymore](https://www.youtube.com/watch?v=WhVSww5fzBA) |
| 9 | Craigslist | 20:48 | 2026-07-01 | [Why nobody uses Craigslist anymore](https://www.youtube.com/watch?v=31oqfd8myBI) |
| 10 | Pickleball business ecosystem | 18:31 | 2026-06-29 | [Why the Pickleball boom is already over](https://www.youtube.com/watch?v=mNiOhjB7hNI) |
| 11 | Outback Steakhouse | 14:48 | 2026-06-24 | [Why nobody goes to Outback Steakhouse anymore](https://www.youtube.com/watch?v=HEdhdnbp9lo) |
| 12 | QVC and HSN | 16:08 | 2026-06-19 | [The rise and fall of QVC and HSN](https://www.youtube.com/watch?v=hKZM21muITg) |
| 13 | Crocs | 17:10 | 2026-06-17 | [Why everyone wears these ugly shoes](https://www.youtube.com/watch?v=e31CEPxSJaU) |
| 14 | Panda Express | 13:04 | 2026-06-15 | [The rise of Panda Express](https://www.youtube.com/watch?v=dAp7D2ZX8Ik) |
| 15 | Shark Tank | 16:26 | 2026-06-12 | [From 8 million viewers to irrelevant](https://www.youtube.com/watch?v=3cQ20dNnmDA) |
| 16 | Cartoon Network | 15:06 | 2026-06-10 | [Why Cartoon Network became a dying channel](https://www.youtube.com/watch?v=MPtnA6-LDzw) |
| 17 | Five Guys | 14:39 | 2026-06-08 | [Why nobody goes to Five Guys anymore](https://www.youtube.com/watch?v=4-8_etpRj1Y) |
| 18 | Applebee's | 14:55 | 2026-06-05 | [The real reason Applebee's is dying](https://www.youtube.com/watch?v=hwFIjOsWoCs) |
| 19 | Topgolf | 18:25 | 2026-06-03 | [The rise and fall of Topgolf](https://www.youtube.com/watch?v=guxBwYjQ_GI) |
| 20 | American Idol | 12:15 | 2026-06-01 | [How American Idol went from 36 million viewers to cancelled](https://www.youtube.com/watch?v=NfkzzB_EG5c) |

The local corpus contains:

- 20 audio files
- 20 raw text transcripts
- 20 timestamped SRT files
- 20 YouTube English-original caption files for comparison
- 20 canonical Markdown transcripts with YAML metadata and timestamp deep links
- 73,181 transcribed words
- a SQLite resume database and `corpus.json` manifest

Generated corpus artifacts live under `.workspace/topics/business-failures/` and are intentionally gitignored.

## What the cases taught us

### Failure is usually a system, not an event

Each story uses a visible outcome as its hook, but explains it through accumulated decisions and reinforcing mechanisms:

- Pizza Hut: early franchise and real-estate choices constrained a later delivery pivot; ownership distance, market change, and a mismatched cost structure compounded the problem.
- American Airlines: labor distrust, loss of a technology advantage, delayed restructuring, debt, share buybacks, and an unclear market position reinforced one another.
- NASA: loss of mission, political contracting incentives, managerial suppression of engineering feedback, and normalization of deviance changed what the institution optimized for.

The unit of analysis should therefore be a **failure case with a causal chain**, not merely a bag of topic keywords.

### A single flat category list will be too weak

The same passage can describe:

- an actor,
- a decision,
- a causal mechanism,
- a stage in the decline,
- an outcome,
- and a type of evidence.

Those dimensions should be stored separately so a later query can ask either:

- "Show cases involving financial leverage," or
- "Show decisions that suppressed frontline warnings," or
- "What outcomes followed strategic ambiguity?"

### Source material and analyst interpretation must remain separate

These videos combine dates and metrics, historical events, comparisons, personal anecdotes, strong narrator judgments, clips, and sponsor segments. Retrieval must not flatten all of those into equally authoritative evidence.

The source transcript should remain immutable. Generated labels and derived causal claims should live in a versioned enrichment layer that can be reviewed and replaced.

## Provisional taxonomy v0.3

This is a workup, not approved canon.

### 1. Case identity

Stable fields describing what the case is:

- `subject`
- `subject_type` — company, government agency, product, program, industry
- `industry`
- `geography`
- `time_period`
- `case_scope`
- `failure_state` — decline, bankruptcy, capability loss, safety catastrophe, displacement, failed turnaround

### 2. Causal role

What job a passage does in the failure story:

- `initial_advantage`
- `structural_constraint`
- `decision`
- `mechanism`
- `amplifier`
- `trigger`
- `warning_signal`
- `consequence`
- `response`
- `counterexample`

This dimension is more useful than treating every passage as another undifferentiated "insight."

### 3. Failure mechanism

Multi-select labels for why decline occurred:

- `strategic_drift`
- `unclear_positioning`
- `path_dependence`
- `cost_structure_mismatch`
- `ownership_or_portfolio_neglect`
- `incentive_misalignment`
- `governance_failure`
- `capability_erosion`
- `stakeholder_betrayal`
- `feedback_suppression`
- `financial_leverage`
- `short_term_optimization`
- `market_or_demographic_shift`
- `mission_loss`
- `normalization_of_deviance`
- `failed_transformation`
- `fraud_or_asset_misappropriation`
- `identity_or_reputation_coupling`
- `network_effect_reversal`
- `quality_or_value_erosion`
- `overexpansion_or_overcapacity`
- `commoditization`
- `mission_or_values_lock_in`
- `channel_or_platform_dependency`
- `adverse_selection`
- `success_induced_obsolescence`
- `acquisition_or_integration_failure`

The seven additions were justified by distinct evidence in the expanded cases,
not by an attempt to create an exhaustive ontology. They cover FTX's misuse of
customer assets, Tesla's founder-brand coupling, Snapchat's and Craigslist's
network reversals, McDonald's and Doritos' value erosion, pickleball
overcapacity and commodity equipment, and Craigslist's deliberate values
lock-in.

The second ten cases also require `case_role` so retrieval and teaching material
can distinguish failure, decline, institutional failure, underperformance,
values tradeoffs, boom-bust risk, turnaround counterexample, resilience
counterexample, and partial recovery. Crocs and Panda Express proved why this
cannot be inferred from a playlist title.

### 4. Actor

Who made, influenced, experienced, or responded to the decision:

- `leadership`
- `owner_or_investor`
- `workforce`
- `customer`
- `franchisee_or_partner`
- `contractor_or_supplier`
- `regulator_or_politician`
- `competitor`

### 5. Evidence type

How a retrieved passage should be treated:

- `historical_event`
- `quantitative_metric`
- `named_source_or_quote`
- `narrator_analysis`
- `comparison`
- `personal_anecdote`
- `sponsor_segment`

Sponsor segments should be detected and excluded from topical retrieval by default.

### 6. Epistemic status

Keep source and synthesis honest:

- `direct_source_claim`
- `derived_inference`
- `contested_or_unverified`
- `missing_evidence`

The initial corpus comes from one narrator, so repetition across videos is not independent corroboration.

## Initial case-label workup

These reviewed case labels are stored in
`topics/business-failures.yaml`. Passage labels live in the separate generated
enrichment layer so they can be replaced without changing the source
transcripts.

| Case | Candidate mechanisms | Failure state | Useful contrast |
|---|---|---|---|
| Pizza Hut | path dependence, cost-structure mismatch, ownership/portfolio neglect, unclear positioning, market shift, failed transformation | sustained decline, franchisee bankruptcy, distressed sale | Domino's focused delivery and technology model |
| American Airlines | capability erosion, stakeholder betrayal, financial leverage, short-term optimization, unclear positioning, failed transformation | bankruptcy, market-share loss, customer-experience decline, debt-constrained reinvestment | Delta premium focus and lower-cost carriers |
| NASA | mission loss, incentive misalignment, governance failure, feedback suppression, normalization of deviance, capability erosion | safety catastrophes, cost escalation, launch capability loss, commercial displacement | fixed-price COTS contracts and SpaceX |
| Tesla | identity/reputation coupling, stakeholder betrayal, unclear positioning, strategic drift, market shift | sales decline, market-share loss, brand damage | EV competitors grew while Tesla declined |
| FTX | fraud/asset misuse, governance failure, incentive misalignment, feedback suppression, stakeholder betrayal | conviction, bankruptcy, customer-asset loss, confidence collapse | formal controls expected of financial institutions |
| McDonald's | short-term optimization, unclear positioning, strategic drift, cost mismatch, value erosion | same-store sales, value perception, and frequency decline | fast-casual value and McDonald's real-estate resilience |
| Snapchat | governance failure, feedback suppression, failed transformation, network reversal, capability erosion | stagnation, creator abandonment, product misfires | Instagram, TikTok, and ecosystem-based AR competitors |
| Doritos | short-term optimization, value erosion, stakeholder betrayal, strategic drift, market shift | volume and trust decline; parent-company stagnation | long-term brand stewardship |
| Craigslist | path dependence, values lock-in, capability erosion, failed transformation, network reversal | traffic and relevance decline; category fragmentation | focused vertical marketplaces |
| Pickleball ecosystem | demographic shift, cost mismatch, overcapacity, commoditization, incentive mismatch | franchisee losses, bankruptcies, slowing growth | low-cost public play and differentiated alternatives |

## Cross-case patterns worth making retrievable

### 1. Small decisions compound into structural failure

Pizza Hut's narrator explicitly frames decline as "little mistakes and little changes" compounding over time at [03:05](https://www.youtube.com/watch?v=CU3xYnICJ0s&t=185s). American Airlines closes with the same pattern: short-term decisions "borrow a mortgage against the future" at [20:27](https://www.youtube.com/watch?v=KhoAf9K9JC8&t=1227s).

### 2. Strategic ambiguity produces a middle with no advantage

Pizza Hut is described as "stuck in the middle" at [11:16](https://www.youtube.com/watch?v=CU3xYnICJ0s&t=676s). American Airlines is similarly described as unable to be multiple things at once at [14:58](https://www.youtube.com/watch?v=KhoAf9K9JC8&t=898s).

### 3. Incentives frequently explain behavior better than stated intent

Pizza Hut's proposed private-equity turnaround is constrained by defined hold periods at [16:08](https://www.youtube.com/watch?v=CU3xYnICJ0s&t=968s). American Airlines spent nearly $13 billion on share buybacks while carrying merger debt at [15:27](https://www.youtube.com/watch?v=KhoAf9K9JC8&t=927s). NASA's cost-plus contracting rewarded greater spending, while fixed-price contracts reversed that incentive at [21:43](https://www.youtube.com/watch?v=eX9ZC5k7XdI&t=1303s).

### 4. Organizations suppress inconvenient feedback before visible failure

NASA managers overruled engineers at [12:12](https://www.youtube.com/watch?v=eX9ZC5k7XdI&t=732s), and repeated anomalies became normalized at [12:28](https://www.youtube.com/watch?v=eX9ZC5k7XdI&t=748s). American Airlines' long-running workforce betrayal remained visible decades later at [19:17](https://www.youtube.com/watch?v=KhoAf9K9JC8&t=1157s).

### 5. Recovery may require a competing system, not an internal fix

The NASA story's most distinctive response is creating a competitor that could continue the original mission at [25:04](https://www.youtube.com/watch?v=eX9ZC5k7XdI&t=1504s). This suggests `response` needs to distinguish internal turnaround, restructuring, sale, and external replacement.

## Retrieval implications

The first index should embed timestamped transcript chunks with:

- stable source metadata,
- start and end timestamps,
- case identity,
- reviewed causal-role labels,
- reviewed failure-mechanism labels,
- evidence type,
- taxonomy version.

Retrieval should diversify across cases rather than return several adjacent chunks from one video. MMR is a reasonable first default.

Answers should include:

1. a direct source-backed synthesis,
2. the cases represented,
3. timestamp-linked excerpts,
4. clearly labeled inference,
5. corpus limitations or missing evidence.

## Quality issues found during the spike

- `small.en` is adequate for pattern discovery but introduces transcription errors in names and occasional phrases. Retrieval should point to audio timestamps, and important quotations should be checked before publication.
- Sponsor segments are embedded throughout the corpus and need exclusion labels.
- Flat-playlist metadata provides useful channel and playlist identity, while final publication dates arrive during individual video download.
- The current corpus contains one channel and one narrator. It supports analysis of the channel's treatment of business failure, not yet independent domain truth.
- Video titles frame NASA as a failure alongside companies, but `subject_type` and `failure_state` must preserve the important distinction between corporate decline and institutional mission/capability failure.

## Caveat mitigation implemented

### Transcript accuracy

- Downloaded YouTube's English-original automatic captions for all twenty videos as an independent comparison source.
- Kept local `small.en` Whisper output as the selected retrieval transcript because it produces clean, non-overlapping segments and was at least as accurate on inspected names.
- Attempted local `medium.en`. Apple GPU allocation failed; CPU mode worked but
  was too slow for an interactive spike. The seven additional samples use the
  accepted `small.en` path.
- Preserved audio, both transcript candidates, and timestamps so any passage can be re-transcribed or checked without downloading again.

For a later quality pass, the practical order is:

1. Prefer creator-edited captions when a video provides them.
2. Compare YouTube automatic captions with local Whisper output.
3. Re-transcribe only disputed or publication-bound passages with a stronger model.
4. Verify quoted names, numbers, and claims against the timestamped audio.

Downloading a larger model for every passage is not the best first move. The
[official whisper.cpp model catalog](https://github.com/ggml-org/whisper.cpp/blob/master/models/README.md)
includes quantized `large-v3-turbo` variants that use less disk and memory than
full `large-v3`; that is worth testing only after retrieval proves which
passages require better transcription. The caption comparison path uses
[yt-dlp's supported subtitle options](https://github.com/yt-dlp/yt-dlp#subtitle-options).

### Sponsor contamination

- Added reviewed sponsor intervals for Outskill, Compound Conference, Relay,
  Bedrock, Homebase, Zapier, Monarch, David, and Near.
- Preserved 54 sponsor passages in the enrichment artifact for auditability.
- Excluded all 54 from the Chroma collection.
- Verified the 334 indexed passages contain zero `sponsor_segment` records.

### Single-narrator bias

- Added evidence-type labels that distinguish metrics, historical events, named quotations, comparisons, personal anecdotes, and narrator analysis.
- Added epistemic status: direct source claim, derived inference, contested or unverified, and missing evidence.
- Marked passage-level model labels as `machine_workup`; reviewed corrections are `curated_workup`.
- Kept the source transcript immutable and stored generated interpretation in a separate JSONL enrichment layer.

This mitigates false confidence but does not create independent corroboration.
That requires additional channels, primary records, or reliable external sources
in a later domain-intelligence mode.

## Retrieval spike results

The disposable Chroma index contains 334 non-sponsor passages using local
`sentence-transformers/all-MiniLM-L6-v2` embeddings. Each passage carries its
case identity, timestamps, source URL, taxonomy version, transcript source,
case labels, passage labels, evidence type, and epistemic status.

This follows Chroma's
[local `PersistentClient` pattern](https://cookbook.chromadb.dev/core/) and the
[Sentence Transformers semantic-search pattern](https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html).

At twenty videos, the unchanged three-case regression produces:

- **5/10 complete case coverage**
- **5/10 strict retrieval**
- **Zero sponsor contamination.**

The separate twenty-video calibration suite produces **8/10 complete case
coverage** and **8/10 strict retrieval**. Hybrid retrieval materially improves
label-aware results, but the old generic questions become ambiguous when many
additional cases are valid answers. Keep the old suite as a regression and add
explicit case scope or conversational context rather than hiding the mismatch.

The generated evaluation is stored at
`reports/topics/business-failures-retrieval-evaluation.md`.

## Recommended next slice

Do not ingest the remaining 101 playlist videos yet.

First:

1. Review a stratified sample of v0.3 machine-workup passages in the notebook.
2. Add explicit case, industry, case-role, or playlist-range query scope.
3. Generate source-linked case cards and causal chains for all twenty cases.
4. Add source-backed answer synthesis only after scoped retrieval is strong.
5. Add a small corroboration pilot from a second source before calling the
   corpus domain intelligence.
6. Capture positions 21–35 only after those learning artifacts pass review.
