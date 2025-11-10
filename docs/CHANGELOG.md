# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed
- `BatchProcessor.process_batch()` now raises `BatchProcessingError` instead of `RuntimeError` when invoked from an async context, aligning the implementation, documentation, and regression tests (PR #199).

