# Evaluation Datasets

## Purpose
The evaluation datasets are designed to test the performance of the skill extraction model under different conditions.

## Overview
Every dataset contains a list of cases with the following structure:
```json
[
    {
        "input": {
            "job_role": string,
            "technology": [string],
            "programming": [string],
            "concepts": [string]
        },
        "expected": {
            "technology": [string],
            "programming": [string],
            "concepts": [string]
        }
    },
    ...
]
```
Each case includes an `input` section, which simulates the data that the model will receive, and an `expected` section, which contains the skills that the model should ideally extract and rank.

## Datasets
- `eval_cases_real.json` contains completely randomized cases that simulate real inputs, as it contains skills that may not be in our role profiles. Used to evaluate the model's performance in a more realistic setting, mainly focused on dataset design. Note that the expected skills do not include skills with a score of 0, so this should be tested with flag `include_zero` set to `False`.

- `eval_cases_basic.json` is meant to be used to test baseline performance with known vocabulary. It contains cases where the expected skills are all present in the role profiles, and the model should identify relevant skills and rank them correctly. This dataset is more focused on testing the model's ability at handling known inputs and producing accurate outputs. `include_zero` should be set to `False` for this dataset as well.