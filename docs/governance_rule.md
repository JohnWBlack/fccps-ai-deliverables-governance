# FCCPS AI Committee Governance Rules

## Core Principle: Source of Truth First

### 1. Hierarchy of Authority

1. **Source of Truth (SoR)** - `sor/` directory YAML files
   - Primary authority for all committee data
   - Single source for workstreams, timeline, and deliverables
   - All edits must be made here first

2. **Supporting Documentation** - `docs/` directory
   - Schema definitions and governance rules
   - Explanatory documentation
   - Derived from SoR structure

3. **Derived Content** - `public/` directory
   - Generated from SoR, never edited directly
   - Public-safe snapshots for external consumption
   - Automatically stripped of internal fields

### 2. Edit Workflow

#### Chair-Managed Process
1. **Make Changes**: Edit YAML files in `sor/` directory
2. **Validate**: Run `python scripts/validate_sor.py`
3. **Build**: Run `python scripts/build_snapshot.py`
4. **Commit**: Commit both source changes and generated snapshot
5. **Push**: Update repository with traceable commit history

#### Traceability Requirements
- Every change must be committed with descriptive message
- No direct editing of generated files
- All edits must pass validation
- Cross-references must remain valid

### 3. Data Integrity Rules

#### Required Fields
- All entities must have required fields populated
- Date fields must follow YYYY-MM-DD format
- Status fields must use valid enum values

#### Cross-References
- Deliverables must reference valid workstream IDs
- Timeline events may reference workstream IDs
- No orphaned references allowed

#### Public Safety
- Internal notes are stripped from public snapshots
- Only deliverables marked `public_facing: true` appear publicly
- No email addresses or internal links in committed data

### 4. Future Enhancement Path

#### Committee Edit Proposals (Future)
- Core SoR structure remains unchanged
- Proposal system builds on existing YAML foundation
- Governance rules apply to all content types
- Validation ensures proposal integrity

#### Extensibility Principles
- New fields added to YAML schemas
- Backward compatibility maintained
- Public snapshot generation adapts automatically
- Validation scripts updated for new requirements

### 5. Quality Assurance

#### Automated Validation
- Syntax validation for all YAML files
- Required field validation
- Enum value validation
- Cross-reference validation

#### Manual Review
- Committee chair reviews all changes
- Public snapshot accuracy verified
- Governance compliance checked
- Documentation updated as needed

### 6. Access and Permissions

#### Repository Access
- Public repository for transparency
- Write access limited to committee chair
- Read access available to all stakeholders

#### Change Management
- All changes tracked via Git history
- Clear commit messages required
- Validation prevents invalid changes
- Rollback capability maintained

## Enforcement

These governance rules ensure:
- **Single Source of Truth**: No conflicting data sources
- **Traceability**: Complete audit trail of all changes
- **Quality**: Automated validation prevents errors
- **Transparency**: Public access to appropriate information
- **Future-Proofing**: Structure supports planned enhancements
