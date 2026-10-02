# BactScout JOSS submission evidence checklist

Evidence checked 2 October 2026. This is a preparation record, not an editorial scope decision. JOSS editors make that decision. Public links below are the evidence to cite; statements marked for author confirmation must not be upgraded to established fact without confirmation.

## JOSS gates and current paper

The current [JOSS author guidance](https://joss.readthedocs.io/en/latest/submitting.html) requires demonstrated research use, more than six months of active public history, open-source practices, and iterative development. Its [paper format](https://joss.readthedocs.io/en/latest/paper.html) calls for Summary, Statement of need, State of the field, Software design, Research impact statement, AI usage disclosure, Acknowledgements, and References; the paper should be 750–1,750 words. The [author COI policy](https://joss.readthedocs.io/en/latest/policies.html#conflict-of-interest-policy-for-authors) requires conflict disclosure, while the [paper guidance](https://joss.readthedocs.io/en/latest/paper.html) requires acknowledgement of financial support. Confirm whether the sponsor was involved. JOSS requires AI tools, locations and scope of assistance, and human review/design responsibility to be disclosed; see its [AI usage policy](https://joss.readthedocs.io/en/latest/submitting.html#ai-usage-policy).

The draft at [`joss/paper.md`](paper.md) contains the required sections and a competing-interests declaration confirmed by the submitting author. Research-use wording, group authorship and the provisional AI disclosure still need final author review. The paper acknowledges NIHR133307; sponsor involvement remains to be confirmed. The 38-read example is not assigned to a particular institution or cohort.

## Evidence ledger

| Evidence and stage | Supported claim | Limitation |
|---|---|---|
| [Public releases](https://github.com/ghruproject/bactscout/releases) checked through the GitHub API: v1.0.0, 27 Oct 2025; v1.2.0, 5 Nov 2025; v1.3.0, 2 Jun 2026; v1.4.0, 3 Jul 2026; v1.4.1, 5 Sep 2026; [v1.4.2](https://github.com/ghruproject/bactscout/releases/tag/v1.4.2), 24 Sep 2026. | Release and feature-development records span more than six months; long-read functionality and subsequent user-driven corrections demonstrate iteration. | Historical release dates do not alone establish when a formerly private repository became public. The owner should confirm public availability over the required period; no public-from-inception claim is made. |
| [v1.4.0 release notes](https://github.com/ghruproject/bactscout/releases/tag/v1.4.0) credit [PR #21](https://github.com/ghruproject/bactscout/pull/21) to PovilasMat as a first contribution, preparing Bioconda packaging. The repository page currently reports 6 issues and 0 open PRs: [repository](https://github.com/ghruproject/bactscout). | There is at least one public, reviewed contribution from a named contributor and a public issue/PR path. | The release describes packaging preparation; it does not prove that a Bioconda package was published or used. The present issue/PR counts do not themselves establish sustained external discussion or adoption. Confirm the contributor’s relationship to the project and whether the public PR/history is complete enough for the submission narrative. |
| [QualiBact FAQ](https://qualibact.org/faq/) recommends BactScout as a read-level companion to its assembly QC. | A domain-specific referral supporting complementary use. | Related projects may share contributors. This is not evidence of independent laboratory adoption. |
| [Galaxy CoFest 2026 outcomes](https://galaxyproject.org/news/2026-07-20-gcc2026-cofest-outcomes/) lists “Tool wrapping & QC subworkflow for public health pathogen genomics,” to wrap and extend BactScout, with a lead and three named contributors. | External community interest and an integration effort in progress. | The BactScout entry has no outcome notes, code link, workflow, ToolShed release or deployment evidence. Describe as an initiative, not completed Galaxy integration or adoption. Obtain a public artifact and status from the project team before claiming implementation. |
| Preparation review located private primary evidence of BactScout use in sentinel surveillance before assembly QC and downstream analysis. | Actual research use is supported by correspondence held by the authors. | Authors must approve the public wording or provide evidence confidentially to editors. Private figures and correspondence are excluded from this repository. PathogenWatch integration is omitted because no primary implementation/deployment artifact was verified. |
| A 38-read BactScout run is reported in the project task record. | Evidence that a real run was performed and can support an operational example once the record is checked by the authors. | This is not a public artifact and does not establish a study cohort, institution, sample total, external adoption or research impact. Do not generalize from this run to a larger count or named organization. |

## Author confirmations before submission

- [ ] Final author review confirms the author list and affiliations are complete and current, the group-author listing is appropriate, and all coauthors agree to the submitted version. Keep private consent correspondence out of this repository checklist; no short contribution descriptions are requested here.
- [ ] Authors approve a public summary of the actual research use, or decide what primary evidence can be shown confidentially to JOSS editors. Confirm the research context and wording; disclose no counts or site names without explicit verification and approval.
- [ ] Complete an author-led inventory of generative AI use across code, tests, documentation and paper; identify tools/models and versions where known, scope, and human review/validation. Known use is already disclosed, so a no-AI-use statement would be incorrect.
- [ ] Confirm sponsor involvement and the completeness of the funding acknowledgement.
- [x] No competing interests confirmed by the submitting author on 2 October 2026 and incorporated into the paper.
- [x] Removed unsupported runtime, memory, linear-scaling and numerical test-coverage claims.

Optional evidence improvements, not prerequisites while the claims remain limited: obtain a completed Galaxy integration artifact or verify PathogenWatch deployment before adding either claim.

## Readiness acceptance criteria

- [ ] The paper contains every required JOSS section, is within the 750–1,750 word range, and every impact sentence maps to evidence in the ledger or to confirmed author evidence. Current draft contains the required headings; placeholders and provisional statements still need author resolution.
- [ ] Each impact statement is clearly labelled as recommendation, work in progress, deployed integration, or demonstrated use/adoption; no future intent is presented as realized impact.
- [ ] Public release and issue/PR history is checked directly before submission; active development demonstrably exceeds six months. No claim of “public from inception” is made solely from GitHub repository creation date.
- [ ] The repository remains installable and reviewable, with its license, tests/CI, documentation, contribution/support guidance, and stable release path. Reviewers can run the core workflow using documented example data.
- [ ] Every author confirmation above is resolved, the paper PDF is compiled and visually inspected, and the final version is agreed by all authors.

**Validation status:** See [validation.md](validation.md) for executed checks, exact scope and known limitations. The revised draft has been built using official Inara tooling. Final author approval and completion of the AI disclosure and sponsor-role statement remain outstanding.

## Submission handover

Use repository `https://github.com/ghruproject/bactscout` and paper path `joss/paper.md`. Select the branch/revision containing the reviewed preparation changes. The Q30 correction is currently unreleased; do not describe the existing 1.4.2 image as containing it. Before submission, choose and validate the software revision being reviewed and make the source, manuscript and reviewer instructions consistent.

The final accepted software release should be archived for a version-specific DOI at review completion. No new archive or JOSS submission has been created during preparation. Under the current JOSS AI policy, conversational exchanges with editors/reviewers must be handled by the authors without AI assistance except translation.
