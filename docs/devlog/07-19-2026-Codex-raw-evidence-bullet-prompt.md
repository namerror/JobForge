### 2026-07-19 - Raw Evidence Bullet Prompt

**Agent:** Codex (GPT-5)

**Changes:**
- `app/bulletpoints_generation/llm_client.py:92-106` - Added prompt guidance that supplied project or experience evidence is mostly raw, human-written factual context and should be reframed into recruiting-focused, ATS-friendly bullets without copying the evidence's logic, tone, or wording.
- `tests/test_bulletpoints_llm_client.py:73-86` - Extended instruction-building assertions to preserve the raw-evidence and live-evidence recruiting guidance.

**Rationale:**
The bullet generation prompt already required grounded, ATS-friendly resume bullets, but it did not clearly distinguish evidence as factual source material from final resume style. The new phrasing tells the LLM to use evidence for support and context while polishing and reframing the most important supported details for recruiting impact.

**Tests:**
- `test_build_bulletpoint_instructions_distinguishes_exact_and_flexible_counts`: validates that the instruction prompt keeps count guidance, evidence-type wording, and the new raw-evidence polishing guidance.

**Impact:**
Bullet generation should rely less on the source evidence's informal wording or structure while still avoiding unsupported claims.
