# Skill Pools Data

This directory stores skill pools used for:
1) generating partial-label evaluation cases, and
2) (optionally) informing baseline and hybrid methods.

Skill pools are organized by:
- role profile (e.g., backend, frontend)
- category: Technology | Programming | Concepts
- relevance bucket: core | nice | exclude
- could be implemented later: deprioritized
  - [Not implemented] *deprioritized: skills that might appear but should be ranked low for this role*

## Directory layout

data/skill_pools/
- raw/<role>/
    - <category>.txt
        Human/LLM-authored raw comma-separated lists of skills by category, grouped into sections.
        These files are the source-of-truth for pool generation.
- normalized/
    - skill_pools.json
      Canonical, normalized output used by scripts.
    - skill_pools.schema.json
      JSON schema for validation (optional but recommended).

## Raw file format

Each raw file is a single role profile with multiple sections.

Example sections:

  [core]

  [nice]

  [exclude]

Each section value is a comma-separated list of skills.

## Normalization rules
[Not implemented]
Normalization is applied by scripts/build_skill_pools.py using:
- a normalization pipeline that includes:
  - lowercasing
  - punctuation removal
  - whitespace normalization
- stopword removal (data/normalization/stopwords.txt)
- allow/block overrides:
  - allowlist_overrides.json (force-keep)
  - blocklist_overrides.json (force-drop)

All outputs in normalized/ must be canonical skill strings.
No synonyms or variants should remain.

## How to regenerate skill_pools.json

From repo root:
[Placeholder]

## How to generate eval cases

[Placeholder]

## Generation Prompt Template

```
You are generating a structured skill pool for a resume skill-selection system.

ROLE PROFILE: {ROLE_PROFILE_NAME}
JOB TITLE EXAMPLE: {JOB_TITLE_EXAMPLE}
CATEGORY: {CATEGORY_NAME}

Category definitions:
- Technology: tools, frameworks, platforms, databases, cloud services, DevOps tooling.
- Programming: programming languages only.
- Concepts: technical concepts, patterns, architectures, methodologies, engineering practices. NOT soft skills.

Instructions:
- Generate skills ONLY for the specified CATEGORY.
- Do NOT mix categories. (A common mistake is to include concepts like "rest api" in the Technology category; it belongs in Concepts.)
- Do NOT include soft skills (e.g., communication, leadership).
- Avoid vague items (e.g., "software development", "coding").
- Prefer canonical names (e.g., "postgresql" not "postgres").
- Avoid duplicates.
- Use lowercase except where standard formatting requires otherwise (e.g., c#, node.js).
- No explanations or commentary.
- Generate as many as you can think of for the specified category and role profile, try to make the list comprehensive.

Relevance buckets:
- core: high-signal, commonly expected skills for this role.
- nice: useful but optional skills that strengthen a resume.
- exclude: skills that are typical of other roles and should NOT be selected for this role if present.

Output format (STRICT):

[core]
comma, separated, list, here

[nice]
comma, separated, list, here

[exclude]
comma, separated, list, here
```

## Note
- The skill pools are meant to be a comprehensive list of **relevant** skills that could be expected for each role profile and category. 