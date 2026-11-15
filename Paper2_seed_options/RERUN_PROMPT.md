# Prompt: rerun the drug-repurposing analysis from public inputs only

**Setup before pasting the prompt:**
1. Clone the current repository as a read-only reference:
   `git clone https://github.com/knarendrakumar187/Drug_Repurposing old_reference`
2. Make a new, empty folder for the new work, e.g. `Paper2_PublicRun/`, and `git init` it.
   This becomes the new repository for the paper.
3. Unzip `Paper2_seed_options.zip` into `Paper2_PublicRun/Paper2_seed_options/`.
4. Open Claude Code (or another coding agent) in `Paper2_PublicRun/` and paste everything
   below the line.

---

You are helping me rerun our knowledge-graph drug-repurposing analysis for NAFLD/liver
fibrosis so that **every input is public and citable**. The method stays the same as our
existing pipeline, but several inputs must be replaced.

- **Old pipeline (read-only reference):** `../old_reference/` (code in
  `../old_reference/Paper2_Results/code/` and `../old_reference/scripts/`).
- **New work:** everything goes in the current folder (`Paper2_PublicRun/`), which will become
  a new public repository.

Work carefully, step by step, and **stop and ask me whenever something is unclear**. Never
guess.

## 1. The rule that matters most

The new run must not read, copy or depend on any in-house patient-derived result. Do **not**
use any of these, directly or indirectly:

- **Old graphs.** The `liver_graph` graph release (`graph-export-2026-11-05`, its dump or CSV
  ZIP), any existing Neo4j database built from it, and `old_reference/scripts/rebuild_graph.py`
  / `prepare_graph_release.py`. That graph holds an expression layer and `TRACKS_FIBROSIS` /
  `TRACKS_INFLAMMATION` links that must not be used.
- **Old input folders.** Anything under `old_reference/Paper1_HighConfidence/` or
  `old_reference/Paper1_Results/`, or files named like `*progression_genes*`,
  `11_final_all_3845_genes.csv`, `11_FINAL_shortlist_*`, `10_loso_all_eligible_runs.csv`,
  `task2_gene_clusters.csv` or `task4_all_significant.csv`.
- **Old Paper 2 results.** Every result file under `old_reference/Paper2_Results/`, including the
  "saved evidence" tables (`New_drug_gene_links/`, `Task7_external_layer/`,
  `Task4/graph_write/indication_pairs_plan.csv`, `Recovery2_ChEMBL/graph_gap_properties.csv`).
  Those drug links, directions and indications were selected using the old gene list, so they
  must be searched again for the new seed genes.
- **Concepts from those results.** Tier 1/2/3, the 23-gene shortlist, clusters C1–C5, F0–F4
  values, `Largest_transition`, and the 6,222 / 3,845 / 14,794 gene lists.

Reusing **code** is fine. Reusing **results** is not. Whenever an old script reads one of the
files above, replace that input with the public one described below. Don't copy any old
README text that mentions the companion study, Paper 1 or the old graph release.

## 2. Public inputs

| Input | Where |
|---|---|
| OptimusKG parquet files (gene, drug, disease, pathway, biological_process, phenotype and their edge files) | Harvard Dataverse, DOI 10.7910/DVN/IYNGEV. Record the version and download date. |
| Seed genes (Gene\*): `Paper2_seed_options/seed_genes_main_Ryaboshapkina2017.csv` (280 genes) | From Ryaboshapkina & Hammar, *Sci Rep* 2017;7:12361, Supplementary Table S2 (CC BY 4.0). Read `Paper2_seed_options/README.md`. |
| Optional add-on: `Paper2_seed_options/seed_genes_optional_GWAS_Catalog.csv` | GWAS Catalog, downloaded 2026-11-11 |
| Drug–target links and directions | ChEMBL (REST API), DGIdb 5, GtoPdb, Open Targets: the same sources and search code as before, queried again now. Record each source's version and query date; they may be newer than before. |
| KEGG (legacy) and Hallmark pathways | MSigDB 2024.1 GMT files: `c2.cp.kegg_legacy.v2024.1.Hs.symbols.gmt` **and** `h.all.v2024.1.Hs.symbols.gmt`. Hallmark is needed now because the old graph is no longer the source. |
| Pathway–NAFLD curation | CTD `CTD_diseases_pathways.csv.gz` (NAFLD = MESH:D065626); `old_reference/scripts/fetch_rebuild_inputs.py` can download it |

Seed file columns used: `gene`, `ensembl_id`, `main_stage`, `all_stages`, `direction`
(`increasing` / `decreasing` / `mixed` / `not_applicable`), `usable_for_metapath`.

## 3. Workspace rules

- In the current folder, create subfolders `code/`, `data/` (git-ignored for large or licensed
  inputs), `results/` and `logs/`. Copy the scripts you need from `../old_reference/` into
  `code/` and edit only the copies. Never change anything in `../old_reference/`.
- Create a **new, empty Neo4j database** (for example `paper2public`, or a separate instance
  on Community edition) and write only to it. Before every write, check that the target
  database is `paper2public`. Keep the old habits: dry run first, then `--apply`, an undo file,
  and a write log with node and relationship counts before and after.
- `old_reference/scripts/run_analysis.py` refuses to run unless the graph has the old graph's
  exact size. Write a new runner `code/run_analysis.py` that checks this run's own expected
  counts instead.
- Keep OptimusKG, KEGG and CTD files out of git (licence terms); commit code, seed files and
  results only.
- Every number reported must come from a file or query of this run. Do not reuse old numbers.
- Make the output fully separate: no old result files in any folder of this run.

## 4. What to do, in order

Keep the old relationship names (`ACTS_ON`, `INTERACTS_WITH`, `IN_PATHWAY`, `TREATS`,
`OFF_LABEL_FOR`, `CONTRAINDICATED_IN`, `IMPLICATED_IN`, `ASSOCIATED_WITH`) and node
properties (`node_id`, `symbol`, `name`) so the copied scripts work with few changes.

### Step 0: build the graph fresh from OptimusKG

- **0.0 Import OptimusKG.** Write a new importer for the parquet files:
  - **Nodes:** all genes (`symbol`, `ensembl_id`), drugs, diseases, pathways, biological
    processes and phenotypes.
  - **Edges:**
    - drug_gene → `ACTS_ON`, keeping `relation` as `action` and the `properties`
      (sources, mechanisms_of_action, source_ids, source_urls)
    - gene_gene → `INTERACTS_WITH`
    - pathway_gene → `IN_PATHWAY`
    - drug_disease: INDICATION → `TREATS`, OFF_LABEL_USE → `OFF_LABEL_FOR`,
      CONTRAINDICATION → `CONTRAINDICATED_IN`
    - disease_gene → `ASSOCIATED_WITH` with `evidence_score` stored
    - plus the disease_disease, disease_phenotype and biological_process_gene edges
  - **Drug metadata:** load it at import time (SMILES, molecule type, phase, sources), so the
    old "recover from OptimusKG" steps (0.1, 0.3) aren't needed.
  - **Count check:** report node and edge counts per type and check they equal the parquet row
    counts after any documented filtering.
  - **No other layers:** no expression layer and no progression links.
- **0.2 Fill missing drug metadata from ChEMBL.** Use the same logic as
  `old_reference/scripts/paper2_fetch_chembl_gaps.py`, with OptimusKG values taking
  precedence. Query ChEMBL freshly; don't reuse `graph_gap_properties.csv`.
- **0.4 New drug–gene links from ChEMBL, DGIdb, GtoPdb and Open Targets.** Rerun the search in
  `old_reference/Paper2_Results/code/new_links_search.py` (with the same source filters and the
  same curation rules as `new_links_report.py`), but for the **280 seed genes** instead of the
  old gene list.
  - **Fresh queries.** The old raw caches aren't in the repository, so query the sources again.
    Cache the raw downloads under `data/raw/` and record versions and dates.
  - **Writing.** Write the links as `ACTS_ON` with `layer = 'added curated drug-target links'`,
    `sources`, `action_labels`, `push` and `mechanism`.
- **0.5 External directions.** For OptimusKG `ACTS_ON` links on the seed genes that have no
  direction (TARGET / ENZYME / TRANSPORTER / CARRIER), look up GtoPdb, DGIdb and ChEMBL as
  before and store the result as `external_action_*`.
- **0.6 Pathways.** Add KEGG legacy and Hallmark from the MSigDB 2024.1 GMT files as `Pathway`
  nodes with `IN_PATHWAY` links. Reuse the parsing logic of `old_reference/scripts/restore_kegg.py`,
  but not its expected counts, and don't link KEGG to NAFLD here (that's step 0.7).
- **0.7 Pathway → NAFLD links (`IMPLICATED_IN`).** The old main link used in-house enrichment
  results, so replace it with enrichment of the **seed genes**:
  - **Test:** hypergeometric test for Reactome, KEGG and Hallmark.
  - **Background:** all genes with at least one `IN_PATHWAY` link in this graph.
  - **Correction:** BH-FDR < 0.05.
  - **Gene groups tested:** all histology seed genes; each stage (`1_steatosis`, `2_NASH`,
    `3_fibrosis`, `4_HCC`); and each stage × direction (increasing / decreasing).
  - **Rule:** a pathway is linked to NAFLD (EFO_0003095) only if it is significant in at least
    one group **and** CTD links it to NAFLD (MESH:D065626) through at least 2 curated genes.
    This keeps the old two-source rule.
  - **Report:** the number of links. If fewer than 20 pathways pass, stop and tell me; don't
    change the rule yourself.
- **0.8 Indications for added drugs.** For drugs added in 0.4, fetch their ChEMBL indications
  (the logic of `task4_added_drug_indications.py`; record the ChEMBL release) and add them as
  `TREATS`, as before. Don't reuse `indication_pairs_plan.csv`.
- **Graph report.** Report final node and relationship counts and the relationship types.

### Task 1: seed gene table

A table of the 280 seed genes with their stage, direction and OptimusKG connections. Report
the counts per stage and direction.

### Task 2: drug–gene links on the seed genes

All `ACTS_ON` links to seed genes, with action and source. Use the same direction logic as the
old Task 2:

- **Drug direction:** comes from the link's own action. If OptimusKG gives none, use the
  `external_action_direction` stored on the same link.
- **Gene direction:** `increasing` → positive, `decreasing` → negative. `mixed` and
  `not_applicable` → no gene direction.

Report the number of links, genes, drugs, and links with a known direction.

### Task 3: druggability

Druggability of the seed genes, overall and by stage, against a background of **all OptimusKG
genes that have at least one `INTERACTS_WITH` partner** (report the size). Use Fisher's exact
test with BH-FDR, plus 1,000 degree-matched permutations (seed 42), and the same druggable
definition as before (pharmacological-target links only).

### Task 4: candidate drugs

Same coverage table and the same candidate filter as before:

- phase ≥ 2 → not withdrawn → no existing fibrosis-type liver use (graph `TREATS` +
  ChEMBL indications) → mechanism annotated

Report every step of the funnel. The old `task4_drug_coverage.py` adds a
`main_paper1_pathway` column from `task4_all_significant.csv`; drop it, or replace it with each
seed gene's most significant pathway from your step 0.7 enrichment.

### Direction filter

The same rule as before:

- **Direction-consistent link:** the drug switches down an increasing gene, or switches up a
  decreasing gene.
- **Drugs kept:** only drugs whose **every** link with a known direction is direction-consistent
  ("only consistent"). Report the numbers for only-consistent, mixed and only-inconsistent.

### Metapaths

Same code and the same 4 rules as before, with the seed genes as Gene\*:

- **B:** Drug -ACTS_ON-> Gene -INTERACTS_WITH- Gene\* -IN_PATHWAY-> Pathway -IMPLICATED_IN-> NAFLD
- **BB:** Drug -ACTS_ON-> Gene1 -INTERACTS_WITH- Gene2 -INTERACTS_WITH- Gene\* -IN_PATHWAY-> Pathway -IMPLICATED_IN-> NAFLD
- **Rules:**
  1. routes start only from the drug's direction-consistent targets
  2. in-between genes have ≤ 500 interaction partners
  3. pathway size is 5–200 genes
  4. Gene1, Gene2 and Gene\* are different genes, and the drug has no `TREATS` /
     `OFF_LABEL_FOR` link to NAFLD, NASH or cirrhosis of liver
- **Runs (replace the old tier runs):**

| Run | Gene\* set |
|---|---|
| RunA (main result) | all 280 seed genes |
| RunB | the 228 histology genes (exclude `main_stage == 0_genetic_risk`) |
| RunC | genes with `3_fibrosis` in `all_stages` |
| RunD (optional) | 280 seed genes + GWAS add-on genes (stage `0_genetic_risk`, no direction) |

- **Stage label:** each route's Gene\* stage = `main_stage` from the seed file. Drop the old
  F0–F4 columns.

### Ranking

Same as before, for each run:

- direct diseases of the BB drugs
- keep drugs with ≥ 1 `TREATS` link to a liver disease
- remove drugs contraindicated in any liver disease
- rank by BB routes
- stage table for ranks 1–25 (ties kept), with routes per stage `0_genetic_risk` … `4_HCC`
  instead of F0→F1 … F3→F4

Then compare the top 25 across runs.

## 5. Output

In `Paper2_PublicRun/results/`, the same kinds of files as the old run (per run: routes,
BB routes, direct diseases, final ranked drugs, stage table), plus
`Paper2_PublicRun/README.md` with:

- a step table (what was done, result numbers, code, output file)
- the run table (drugs with B routes, BB routes, drugs with BB routes, treat a liver disease,
  removed, final ranked drugs)
- all source versions and download dates
- points for the manuscript: direction is checked only at the drug → target step;
  gene–gene links have no sign; results are repurposing hypotheses, not treatments

The README and all outputs must describe only this run, with no mention of any other analysis.

## 6. Final audit (do this before saying you are done)

1. Search `Paper2_PublicRun/` code for any path or name listed in section 1, and show me the
   result (it must be empty).
2. Query `paper2public` to prove there are no expression nodes and no `TRACKS_*`
   relationships, and list all node labels and relationship types.
3. Confirm that every Gene\* in the route files is in the seed file.
4. Check that funnel numbers add up and that the README numbers match the files.
5. Rerun the metapath and ranking steps once from scratch, and confirm the final ranked list
   is identical.

## 7. How to work with me

1. First, read the old code and give me a short plan: which scripts you will copy, and exactly
   which input each one changes. **Wait for my OK.**
2. Then go one step at a time (Step 0 → Tasks 1–4 → Direction → Metapaths → Ranking). After
   each step, show the key numbers and any problem, and wait for my OK before the next step.
3. If a step gives far fewer results than expected (for example very few drugs or routes),
   report it. Don't loosen any rule without asking me.
