# test_real_api.py File Locations Explained

This project contains three `test_real_api.py` files in different locations, each serving a distinct purpose:

## 1. `tests/test_real_api.py`
**Purpose**: Comprehensive real API testing for core features
**Tests**:
- Bookmark functionality with topic/context parameters
- Language consistency in responses
- Logical inference field completeness
- End-to-end workflow functionality

**Usage**: `GOOGLE_API_KEY=your-key python tests/test_real_api.py`

## 2. `tests/integration/test_real_api.py`
**Purpose**: Integration testing with async coordinator and batch operations
**Tests**:
- AsyncCoordinator with real API calls
- Batch workflow operations
- Production-like scenario validation
- Enhanced reasoning and logical inference

**Usage**: `PYTHONPATH=src python tests/integration/test_real_api.py`

## 3. `tools/test_assets/test_real_api.py`
**Purpose**: Multi-modal feature testing (images, PDFs, URLs)
**Tests**:
- File uploads (images, PDFs)
- URL context processing
- Mixed input scenarios
- Multi-modal functionality

**Usage**: `PYTHONPATH=src python tools/test_assets/test_real_api.py`

## Why Not Consolidated?

These files are **intentionally separate** because they:
1. Test different layers of the system (core vs integration vs multi-modal)
2. Have different dependencies and setup requirements
3. Are used in different testing workflows
4. Provide focused, targeted testing for specific features

This separation follows the testing pyramid pattern: unit tests → integration tests → specialized feature tests.
