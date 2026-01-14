# Agent-Tron Verification Guide

## What to Verify

### 1. LPM Sampling (Large Population Model)

**Look for these log messages:**

```
[LPM] Agent <agent_id>: Population prior has <N> products
[LPM] Agent <agent_id>: Conditioned distribution top 3: [('product_id', '0.XXX'), ...]
[LPM] ✓ Agent <agent_id>: Sampled <product_id> with prob <0.XXXX>
```

**What this confirms:**
- ✅ LPM is being called for each persona
- ✅ Population prior is generated (base distribution)
- ✅ Distribution is conditioned on persona (persona-specific preferences)
- ✅ Decision is sampled from the conditioned distribution
- ✅ Different personas should get different sampled decisions

**Expected behavior:**
- Different agent IDs should show different sampled product IDs
- Probabilities should vary based on persona archetype
- Top 3 products in conditioned distribution should differ per persona

---

### 2. Evidence Retrieval (Data Engine)

**Look for these log messages:**

```
[EvidenceRetriever] Persona <archetype> (ID: <agent_id>...): Retrieving <N> items
[EvidenceRetriever] LPM sampled decision: <product_id> (prob: <0.XXX>)
[EvidenceRetriever] Persona <archetype>: Total <N> evidence IDs: [<id1>..., <id2>..., ...]
[Handler] Agent <agent_id>: Evidence IDs (first 3): [<id1>..., <id2>..., <id3>...]
```

**What this confirms:**
- ✅ Evidence retrieval uses the LPM sampled decision
- ✅ Evidence is retrieved from Data Engine (bucket 2 = surveys/interviews)
- ✅ Persona-specific filtering is applied (keywords, demographics, archetype)
- ✅ Different personas get different evidence IDs

**Expected behavior:**
- Different agent IDs should show different evidence IDs
- Evidence count may vary per persona (8-17 items typical)
- Evidence IDs should be unique per persona (not all the same)

---

### 3. Persona-Specific Variation

**Key indicators:**

1. **Different Sampled Decisions:**
   - Agent A: `Sampled p1 with prob 0.6234`
   - Agent B: `Sampled p2 with prob 0.5123`
   - Agent C: `Sampled p1 with prob 0.7891`

2. **Different Evidence IDs:**
   - Agent A: `Evidence IDs: ['abc123...', 'def456...', 'ghi789...']`
   - Agent B: `Evidence IDs: ['xyz987...', 'uvw654...', 'rst321...']`
   - Agent C: `Evidence IDs: ['mno111...', 'pqr222...', 'stu333...']`

3. **Different Evidence Counts:**
   - Some agents get 8 items, others get 10, 12, 15, or 17
   - This is intentional based on persona characteristics

---

## How to Check Logs

### In Terminal/Django Logs:

1. **Search for LPM sampling:**
   ```bash
   grep "\[LPM\]" logs.txt
   ```

2. **Search for evidence retrieval:**
   ```bash
   grep "\[EvidenceRetriever\]" logs.txt
   ```

3. **Search for specific agent:**
   ```bash
   grep "Agent <agent_id>" logs.txt
   ```

### In Django Response:

Check the API response for:
- `sampled_decision.choice` - Should vary per agent
- `sampled_decision.probability` - Should vary per agent
- `ground_truth_evidence` - Should have different `evidence_id` values per agent
- `lpm_trace` - Should show LPM processing details

---

## Troubleshooting

### If all agents get the same sampled decision:
- Check that `agent_id` is unique for each persona
- Verify that `seed` derivation uses `agent_id`
- Check that persona archetype/demographics differ

### If all agents get the same evidence:
- Check that persona-specific filtering is enabled
- Verify that `persona_id` seed is being used for randomization
- Check that evidence scoring includes persona keywords

### If no evidence is retrieved:
- Verify Data Engine is initialized
- Check that bucket 2 (surveys/interviews) has data
- Verify storage directory path is correct

---

## Summary

✅ **LPM Sampling:** Each persona gets a unique decision sampled from their conditioned distribution

✅ **Evidence Retrieval:** Each persona gets persona-specific evidence from the Data Engine

✅ **Persona Variation:** Different personas receive different decisions and evidence

The system is working correctly if you see:
- Different `sampled_decision.choice` values per agent
- Different `ground_truth_evidence` IDs per agent
- Varying evidence counts (8-17 items)
- LPM distribution values that make sense for each persona

