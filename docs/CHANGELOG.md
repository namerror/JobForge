# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Role family detection and inheritance in baseline scorer
- Baseline scoring algorithm with role-specific boosts
- Skill selection service with latency tracking and structured logging
- `include_zero` option in skill ranking to include irrelevant skills for evaluation purposes, defaulting to False

### Fixed
- Empty string handling in baseline scorer to prevent false partial matches
- TOP_N environment variable type conversion (string to int)
- Attribute name mismatch in `baseline_select_skills()` (job_role vs role)

## [0.1.0] - Initial Setup

### Added
- Basic FastAPI application structure
- Baseline scoring algorithm with synonym normalization
- Role profile definitions for multiple engineering roles
- Health check endpoint
- Select skills endpoint (placeholder implementation)
