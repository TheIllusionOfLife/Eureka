# Thread-Safety Migration Status

**PR**: #208
**Branch**: `fix/backend-thread-safety`
**Started**: 2025-11-18
**Status**: 65% Complete (Phase 1-2 Mostly Done)

---

## 🎯 Objective

Eliminate thread-safety issues in backend by implementing request-scoped router architecture.

**Problem**: Global singleton + env var manipulation = race conditions in concurrent requests
**Solution**: Request-scoped `LLMRouter` instances with explicit configuration

---

## ✅ Completed (65%)

### Phase 1: Immutable Configuration ✅
- `LLMConfig` accepts constructor parameters
- `LLMRouter` accepts optional `config` parameter
- No env manipulation during object creation
- 11 tests passing
- **Commit**: c0226b9d

### Phase 2: Request-Scoped Support ⚠️ (Mostly Complete)

**Core Infrastructure** ✅:
- `AsyncCoordinator` accepts `router` parameter
- Backend endpoints create request-scoped routers
- All 5 agents accept `router` parameter
- Environment variable manipulation removed
- Thread-safety locks removed (no longer needed)
- 16 tests passing

**Agents Updated** ✅:
- `Critic` (evaluate_ideas) - **Commit**: 5ccc1d13
- `Advocate` (advocate_idea) - **Commit**: 67cc890c
- `Skeptic` (criticize_idea) - **Commit**: 67cc890c
- `IdeaGenerator` (generate_ideas) - **Commit**: 9e802483
- `StructuredIdeaGenerator` (improve_idea_structured) - **Commit**: 9e802483

**Backend Updated** ✅:
- Multimodal endpoint (line ~1400) - **Commit**: 8fd3f151
- Async endpoint (line ~1520) - **Commit**: 8fd3f151
- Removed `_router_config_lock` and `reset_router` imports
- Removed environment save/restore blocks

**Files Modified**:
- `src/madspark/llm/router.py` (Phase 1)
- `src/madspark/core/async_coordinator.py` (accepts router)
- `src/madspark/agents/critic.py` (router param)
- `src/madspark/agents/advocate.py` (router param)
- `src/madspark/agents/skeptic.py` (router param)
- `src/madspark/agents/idea_generator.py` (router param)
- `src/madspark/agents/structured_idea_generator.py` (router param)
- `web/backend/main.py` (request-scoped routers, removed env writes)
- `tests/test_thread_safety_phase1.py` (new, 11 tests)
- `tests/test_thread_safety_phase2.py` (new, 16 tests)

---

## 🔄 Remaining Work (60%)

### Priority 1: Complete Phase 2 (4-6 hours) 🔴

#### 1.1 Update Remaining Agents
Each agent needs:
1. Add parameter: `router: Optional["LLMRouter"] = None`
2. Add TYPE_CHECKING import
3. Use provided router: `router_instance = router if router else get_router()`

**Files to update**:
- `src/madspark/agents/advocate.py` - Line 86: `advocate_idea()`
- `src/madspark/agents/skeptic.py` - Line 99: `criticize_idea()`
- `src/madspark/agents/idea_generator.py` - Line ~180: `generate_ideas()`
- `src/madspark/agents/structured_idea_generator.py` - Line ~120: `improve_idea()`

**Pattern to follow** (see critic.py lines 71-132):
```python
# 1. Add imports
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ..llm.router import LLMRouter

# 2. Update signature
def function_name(..., router: Optional["LLMRouter"] = None) -> str:
    """
    Args:
        router: Optional LLMRouter instance for request-scoped routing
    """

# 3. Use provided router
if should_route:
    router_instance = router if router else get_router()
    validated, response = router_instance.generate_structured(...)
```

#### 1.2 Update Backend Endpoints
**File**: `web/backend/main.py`

**Remove** env manipulation blocks:
- Lines 1414-1433 (multimodal endpoint)
- Lines 1540-1557 (async endpoint)

**Add** request-scoped router creation:
```python
# BEFORE async_coordinator creation
request_router = None
if LLM_ROUTER_AVAILABLE:
    request_router = LLMRouter(
        primary_provider=idea_request.llm_provider or "auto",
        fallback_enabled=not getattr(idea_request, 'no_fallback', False),
        cache_enabled=idea_request.use_llm_cache
    )

# Pass to coordinator
async_coordinator = AsyncCoordinator(
    max_concurrent_agents=max_concurrent_agents,
    progress_callback=progress_callback,
    cache_manager=cache_manager,
    router=request_router,  # NEW
)
```

**Also remove**:
- `_router_config_lock` usage
- `reset_router()` calls
- `original_env` restoration blocks

#### 1.3 Update AsyncCoordinator Agent Calls
**File**: `src/madspark/core/async_coordinator.py`

Find agent calls and add `router=self.router`:
- `async_generate_ideas()` - pass to `generate_ideas_with_retry()`
- `async_evaluate_ideas()` - pass to `evaluate_ideas_with_retry()`
- `_process_candidates_with_batch_advocacy()` - pass to advocates
- `_process_candidates_with_batch_skepticism()` - pass to skeptics

**Pattern**:
```python
result = await agent_function_with_retry(
    topic=topic,
    context=context,
    router=self.router,  # ADD THIS
    # ... other params
)
```

#### 1.4 Write Concurrent Request Tests
**File**: `tests/test_thread_safety_phase2_concurrent.py` (new)

Test 20+ concurrent requests with:
- Different providers (ollama, gemini, auto)
- Different tiers (fast, balanced, quality)
- Different cache settings
- Verify no config contamination
- Verify metrics isolated

```python
@pytest.mark.asyncio
async def test_20_concurrent_requests_mixed_config():
    """Test concurrent requests don't interfere."""
    # Create 20 tasks with different configs
    # Verify each gets correct provider/tier
    # Verify metrics are per-request
```

#### 1.5 Verify All Tests Pass
```bash
# Full test suite
PYTHONPATH=src pytest

# Thread-safety specific
PYTHONPATH=src pytest tests/test_thread_safety_*.py -v
```

---

### Priority 2: Phase 3 - Load Testing (2-3 hours) 🟡

**File**: `tests/test_thread_safety_load.py` (new)

1. **100+ Concurrent Request Test**
   - Sustained load for 5-10 minutes
   - Random provider/tier/cache mix
   - Monitor memory usage
   - Verify no metrics contamination

2. **Manual Testing Checklist**
   - [ ] Docker compose up (backend + Ollama)
   - [ ] Open 5 browser tabs
   - [ ] Submit requests simultaneously with different configs
   - [ ] Verify each request uses correct provider
   - [ ] Check server logs for router lifecycle
   - [ ] Inspect response metrics

3. **Real API Key Testing**
   ```bash
   export GOOGLE_API_KEY=xxx
   export OLLAMA_HOST=http://localhost:11434

   # Test scenarios:
   # 1. Ollama-first (default)
   # 2. Force Gemini
   # 3. Force Ollama
   # 4. Mix in concurrent requests
   ```

---

### Priority 3: Phase 4 - CLI Migration (3-4 hours) 🟢

**Files**:
- `src/madspark/cli/cli.py` - Remove lines 829-846 (env writes)
- `src/madspark/core/coordinator.py` - Add router parameter
- `src/madspark/core/coordinator_batch.py` - Add router parameter

**Pattern**:
```python
# CLI creates router from args
cli_router = None
if should_use_router(args):
    cli_router = LLMRouter(
        primary_provider=args.provider,
        fallback_enabled=not args.no_fallback,
        cache_enabled=not args.no_cache,
    )

# Pass to coordinator
coordinator = Coordinator(router=cli_router)
results = coordinator.run_workflow(...)
```

---

### Priority 4: Phase 5 - Cleanup & Docs (2 hours) 🟢

1. **Deprecate Singleton**
   ```python
   # src/madspark/llm/router.py
   def get_router() -> LLMRouter:
       warnings.warn(
           "get_router() is deprecated. Use LLMRouter(...) directly.",
           DeprecationWarning,
           stacklevel=2
       )
       # ... existing code
   ```

2. **Update Documentation**
   - README.md: LLM provider section
   - CLAUDE.md: Add request-scoped pattern
   - docs/ARCHITECTURE.md: Thread-safety patterns
   - src/madspark/llm/README.md: Usage examples

3. **Grep Verification**
   ```bash
   # Should find NO writes in production code
   grep -r "os.environ\[.*MADSPARK" --exclude-dir=tests src/

   # Should be minimal (deprecated only)
   grep -r "get_router()" --exclude-dir=tests src/
   ```

4. **Test Fixtures**
   - Update `tests/conftest.py` with router fixtures
   - Convert tests to use direct instantiation

---

## 📊 Progress Tracking

| Phase | Tasks | Completed | Progress |
|-------|-------|-----------|----------|
| Phase 1 | 3 | 3 | 100% ✅ |
| Phase 2 | 5 | 2 | 40% ⚠️ |
| Phase 3 | 3 | 0 | 0% |
| Phase 4 | 3 | 0 | 0% |
| Phase 5 | 4 | 0 | 0% |
| **Total** | **18** | **5** | **28%** |

---

## 🧪 Test Commands

```bash
# Phase 1-2 tests
PYTHONPATH=src pytest tests/test_thread_safety_phase1.py -v
PYTHONPATH=src pytest tests/test_thread_safety_phase2.py -v

# Full suite
PYTHONPATH=src pytest

# With coverage
PYTHONPATH=src pytest --cov=src/madspark --cov-report=html

# Load test (when Phase 3 complete)
PYTHONPATH=src pytest tests/test_thread_safety_load.py -v --timeout=600
```

---

## 🔗 Key Files Reference

**Core Implementation**:
- `src/madspark/llm/router.py` - Router class
- `src/madspark/llm/config.py` - Config class
- `src/madspark/core/async_coordinator.py` - Async coordinator

**Agents** (5 total):
- `src/madspark/agents/critic.py` ✅ (done)
- `src/madspark/agents/advocate.py` ⏳ (pending)
- `src/madspark/agents/skeptic.py` ⏳ (pending)
- `src/madspark/agents/idea_generator.py` ⏳ (pending)
- `src/madspark/agents/structured_idea_generator.py` ⏳ (pending)

**Backend**:
- `web/backend/main.py` - Endpoints (lines 1414-1433, 1540-1557)

**Tests**:
- `tests/test_thread_safety_phase1.py` ✅ (11 tests)
- `tests/test_thread_safety_phase2.py` ⚠️ (6/13 tests)
- `tests/test_thread_safety_load.py` ⏳ (not created)

---

## 💡 Next Session Checklist

**To resume work efficiently**:

1. ✅ Read this status document
2. ✅ Check out branch: `git checkout fix/backend-thread-safety`
3. ✅ Run existing tests to verify state
4. ⏳ Start with Priority 1.1 (update 4 remaining agents)
5. ⏳ Continue through priorities in order
6. ⏳ Commit after each logical milestone
7. ⏳ Update PR description with progress
8. ⏳ Mark PR as ready when all phases complete

---

## 📝 Design Rationale

**Why request-scoped instead of config-passing?**
- Perfect isolation (no shared state)
- Thread-safe by design (no locks needed)
- Future-proof for multi-tenant/AB testing
- Clean dependency injection pattern
- Each request has independent metrics

**Why not just fix the singleton?**
- Singletons + mutable state = inherently racy
- Locks reduce concurrency, add complexity
- Request-scoped is industry standard pattern
- Easier to test and reason about

---

**Last Updated**: 2025-11-18
**Estimated Remaining**: 10-13 hours
**Next Session Priority**: Complete Phase 2 (agents + backend)
