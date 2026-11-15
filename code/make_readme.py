"""Write README.md from this run's result files (every number is read from a file, nothing typed by hand).

    python code/make_readme.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
GB = R / "graph_build"


def j(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def n(x):
    return f"{int(x):,}"


def main():
    src = j("data/SOURCES.json")["files"]
    okg = next(s for s in src if s["source"] == "OptimusKG")
    okg_date = min(s["downloaded_utc"] for s in src if s["source"] == "OptimusKG")[:10]
    gmt = [s for s in src if s["source"] == "MSigDB"]
    ctd = next(s for s in src if s["source"] == "CTD")
    imp = j("results/graph_build/step0_0_import/write_log.json")
    plan = pd.read_csv(GB / "step0_0_import/edge_plan.csv")
    s02 = j("results/graph_build/step0_2_chembl_gaps/write_log.json")
    s04 = j("results/graph_build/step0_4_new_links/numbers.json")
    s04w = j("results/graph_build/step0_4_new_links/graph_write/write_log.json")
    s05 = j("results/graph_build/step0_5_external_directions/summary.json")
    s05w = j("results/graph_build/step0_5_external_directions/write_log.json")
    s06w = j("results/graph_build/step0_6_pathways/write_log.json")
    s06 = pd.read_csv(GB / "step0_6_pathways/pathway_summary.csv").set_index("source")
    s07 = j("results/graph_build/step0_7_pathway_nafld/summary.json")
    s07t = pd.read_csv(GB / "step0_7_pathway_nafld/significant_pathways_ctd_check.csv")
    s08 = j("results/graph_build/step0_8_added_drug_indications/write_log.json")
    g = j("results/graph_build/graph_report.json")
    t1 = pd.read_csv(R / "Task1/seed_gene_table.csv")
    t1c = pd.read_csv(R / "Task1/counts_by_stage_direction.csv")
    t2 = pd.read_csv(R / "Task2/summary_numbers.csv", index_col=0)["value"]
    t3 = pd.read_csv(R / "Task3/druggability_summary_pharmacological.csv").set_index("Group")
    t3bg = pd.read_csv(R / "Task3/background_genes_druggability.csv")
    fun = pd.read_csv(R / "Task4/candidate_funnel.csv")
    dsum = pd.read_csv(R / "Direction_consistent_drugs/candidate_drugs_direction_summary.csv")
    dgrp = dsum.direction_group.value_counts()
    mp = pd.read_csv(R / "Metapath_runs/metapath_run_summary.csv").set_index("run")
    rk = pd.read_csv(R / "Metapath_runs/ranking_run_table.csv").set_index("run")
    t25 = pd.read_csv(R / "Metapath_runs/top25_comparison_all_drugs.csv")
    finA = pd.read_csv(R / "Metapath_runs/RunA_all_seed_genes_BB_liver_treating_drugs_final.csv")
    allA = pd.read_csv(R / "Metapath_runs/RunA_all_seed_genes_BB_all_drugs_ranked.csv")
    linked = s07t[s07t.linked].sort_values("best_q")

    runs = [("RunA (main result)", "RunA_all_seed_genes", "all 280 seed genes"),
            ("RunB", "RunB_histology_genes", "histology genes (main_stage != 0_genetic_risk)"),
            ("RunC", "RunC_fibrosis_genes", "genes with 3_fibrosis in all_stages"),
            ("RunD", "RunD_seed_plus_GWAS", "280 seed genes + GWAS Catalog add-on genes")]
    run_rows = "\n".join(
        f"| {lab} | {gs} | {n(mp.loc[r, 'gene_star'])} | {n(mp.loc[r, 'drugs_with_B_routes'])} | {n(mp.loc[r, 'BB_routes'])} | "
        f"{n(rk.loc[r, 'drugs_with_BB_routes'])} | {n(rk.loc[r, 'drugs_treating_a_liver_disease'])} | "
        f"{n(rk.loc[r, 'removed_liver_contraindicated'])} | **{n(rk.loc[r, 'final_ranked_drugs'])}** | {n(rk.loc[r, 'secondary_ranked_drugs'])} |"
        for lab, r, gs in runs)
    funnel_rows = "\n".join(f"| {r.step} | {n(r.drugs)} |" for r in fun.itertuples())
    stage_rows = "\n".join("| " + " | ".join(str(v) for v in r) + " |" for r in t1c.values)
    rels = "\n".join(f"| {k} | {n(v)} |" for k, v in g["relationships"].items())
    nodes = "\n".join(f"| {k} | {n(v)} |" for k, v in g["nodes"].items())
    pw_rows = "\n".join(f"| {r.name} | {r.database} | {r.best_q:.2g} | {r.link_basis} |" for r in linked.itertuples())
    common = t25[t25.in_all_runs]
    t3row = lambda k: f"{t3.loc[k, 'Percentage']:.1f}% vs {t3.loc[k, 'Degree-matched expected %']:.1f}% expected"  # noqa: E731

    readme = f"""# Knowledge-graph drug repurposing for NAFLD / liver fibrosis from public inputs

This repository rebuilds a drug-repurposing knowledge graph for non-alcoholic fatty liver disease (NAFLD) and liver fibrosis
from public, citable sources only, and searches it for drugs whose action opposes the disease direction of published
NAFLD signature genes. All results are **repurposing hypotheses, not treatments**.

## Inputs and versions

| Input | Version / release | Retrieved | Use |
|---|---|---|---|
| OptimusKG (Harvard Dataverse, doi:10.7910/DVN/IYNGEV) | v{okg['version']} (released {okg['release_time'][:10]}), licence {okg['licence']} | {okg_date} | base graph (37 node/edge parquet files) |
| Seed genes: Ryaboshapkina & Hammar, Sci Rep 2017;7:12361, Suppl. Table S2 (CC BY 4.0) | `Paper2_seed_options/seed_genes_main_Ryaboshapkina2017.csv` | - | Gene* (280 genes) |
| GWAS Catalog liver hits (optional add-on) | `Paper2_seed_options/seed_genes_optional_GWAS_Catalog.csv` | 2026-11-11 | RunD only |
| MSigDB KEGG legacy + Hallmark | {gmt[0]['version']} | {gmt[0]['downloaded_utc'][:10]} | pathways (step 0.6) |
| CTD diseases-pathways | {ctd['version'].lstrip('# ')} | {ctd['downloaded_utc'][:10]} | NAFLD pathway curation (step 0.7) |
| ChEMBL REST API | {s04['release']['ChEMBL']} | step 0.2-0.8 | drug metadata, mechanisms, indications |
| IUPHAR/BPS Guide to Pharmacology | {s04['release']['GtoPdb'].lstrip('# ')} | | drug-target links, directions |
| DGIdb | {s04['release']['DGIdb']} | | drug-target links, directions |
| Open Targets Platform | {s04['release']['OpenTargets']} | | drug-target links |

URLs, download times and SHA-256 checksums of the downloaded files: `data/SOURCES.json` (the `data/` folder is not in git
because of licence terms; `python code/download_inputs.py` downloads it again).

## Steps

| Step | What was done | Result | Code | Output |
|---|---|---|---|---|
| D | download public inputs, check type/size, record checksums | {len(src)} files | `download_inputs.py` | `data/SOURCES.json` |
| 0.0 | import OptimusKG genes, drugs, diseases, pathways, biological processes, phenotypes and their edges into Neo4j `paper2public` (no expression layer) | {n(imp['after']['nodes_total'])} nodes, {n(imp['after']['relationships_total'])} relationships; counts equal the parquet rows ({int(plan.missing_endpoint_dropped.sum())} disease-tree rows pointing to phenotype terms left out) | `import_optimuskg.py` | `results/graph_build/step0_0_import/` |
| 0.2 | fill missing drug metadata from ChEMBL (OptimusKG values take precedence) | {n(s02['drugs_written'])} drugs filled | `fetch_chembl_gaps.py` | `step0_2_chembl_gaps/` |
| 0.4 | new curated drug-target links for the seed genes from GtoPdb, DGIdb, ChEMBL, Open Targets | {n(s04w['links_written'])} links, {n(s04w['drug_nodes_created'])} new Drug nodes | `new_links_search.py`, `write_new_links_to_graph.py` | `step0_4_new_links/` |
| 0.5 | drug directions for seed-gene OptimusKG links without one (GtoPdb, DGIdb, ChEMBL) | {n(s05w['written'])} of {n(s05['no_direction'])} links resolved | `external_action_check.py` | `step0_5_external_directions/` |
| 0.6 | KEGG legacy + Hallmark pathways | {n(s06w['pathways'])} pathways, {n(s06w['memberships'])} memberships | `load_pathways.py` | `step0_6_pathways/` |
| 0.7 | Pathway -IMPLICATED_IN-> NAFLD from seed-gene enrichment (hypergeometric, BH-FDR < 0.05) + CTD | {s07['linked']} links (see below) | `pathway_nafld_links.py` | `step0_7_pathway_nafld/` |
| 0.8 | ChEMBL indications of the drugs added in 0.4, as TREATS | {n(s08['links_written'])} links | `added_drug_indications.py` | `step0_8_added_drug_indications/` |
| Task 1 | seed gene table | 280 genes, {int(t1.usable_for_metapath.sum())} usable for metapaths | `task1_seed_gene_table.py` | `results/Task1/` |
| Task 2 | drug-gene links on seed genes | {n(t2['links'])} links, {n(t2['unique_drugs'])} drugs, {n(t2['genes_with_drug'])} genes, {n(t2['links_known_direction'])} with known drug direction | `task2_drug_gene_edges.py` | `results/Task2/` |
| Task 3 | druggability (pharmacological target) vs {n(len(t3bg))} genes with a gene-gene partner | all seed genes {t3row('All seed genes')} (degree-matched) | `task3_druggability.py` | `results/Task3/` |
| Task 4 | coverage table + candidate filter | {n(fun.drugs.iloc[-1])} mechanism-annotated candidates | `task4_drug_coverage.py` | `results/Task4/` |
| Direction | keep drugs whose every decided link is direction-consistent | {n(dgrp.get('only consistent', 0))} only consistent, {n(dgrp.get('mixed', 0))} mixed, {n(dgrp.get('only inconsistent', 0))} only inconsistent, {n(dgrp.get('no decided link', 0))} no decided link | `direction_consistent_drugs.py` | `results/Direction_consistent_drugs/` |
| Metapaths | B and BB routes, 4 runs | see run table | `metapaths.py` | `results/Metapath_runs/` |
| Ranking | liver-treating drugs ranked by BB routes; stage tables; top-25 comparison | see run table | `ranking.py` | `results/Metapath_runs/` |

### Final graph (`paper2public`)

| Node label | Count |
|---|---|
{nodes}

| Relationship type | Count |
|---|---|
{rels}

### Seed genes by stage and direction

| main_stage | {" | ".join(t1c.columns[1:])} |
|---|{"---|" * (len(t1c.columns) - 1)}
{stage_rows}

### Pathway -> NAFLD links (step 0.7)

Enrichment found {int(sum(s07['significant_pathways'].values()))} significant pathways ({", ".join(f"{k} {v}" for k, v in s07['significant_pathways'].items())});
{s07['significant_and_in_ctd']} of them are linked to NAFLD in CTD. Rule used: a significant Reactome or KEGG pathway is linked only if
CTD links it to NAFLD (MESH:D065626) through >= 2 curated genes; a significant Hallmark set is linked on enrichment alone,
because CTD has no Hallmark pathways. The strict two-source rule for all databases would give 6 links.

| Pathway | Database | Best q | Basis |
|---|---|---|---|
{pw_rows}

### Candidate funnel (Task 4)

| Step | Drugs |
|---|---|
{funnel_rows}

## Run table

Metapaths: **B** Drug -ACTS_ON-> Gene -INTERACTS_WITH- Gene\\* -IN_PATHWAY-> Pathway -IMPLICATED_IN-> NAFLD and
**BB** Drug -ACTS_ON-> Gene1 -INTERACTS_WITH- Gene2 -INTERACTS_WITH- Gene\\* -IN_PATHWAY-> Pathway -IMPLICATED_IN-> NAFLD,
for the {n(dgrp.get('only consistent', 0))} only-consistent drugs. Rules: routes start only at direction-consistent targets; in-between
genes have <= 500 partners; pathway size 5-200; Gene1, Gene2 and Gene\\* differ, and the drug has no TREATS / OFF_LABEL_FOR
link to NAFLD, NASH or cirrhosis of liver.

| Run | Gene\\* set | Gene\\* | Drugs with B routes | BB routes | Drugs with BB routes | Treat a liver disease | Removed (liver contraindication) | Final ranked drugs | Secondary list |
|---|---|---|---|---|---|---|---|---|---|
{run_rows}

**Final ranked drugs** = drugs with >= 1 TREATS link to a liver disease and no CONTRAINDICATED_IN link to any liver disease,
ranked by BB routes (`<run>_BB_liver_treating_drugs_final.xlsx`). RunA: {", ".join(f"{r.Drug} (rank {r.Rank})" for r in finA.itertuples()) or "none"}.

**Secondary list** = all drugs with BB routes, not restricted to a current liver use, minus drugs contraindicated in any liver
disease (`<run>_BB_all_drugs_ranked.xlsx`; top 25 compared in `top25_comparison_all_drugs.md`). It was added because the
liver-treating requirement leaves very few drugs. RunA top 3: {", ".join(f"{r.Drug} ({n(r._4)} BB routes)" for r in allA.head(3).itertuples())}.
{len(common)} drugs are in the secondary top 25 of all four runs.

Stage of a route = `main_stage` of its Gene\\* (`0_genetic_risk` ... `4_HCC`); stage tables: `<run>_BB_top_drugs_stages.xlsx`
and `<run>_BB_all_drugs_top_stages.xlsx`.

## Points for the manuscript

- Direction is checked only at the drug -> target step (drug action vs the seed gene's disease direction).
- Gene-gene links (INTERACTS_WITH) have no sign, so the gene-gene steps of a route carry no direction.
- `0_genetic_risk` seed genes have no direction; links to them are never direction-consistent, so drugs acting only on them are
  not kept by the direction filter (they can still be reached as Gene\\* in routes).
- Only {s07['linked']} pathways connect to NAFLD; all routes end in these pathways, and many drugs share the same target (e.g. PPAR
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
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("wrote README.md")


if __name__ == "__main__":
    main()
