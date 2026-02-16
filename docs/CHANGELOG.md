# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with 49 tests covering baseline scoring functionality
- Normalization tests for skill name standardization
- Scoring tests for keyword matching (exact, partial, inheritance)
- Ranking tests ensuring determinism, tie-breaking, and no skill invention
- API integration tests for `/health` and `/select-skills` endpoints
- Pytest configuration with DEV_MODE enabled for detailed test output

### Fixed
- Empty string handling in baseline scorer to prevent false partial matches
- TOP_N environment variable type conversion (string to int)

### Changed
- Expanded test coverage from 4 to 49 tests

## [0.1.0] - Initial Setup

### Added
- Basic FastAPI application structure
- Baseline scoring algorithm with synonym normalization
- Role profile definitions for multiple engineering roles
- Health check endpoint
- Select skills endpoint (placeholder implementation)
