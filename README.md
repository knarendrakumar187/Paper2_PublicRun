# Knowledge-graph drug repurposing for NAFLD / liver fibrosis from public inputs

This repository rebuilds a drug-repurposing knowledge graph for non-alcoholic fatty liver disease (NAFLD) and liver fibrosis
from public, citable sources only, and searches it for drugs whose action opposes the disease direction of published
NAFLD signature genes. All results are **repurposing hypotheses, not treatments**.

## Inputs and versions

| Input | Version / release | Retrieved | Use |
|---|---|---|---|
| OptimusKG (Harvard Dataverse, doi:10.7910/DVN/IYNGEV) | v3.2 (released 2026-09-09), licence CC BY-NC-SA 4.0 | 2026-11-13 | base graph (37 node/edge parquet files) |
| Seed genes: Ryaboshapkina & Hammar, Sci Rep 2017;7:12361, Suppl. Table S2 (CC BY 4.0) | `Paper2_seed_options/seed_genes_main_Ryaboshapkina2017.csv` | - | Gene* (280 genes) |
| GWAS Catalog liver hits (optional add-on) | `Paper2_seed_options/seed_genes_optional_GWAS_Catalog.csv` | 2026-11-11 | RunD only |
| MSigDB KEGG legacy + Hallmark | 2024.1.Hs | 2026-11-13 | pathways (step 0.6) |
| CTD diseases-pathways | Report created: Thu Oct 29 12:36:38 EDT 2026 | 2026-11-13 | NAFLD pathway curation (step 0.7) |
| ChEMBL REST API | ChEMBL_37 (2026-05-01), REST API | step 0.2-0.8 | drug metadata, mechanisms, indications |
| IUPHAR/BPS Guide to Pharmacology | GtoPdb Version: 2026.3.1 - published: 2026-10-12 (downloaded 2026-11-13T18:53:33+00:00) | | drug-target links, directions |
| DGIdb | 5, https://dgidb.org/data/latest/interactions.tsv (downloaded 2026-11-13T18:54:28+00:00) | | drug-target links, directions |
| Open Targets Platform | Open Targets Platform 26.09 | | drug-target links |

URLs, download times and SHA-256 checksums of the downloaded files: `data/SOURCES.json` (the `data/` folder is not in git
because of licence terms; `python code/download_inputs.py` downloads it again).

## Steps

| Step | What was done | Result | Code | Output |
|---|---|---|---|---|
| D | download public inputs, check type/size, record checksums | 40 files | `download_inputs.py` | `data/SOURCES.json` |
| 0.0 | import OptimusKG genes, drugs, diseases, pathways, biological processes, phenotypes and their edges into Neo4j `paper2public` (no expression layer) | 164,599 nodes, 10,579,970 relationships; counts equal the parquet rows (142 disease-tree rows pointing to phenotype terms left out) | `import_optimuskg.py` | `results/graph_build/step0_0_import/` |
| 0.2 | fill missing drug metadata from ChEMBL (OptimusKG values take precedence) | 2,696 drugs filled | `fetch_chembl_gaps.py` | `step0_2_chembl_gaps/` |
| 0.4 | new curated drug-target links for the seed genes from GtoPdb, DGIdb, ChEMBL, Open Targets | 110 links, 31 new Drug nodes | `new_links_search.py`, `write_new_links_to_graph.py` | `step0_4_new_links/` |
| 0.5 | drug directions for seed-gene OptimusKG links without one (GtoPdb, DGIdb, ChEMBL) | 62 of 1,257 links resolved | `external_action_check.py` | `step0_5_external_directions/` |
| 0.6 | KEGG legacy + Hallmark pathways | 236 pathways, 20,067 memberships | `load_pathways.py` | `step0_6_pathways/` |
| 0.7 | Pathway -IMPLICATED_IN-> NAFLD from seed-gene enrichment (hypergeometric, BH-FDR < 0.05) + CTD | 12 links (see below) | `pathway_nafld_links.py` | `step0_7_pathway_nafld/` |
| 0.8 | ChEMBL indications of the drugs added in 0.4, as TREATS | 335 links | `added_drug_indications.py` | `step0_8_added_drug_indications/` |
| Task 1 | seed gene table | 280 genes, 233 usable for metapaths | `task1_seed_gene_table.py` | `results/Task1/` |
| Task 2 | drug-gene links on seed genes | 1,659 links, 1,242 drugs, 105 genes, 400 with known drug direction | `task2_drug_gene_edges.py` | `results/Task2/` |
| Task 3 | druggability (pharmacological target) vs 18,453 genes with a gene-gene partner | all seed genes 36.2% vs 18.8% expected (degree-matched) | `task3_druggability.py` | `results/Task3/` |
| Task 4 | coverage table + candidate filter | 321 mechanism-annotated candidates | `task4_drug_coverage.py` | `results/Task4/` |
| Direction | keep drugs whose every decided link is direction-consistent | 115 only consistent, 0 mixed, 43 only inconsistent, 163 no decided link | `direction_consistent_drugs.py` | `results/Direction_consistent_drugs/` |
| Metapaths | B and BB routes, 4 runs | see run table | `metapaths.py` | `results/Metapath_runs/` |
| Ranking | liver-treating drugs ranked by BB routes; stage tables; top-25 comparison | see run table | `ranking.py` | `results/Metapath_runs/` |

### Final graph (`paper2public`)

| Node label | Count |
|---|---|
| BiologicalProcess | 25,754 |
| Disease | 36,753 |
| Drug | 18,671 |
| Gene | 61,306 |
| Pathway | 3,041 |
| Phenotype | 19,341 |

| Relationship type | Count |
|---|---|
| ACTS_ON | 36,721 |
| ASSOCIATED_WITH | 9,734,774 |
| CONTRAINDICATED_IN | 11,379 |
| HAS_PHENOTYPE | 157,144 |
| IMPLICATED_IN | 12 |
| INTERACTS_WITH | 327,924 |
| IN_PATHWAY | 67,044 |
| OFF_LABEL_FOR | 827 |
| PARENT_OF | 47,750 |
| PARTICIPATES_IN | 158,410 |
| TREATS | 58,509 |

### Seed genes by stage and direction

| main_stage | increasing | decreasing | not_applicable | all |
|---|---|---|---|---|
| 0_genetic_risk | 0 | 0 | 52 | 52 |
| 1_steatosis | 10 | 3 | 0 | 13 |
| 2_NASH | 56 | 27 | 0 | 83 |
| 3_fibrosis | 93 | 29 | 0 | 122 |
| 4_HCC | 1 | 9 | 0 | 10 |
| all | 160 | 68 | 52 | 280 |

### Pathway -> NAFLD links (step 0.7)

Enrichment found 23 significant pathways (Hallmark 6, KEGG 3, Reactome 14);
9 of them are linked to NAFLD in CTD. Rule used: a significant Reactome or KEGG pathway is linked only if
CTD links it to NAFLD (MESH:D065626) through >= 2 curated genes; a significant Hallmark set is linked on enrichment alone,
because CTD has no Hallmark pathways. The strict two-source rule for all databases would give 6 links.

| Pathway | Database | Best q | Basis |
|---|---|---|---|
| Epithelial mesenchymal transition | Hallmark | 2e-06 | enrichment only (Hallmark, no CTD coverage) |
| Focal adhesion | KEGG | 0.0013 | enrichment + CTD |
| ECM proteoglycans | Reactome | 0.0018 | enrichment + CTD |
| Non-integrin membrane-ECM interactions | Reactome | 0.0023 | enrichment + CTD |
| Angiogenesis | Hallmark | 0.0043 | enrichment only (Hallmark, no CTD coverage) |
| Syndecan interactions | Reactome | 0.0044 | enrichment + CTD |
| Xenobiotic metabolism | Hallmark | 0.011 | enrichment only (Hallmark, no CTD coverage) |
| Extracellular matrix organization | Reactome | 0.014 | enrichment + CTD |
| E2F targets | Hallmark | 0.021 | enrichment only (Hallmark, no CTD coverage) |
| MTORC1 signaling | Hallmark | 0.025 | enrichment only (Hallmark, no CTD coverage) |
| Chemokine signaling pathway | KEGG | 0.032 | enrichment + CTD |
| Hypoxia | Hallmark | 0.047 | enrichment only (Hallmark, no CTD coverage) |

### Candidate funnel (Task 4)

| Step | Drugs |
|---|---|
| Drugs with >= 1 link to a seed gene (any action) | 1,242 |
| ... with >= 1 pharmacological-target link (coverage table) | 814 |
| ... max phase >= 2 | 580 |
| ... and not withdrawn | 562 |
| ... and no existing fibrosis-type liver use = repurposing candidates | 516 |
| ... and mechanism annotated = main list | 321 |

## Run table

Metapaths: **B** Drug -ACTS_ON-> Gene -INTERACTS_WITH- Gene\* -IN_PATHWAY-> Pathway -IMPLICATED_IN-> NAFLD and
**BB** Drug -ACTS_ON-> Gene1 -INTERACTS_WITH- Gene2 -INTERACTS_WITH- Gene\* -IN_PATHWAY-> Pathway -IMPLICATED_IN-> NAFLD,
for the 115 only-consistent drugs. Rules: routes start only at direction-consistent targets; in-between
genes have <= 500 partners; pathway size 5-200; Gene1, Gene2 and Gene\* differ, and the drug has no TREATS / OFF_LABEL_FOR
link to NAFLD, NASH or cirrhosis of liver.

| Run | Gene\* set | Gene\* | Drugs with B routes | BB routes | Drugs with BB routes | Treat a liver disease | Removed (liver contraindication) | Final ranked drugs | Secondary list |
|---|---|---|---|---|---|---|---|---|---|
| RunA (main result) | all 280 seed genes | 280 | 44 | 5,025 | 44 | 2 | 1 | **1** | 38 |
| RunB | histology genes (main_stage != 0_genetic_risk) | 228 | 37 | 2,675 | 37 | 0 | 0 | **0** | 35 |
| RunC | genes with 3_fibrosis in all_stages | 122 | 27 | 1,781 | 27 | 0 | 0 | **0** | 25 |
| RunD | 280 seed genes + GWAS Catalog add-on genes | 573 | 73 | 15,290 | 73 | 14 | 4 | **10** | 64 |

**Final ranked drugs** = drugs with >= 1 TREATS link to a liver disease and no CONTRAINDICATED_IN link to any liver disease,
ranked by BB routes (`<run>_BB_liver_treating_drugs_final.xlsx`). RunA: PACLITAXEL (rank 1).

**Secondary list** = all drugs with BB routes, not restricted to a current liver use, minus drugs contraindicated in any liver
disease (`<run>_BB_all_drugs_ranked.xlsx`; top 25 compared in `top25_comparison_all_drugs.md`). It was added because the
liver-treating requirement leaves very few drugs. RunA top 3: OCRIPLASMIN (633 BB routes), COLLAGENASE CLOSTRIDIUM HISTOLYTICUM (595 BB routes), PX-12 (130 BB routes).
23 drugs are in the secondary top 25 of all four runs.

Stage of a route = `main_stage` of its Gene\* (`0_genetic_risk` ... `4_HCC`); stage tables: `<run>_BB_top_drugs_stages.xlsx`
and `<run>_BB_all_drugs_top_stages.xlsx`.

## Points for the manuscript

- Direction is checked only at the drug -> target step (drug action vs the seed gene's disease direction).
- Gene-gene links (INTERACTS_WITH) have no sign, so the gene-gene steps of a route carry no direction.
- `0_genetic_risk` seed genes have no direction; links to them are never direction-consistent, so drugs acting only on them are
  not kept by the direction filter (they can still be reached as Gene\* in routes).
- Only 12 pathways connect to NAFLD; all routes end in these pathways, and many drugs share the same target (e.g. PPAR
  agonists), so route counts tie.
- Results are repurposing hypotheses for experimental follow-up, not treatments or evidence of benefit.

## Reproduce

1. `python code/download_inputs.py` (writes `data/`), set `NEO4J_PASSWORD`, create an empty Neo4j database `paper2public`.
2. Graph build, each with a dry run first and then `--apply`: `import_optimuskg.py`, `fetch_chembl_gaps.py`,
   `new_links_search.py` + `write_new_links_to_graph.py`, `external_action_check.py`, `load_pathways.py`,
   `pathway_nafld_links.py`, `added_drug_indications.py`. Each step writes a write log and an undo file.
3. `python code/run_analysis.py --stage all` (checks the graph against `results/graph_build/expected_graph_counts.json`,
   then runs Tasks 1-4, the direction filter, metapaths and ranking).
4. `python code/make_readme.py` regenerates this file from the results.

Python packages: `requirements.txt`. Final checks: `results/audit/`.
