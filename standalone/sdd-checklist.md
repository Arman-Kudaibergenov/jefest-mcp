# SDD Validation Checklist

- [ ] Has `## Context` section (non-empty)
- [ ] Has `## Environment` section with project path
- [ ] Has `## Atomic Tasks` section with numbered steps
- [ ] Step 1 is worktree creation (for change tasks)
- [ ] Has `## Acceptance` section with concrete conditions
- [ ] Has `## Finalize` section
- [ ] Finalize includes commit + push step
- [ ] Finalize includes result-JSON step (result-<project>.json)
- [ ] Finalize ends with /exit
- [ ] Has `## Files` section listing affected files
- [ ] (optional) Has `## Compatibility` section with OS and profile
