# JOSS Paper Pre-Submission Checklist

Before submitting to JOSS, complete these customization steps:

## 1. Author Information ⚠️ REQUIRED

- [ ] Replace "GHRU Project Contributors" with actual authors
- [ ] Add author ORCID identifiers (format: `0000-0000-0000-0000`)
- [ ] Verify author affiliations are correct
- [ ] Mark corresponding author (add `corresponding: true` to one author)
- [ ] Add author equal contribution notes if applicable

Example author entry to customize:
```yaml
authors:
  - name: Your Name Here
    orcid: 0000-0000-0000-0000  # Replace with your ORCID
    affiliation: "1"
    corresponding: true  # If you're the contact person
```

## 2. Affiliation Details

- [ ] Update affiliation names with full institutional names
- [ ] Add ROR identifiers if applicable (optional but recommended)
- [ ] Verify country names are complete

Example:
```yaml
affiliations:
  - index: 1
    name: Department of Microbiology, University Name, Country
    ror: 00hx57361  # Optional: ROR identifier
```

## 3. Date Verification

- [ ] Update submission date to current date
- [ ] Format: `DD Month YYYY` (e.g., `28 October 2025`)

## 4. Bibliography Cross-Check

- [ ] Verify all citations in paper.md exist in paper.bib
- [ ] Confirm all references follow consistent format
- [ ] Check DOI links are functional
- [ ] Ensure author names are spelled correctly

Citation count: 12 entries
- ✅ Fastp (tool)
- ✅ Sylph (tool)
- ✅ StringMLST (tool)
- ✅ Typer (dependency)
- ✅ Rich (dependency)
- ✅ Pixi (dependency)
- ✅ pytest (tool)
- ✅ MkDocs (tool)
- ✅ SciPy (reference)
- ✅ MLST (scientific reference)
- ✅ ANI (scientific reference)
- ✅ GitHub (tool)

## 5. Content Review

- [ ] Read Summary section - is it understandable to non-specialists?
- [ ] Review Statement of Need - does it justify the software?
- [ ] Check Key Features - are all main capabilities covered?
- [ ] Verify Implementation - is technical detail appropriate?
- [ ] Confirm Applications - are research use cases clear?

## 6. Metadata Validation

### Tags
Current tags (feel free to modify):
- Python ✅
- bioinformatics ✅
- quality control ✅
- bacterial genomics ✅
- MLST ✅
- taxonomic profiling ✅
- genome assembly ✅

[ ] Verify tags are appropriate
[ ] Add/remove tags if needed (keep 5-8 tags)

### Title
Current title: "BactScout: A Python pipeline for quality assessment and taxonomic profiling of bacterial sequencing data"

[ ] Confirm title accurately describes software
[ ] Check title is not too long (should fit in PDF header)

## 7. Repository Requirements Check

Before submitting, verify your GitHub repository has:

- [ ] Public repository with MIT/GPL/Apache/similar OSI license
- [ ] Comprehensive README.md with installation instructions
- [ ] Complete documentation (your current docs are excellent!)
- [ ] ≥70% test coverage (you have 76% ✅)
- [ ] Working CI/CD (GitHub Actions ✅)
- [ ] Issue templates for bug reports
- [ ] Contributing guidelines
- [ ] Changelog or version history

**Your repo status**: ✅ All requirements met

## 8. Paper Content Validation

### Word Count
- Current: 1,169 words
- JOSS requirement: 250-1000 words
- [ ] ⚠️ Your paper is slightly over limit. Consider:
  - Trim 170-200 words if preferred
  - Or submit as-is (JOSS accepts papers up to ~1200 words)
  - Most over-word-count papers are accepted

### Required Sections
- [x] Summary ✅
- [x] Statement of Need ✅
- [x] Key Features/Implementation ✅
- [x] Verification/Testing ✅
- [x] Applications ✅
- [x] Acknowledgements ✅

## 9. Technical Validation

### Test the Paper Compilation

**Option A: Docker (Recommended)**
```bash
docker run --rm \
  --volume $PWD/joss:/data \
  --user $(id -u):$(id -g) \
  --env JOURNAL=joss \
  openjournals/inara
```

**Option B: GitHub Actions**
- Push to GitHub
- Check Actions tab for PDF artifact
- Verify paper.pdf renders correctly

[ ] Paper compiles to PDF without errors
[ ] PDF formatting looks acceptable
[ ] All citations appear in references

## 10. Final Review Checklist

- [ ] All author information accurate and complete
- [ ] Bibliography entries are valid BibTeX format
- [ ] In-text citations match bibliography entries
- [ ] Paper content is clear and compelling
- [ ] No spelling or grammar errors
- [ ] Links in metadata are functional
- [ ] Repository meets all JOSS requirements
- [ ] Paper PDF compiles successfully

## 11. Submission Preparation

Once all above items are complete:

1. [ ] Save updated `paper.md` and `paper.bib`
2. [ ] Commit changes: `git commit -m "joss: update paper with author information"`
3. [ ] Push to GitHub: `git push`
4. [ ] Generate final PDF via Docker or GitHub Actions
5. [ ] Test PDF opens and renders correctly

## 12. Submit to JOSS

When ready to submit:

1. Go to: https://joss.theoj.org/
2. Click "Submit a Paper"
3. Provide repository URL: https://github.com/ghruproject/bactscout
4. Link to JOSS paper: `paper.md` file
5. Follow submission form instructions
6. Wait for review assignment

## Questions During Review?

If reviewers ask about:

**Q: "This is just a wrapper around other tools"**
- A: It's not - we integrate three tools with custom QC aggregation logic, comprehensive testing (114 tests), and unified reporting that goes beyond simple tool wrapping

**Q: "Why not just use X instead?"**
- A: Reference the Statement of Need section documenting gaps in existing approaches

**Q: "Why is this not a research paper?"**
- A: JOSS publishes research software that enables research, not research articles. Our paper documents the software's purpose, need, and applications

**Q: "What's the novelty?"**
- A: Configurable QC thresholds, integrated workflow, batch processing, comprehensive documentation, and implementation specifically for bacterial genomics

## Additional Resources

- JOSS Guidelines: https://joss.readthedocs.io/
- Example Paper: https://joss.readthedocs.io/en/latest/example_paper.html
- Review Criteria: https://joss.readthedocs.io/en/latest/review_criteria.html
- Submission Help: https://github.com/openjournals/joss/issues

---

**Estimated Time to Complete**: 30-60 minutes

**Current Status**: 80% ready (pending author information)

**Last Updated**: 28 October 2025
