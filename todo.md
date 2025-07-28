# Plan to Fix High and Medium Priority User Experience Issues

## Issues to Address

### High Priority:
1. **Multiple Ideas Timeout**: `--top-ideas 3` times out after 3 minutes with real API
2. **Top Ideas Limit**: Current system allows 1-10 ideas, but should be limited to 5 maximum

### Medium Priority:
3. **Simple Mode Formatting**: Shows identical original/improved text when no meaningful improvement occurred
4. **Brief Mode Text Artifacts**: Occasional "Here's the version of your idea" suggests improved version being shown instead of original

## Solution Strategy

### 1. Fix Multiple Ideas Timeout (High Priority)

**Root Cause**: The current sync coordinator processes each idea sequentially through the full multi-agent workflow (IdeaGenerator → Critic → Advocate → Skeptic → Improve → Re-evaluate). With 5 ideas, this means 5 × (6 API calls) = 30 API calls in sequence, taking 3+ minutes.

**Solution**: 
- Switch to AsyncCoordinator for `--top-ideas > 1` to enable parallel processing
- Implement intelligent batching: process advocate/skeptic agents in parallel per idea
- Add progress indicators to show user the system is working
- Set realistic time expectations in help text (up to 5 minutes for 5 ideas)

**Implementation**:
- Modify CLI to auto-enable async mode when `--top-ideas > 1`
- Add progress callback to show "Processing idea X of Y..."
- Update help text to mention processing time up to 5 minutes for multiple ideas
- Ensure timeout is set to at least 300 seconds (5 minutes) for multiple ideas

### 2. Limit Top Ideas to Maximum 5 (High Priority)

**Current State**: CLI accepts 1-10 ideas but user specifies maximum should be 5

**Solution**:
- Change `choices=range(1, 11)` to `choices=range(1, 6)` in CLI argument parser
- Update help text to reflect "1-5" range
- Ensure AsyncCoordinator can handle 5 ideas efficiently within 5-minute limit

### 3. Fix Simple Mode Formatting (Medium Priority)

**Root Cause**: When the improvement process doesn't generate meaningful changes (e.g., API returns identical text), the simple mode still shows both original and "improved" versions, confusing users.

**Solution**:
- Add logic to detect when original and improved ideas are identical/very similar
- When no meaningful improvement occurred, show only the original with a note like "Already well-developed - no improvements needed"
- Use similarity scoring to determine if improvement is meaningful (>10% text difference)

### 4. Fix Brief Mode Text Artifacts (Medium Priority)

**Root Cause**: The improved_idea_cleaner sometimes leaves artifacts like "Here's the version of your idea" when cleaning AI-generated text.

**Solution**:
- Add additional cleaner patterns to remove common AI response prefixes
- Specifically target phrases like "Here's the version", "Here's an improved version", etc.
- Ensure the cleaner removes meta-commentary that references the improvement process

## Implementation Steps

1. **Update CLI argument constraints** (5 minutes)
   - Change top-ideas range from 1-10 to 1-5
   - Update help text to reflect 5-minute processing time for multiple ideas

2. **Implement async mode auto-switching** (20 minutes)
   - Modify main() to use AsyncCoordinator when top-ideas > 1
   - Add progress callbacks for user feedback
   - Ensure timeout is properly set to 300+ seconds for multiple ideas

3. **Enhance simple mode logic** (10 minutes)
   - Add similarity detection between original and improved ideas
   - Show appropriate messaging when no improvement occurred

4. **Improve text cleaning patterns** (10 minutes)
   - Add regex patterns to remove AI response artifacts
   - Test with common AI response prefixes

5. **Update documentation** (5 minutes)
   - Update help text to reflect new limits and async behavior
   - Add realistic time expectation notes (up to 5 minutes)

## Expected Outcomes

- Multiple ideas generation completes within 5 minutes instead of timing out
- Top ideas limited to practical maximum of 5
- Simple mode provides clearer feedback when improvements aren't meaningful
- Brief mode text is cleaner without AI response artifacts
- Better user experience with progress feedback for longer operations
- Realistic user expectations about processing time

## Testing Plan

- Test `--top-ideas 5` with real API to ensure it completes under 5 minutes
- Verify simple mode handles identical original/improved scenarios gracefully
- Confirm brief mode text is clean of artifacts
- Test all output modes work correctly with new async processing
- Verify timeout handling works correctly for extended processing times

## Files to Modify

1. `src/madspark/cli/cli.py` - CLI argument parsing, async mode switching, timeout handling
2. `src/madspark/cli/cli.py` - Simple mode formatting logic
3. `src/madspark/utils/constants.py` - Add new cleaner patterns for text artifacts
4. `src/madspark/core/async_coordinator.py` - Ensure proper progress callbacks and timeout handling