# Change Management Checklist

## What to Edit When a Workstream Deliverable Changes

### 1. Identify the Change Type

#### Workstream Changes
- [ ] **Edit `sor/workstreams.yml`**
  - Update workstream status
  - Modify target completion date
  - Change priority level
  - Update description or tags
  - Add/remove dependencies

#### Timeline Changes
- [ ] **Edit `sor/timeline.yml`**
  - Add new milestone or deadline
  - Update event status
  - Modify event dates
  - Change event importance

#### Deliverable Changes
- [ ] **Edit `sor/deliverables.yml`**
  - Update deliverable status
  - Modify due date
  - Change priority
  - Update public_facing flag
  - Edit internal notes

### 2. Validation Process

#### Run Validation
```bash
python scripts/validate_sor.py
```

- [ ] **Check validation output**
  - All required fields populated
  - Valid enum values used
  - Cross-references intact
  - Date formats correct

#### Fix Validation Errors
- [ ] **Address any validation failures**
  - Add missing required fields
  - Correct invalid enum values
  - Fix broken cross-references
  - Standardize date formats

### 3. Build Public Snapshot

#### Generate Snapshot
```bash
python scripts/build_snapshot.py
```

- [ ] **Verify snapshot generation**
  - No errors during build
  - Public data correctly sanitized
  - Internal fields removed

### 4. Update Documentation

#### Update Changelog
- [ ] **Edit `CHANGELOG_PUBLIC.md`**
  - Add entry for public-facing changes
  - Include version number if schema changed
  - Document new features or modifications

#### Update Schema Notes (if needed)
- [ ] **Edit `docs/schema_notes.md`**
  - Document new fields (if any)
  - Update validation rules
  - Modify field descriptions

### 5. Commit and Publish

#### Prepare Commit
```bash
git add sor/ public/public_snapshot.json CHANGELOG_PUBLIC.md docs/
git commit -m "Update deliverables: [brief description of changes]"
```

- [ ] **Review staged changes**
  - Source YAML files updated
  - Public snapshot regenerated
  - Documentation updated
  - No unintended changes

#### Push Changes
```bash
git push
```

- [ ] **Verify CI/CD pipeline**
  - Validation passes in GitHub Actions
  - Snapshot builds successfully
  - Auto-commit completes (if applicable)

## Quick Reference

### Common Change Scenarios

#### New Deliverable Added
1. Add entry to `sor/deliverables.yml`
2. Reference existing workstream ID
3. Set `public_facing: true` if public
4. Run validation
5. Build snapshot
6. Update changelog
7. Commit and push

#### Workstream Status Update
1. Update `status` field in `sor/workstreams.yml`
2. Update related deliverables if needed
3. Run validation
4. Build snapshot
5. Update changelog (if public-facing)
6. Commit and push

#### Timeline Milestone Added
1. Add entry to `sor/timeline.yml`
2. Reference workstream if applicable
3. Run validation
4. Build snapshot
5. Update changelog
6. Commit and push

#### Public-Facing Status Change
1. Update deliverable in `sor/deliverables.yml`
2. Toggle `public_facing` flag if needed
3. Run validation
4. Build snapshot
5. Update `CHANGELOG_PUBLIC.md`
6. Commit and push

## Validation Troubleshooting

### Common Errors
- **Missing required fields**: Add all required fields per schema
- **Invalid enum values**: Use values from `docs/schema_notes.md`
- **Broken cross-references**: Ensure workstream IDs exist
- **Invalid date format**: Use YYYY-MM-DD format

### Quick Fixes
- Run validation after each file edit
- Check ID uniqueness within files
- Verify workstream references in deliverables
- Ensure public-facing flag set correctly for public deliverables

## Governance Compliance

### Required Steps
- [ ] Source of Truth edited first
- [ ] Validation passes without errors
- [ ] Public snapshot regenerated
- [ ] Documentation updated
- [ ] Clear commit message
- [ ] Changes pushed to main branch

### Prohibited Actions
- ❌ Direct editing of `public/public_snapshot.json`
- ❌ Skipping validation
- ❌ Committing without descriptive message
- ❌ Breaking cross-references
- ❌ Including internal data in public snapshot
