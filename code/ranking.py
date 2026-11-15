"""Ranking: direct diseases, liver-treating drugs ranked by BB routes, stage tables, and the top-25 comparison.

For each run's BB output:
  <run>_BB_direct_diseases.xlsx         every direct TREATS / OFF_LABEL_FOR / CONTRAINDICATED_IN disease of the BB drugs
  <run>_BB_liver_treating_drugs_final.xlsx
      drugs with >= 1 TREATS link to a liver disease (Task 4 liver set), minus drugs CONTRAINDICATED_IN any liver
      disease, ranked by BB routes (ties share the lowest rank). Off-label use alone does not count.
  <run>_BB_top_drugs_stages.xlsx        final drugs ranked 1-25 (ties kept): BB routes per Gene* stage
                                        0_genetic_risk ... 4_HCC (main_stage of each route's Gene*)
  top25_comparison.csv / .md            top 25 across runs (main, liver-treating lists)
Secondary (user-approved 2026-11-15, because the liver-treating rule leaves very few drugs):
  <run>_BB_all_drugs_ranked.csv/.xlsx   ALL BB drugs, not restricted to a current liver use, minus drugs
                                        CONTRAINDICATED_IN any liver disease, ranked by BB routes (ties share rank)
  <run>_BB_all_drugs_top_stages.xlsx    stage table for that list, ranks 1-25 (ties kept)
  top25_comparison_all_drugs.csv / .md  top 25 of the secondary lists across runs
Read-only Neo4j.

    python code/ranking.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from neo4j_util import ROOT, driver, now, read_session  # noqa: E402

RUNS_DIR = ROOT / "results/Metapath_runs"
LIVER_SET = ROOT / "results/Task4/liver_disease_set.csv"
RUNS = {"RunA": "RunA_all_seed_genes", "RunB": "RunB_histology_genes", "RunC": "RunC_fibrosis_genes",
        "RunD": "RunD_seed_plus_GWAS"}
STAGES = ["0_genetic_risk", "1_steatosis", "2_NASH", "3_fibrosis", "4_HCC"]
TOP_RANK = 25
LINK = {"TREATS": "treats", "OFF_LABEL_FOR": "off-label for", "CONTRAINDICATED_IN": "contraindicated in"}


def join(s):
    return "; ".join(sorted(set(s.dropna())))


def follow_up(ses, run, liver_ids):
    stem = RUNS_DIR / f"{run}_BB"
    summ = pd.read_excel(f"{stem}.xlsx", sheet_name="Summary")
    routes = pd.read_csv(f"{stem}.csv")
    b_drugs = len(summ)
    bb = summ[summ["BB routes"] > 0][["Drug_ID", "Drug", "BB routes", "B routes"]]
    links = pd.DataFrame(ses.run("""UNWIND $ids AS id MATCH (d:Drug {node_id: id})-[r:TREATS|OFF_LABEL_FOR|CONTRAINDICATED_IN]->(x:Disease)
        RETURN id AS Drug_ID, type(r) AS rel, x.node_id AS disease_id, coalesce(x.name, x.node_id) AS Disease""",
                                 ids=list(bb.Drug_ID)).data(), columns=["Drug_ID", "rel", "disease_id", "Disease"])
    links = links.drop_duplicates(["Drug_ID", "rel", "disease_id"]).merge(bb[["Drug_ID", "Drug"]], on="Drug_ID")
    links["Link"] = links.rel.map(LINK)
    links["is_liver"] = links.disease_id.isin(liver_ids)

    S = bb.rename(columns={"BB routes": "Indirect routes to NAFLD"}).copy()
    for rel, col in [("TREATS", "Treats"), ("OFF_LABEL_FOR", "Off-label for"), ("CONTRAINDICATED_IN", "Contraindicated in")]:
        sub = links[links.rel == rel].groupby("Drug_ID").Disease
        S[f"{col.split()[0]} (n)"] = S.Drug_ID.map(sub.nunique()).fillna(0).astype(int)
        S[col] = S.Drug_ID.map(sub.agg(join)).fillna("")
    lv = links[links.is_liver]
    S["Liver-related direct links"] = S.Drug_ID.map(lv.assign(t=lv.Link + " " + lv.Disease).groupby("Drug_ID").t.agg(join)).fillna("")
    S = S.sort_values(["Indirect routes to NAFLD", "Drug"], ascending=[False, True]).reset_index(drop=True)
    S.insert(0, "No.", S.index + 1)
    with pd.ExcelWriter(RUNS_DIR / f"{run}_BB_direct_diseases.xlsx") as xw:
        S[["No.", "Drug", "Drug_ID", "Indirect routes to NAFLD", "Treats (n)", "Off-label (n)", "Contraindicated (n)",
           "Treats", "Off-label for", "Contraindicated in", "Liver-related direct links", "B routes"]].to_excel(
            xw, sheet_name="Summary", index=False)
        links.sort_values(["Drug", "Link", "Disease"])[["Drug", "Link", "Disease", "disease_id"]].to_excel(
            xw, sheet_name="Direct links", index=False)
        lv.sort_values(["Drug", "Link", "Disease"])[["Drug", "Link", "Disease", "disease_id"]].to_excel(
            xw, sheet_name="Liver links", index=False)

    treats_liver = lv[lv.rel == "TREATS"].groupby("Drug_ID").Disease.agg(join)
    ci_liver = lv[lv.rel == "CONTRAINDICATED_IN"].groupby("Drug_ID").Disease.agg(join)
    T = bb[bb.Drug_ID.isin(treats_liver.index)].copy()
    T["Liver diseases it treats"] = T.Drug_ID.map(treats_liver)
    T["Liver contraindications"] = T.Drug_ID.map(ci_liver)
    final = T[T["Liver contraindications"].isna()].sort_values(["BB routes", "Drug"], ascending=[False, True])
    final.insert(0, "Rank", final["BB routes"].rank(method="min", ascending=False).astype(int))
    final = final.rename(columns={"BB routes": "BB routes to NAFLD"})[["Rank", "Drug", "Drug_ID", "BB routes to NAFLD",
                                                                         "B routes", "Liver diseases it treats"]]
    removed = T[T["Liver contraindications"].notna()].sort_values("BB routes", ascending=False).rename(
        columns={"BB routes": "BB routes to NAFLD"})[["Drug", "Drug_ID", "BB routes to NAFLD", "Liver diseases it treats",
                                                       "Liver contraindications"]]
    final.to_csv(RUNS_DIR / f"{run}_BB_liver_treating_drugs_final.csv", index=False)
    with pd.ExcelWriter(RUNS_DIR / f"{run}_BB_liver_treating_drugs_final.xlsx") as xw:
        final.to_excel(xw, sheet_name="Final drugs", index=False)
        removed.to_excel(xw, sheet_name="Removed drugs", index=False)

    stage_tables(final, routes, RUNS_DIR / f"{run}_BB_top_drugs_stages.xlsx", "Liver diseases it treats")

    # secondary list: all BB drugs, minus liver-contraindicated ones
    A = bb[~bb.Drug_ID.isin(ci_liver.index)].copy()
    A["Liver diseases it treats"] = A.Drug_ID.map(treats_liver)
    A["Treats a liver disease"] = A["Liver diseases it treats"].notna()
    A["Current indications (TREATS)"] = A.Drug_ID.map(links[links.rel == "TREATS"].groupby("Drug_ID").Disease.agg(join))
    A = A.sort_values(["BB routes", "Drug"], ascending=[False, True])
    A.insert(0, "Rank", A["BB routes"].rank(method="min", ascending=False).astype(int))
    A = A.rename(columns={"BB routes": "BB routes to NAFLD"})[["Rank", "Drug", "Drug_ID", "BB routes to NAFLD", "B routes",
                                                                 "Treats a liver disease", "Liver diseases it treats",
                                                                 "Current indications (TREATS)"]]
    A.to_csv(RUNS_DIR / f"{run}_BB_all_drugs_ranked.csv", index=False)
    with pd.ExcelWriter(RUNS_DIR / f"{run}_BB_all_drugs_ranked.xlsx") as xw:
        A.to_excel(xw, sheet_name="All BB drugs ranked", index=False)
        removed.to_excel(xw, sheet_name="Removed (liver CI)", index=False)
    stage_tables(A, routes, RUNS_DIR / f"{run}_BB_all_drugs_top_stages.xlsx", "Liver diseases it treats")
    info = {"run": run, "drugs_with_B_routes": b_drugs, "drugs_with_BB_routes": len(bb),
            "drugs_treating_a_liver_disease": len(T), "removed_liver_contraindicated": len(removed),
            "final_ranked_drugs": len(final), "stage_table_drugs_rank_le_25": int((final.Rank <= TOP_RANK).sum()),
            "secondary_removed_liver_contraindicated": int(bb.Drug_ID.isin(ci_liver.index).sum()),
            "secondary_ranked_drugs": len(A), "secondary_rank_le_25": int((A.Rank <= TOP_RANK).sum())}
    (RUNS_DIR / f"{run}_BB_followup.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info, final, A


def stage_tables(final, routes, path, liver_col):
    top = final[final.Rank <= TOP_RANK]
    r = routes[routes.drug_id.isin(top.Drug_ID)].copy()
    st = r.groupby(["drug_id", "stage"]).size().unstack(fill_value=0).reindex(columns=STAGES, fill_value=0)
    D = top[["Rank", "Drug", "Drug_ID", "BB routes to NAFLD"]].rename(columns={"BB routes to NAFLD": "BB routes"}).set_index("Drug_ID")
    D["Gene* (n)"] = r.groupby("drug_id").gene_star_id.nunique()
    for s_ in STAGES:
        D[f"{s_} routes"] = st[s_]
    D["Main stage (most routes)"] = st.idxmax(axis=1)
    D["% routes in main stage"] = (100 * st.max(axis=1) / st.sum(axis=1)).round(1)
    D["All stages reached"] = st.apply(lambda row: ", ".join(c for c in STAGES if row[c] > 0), axis=1)
    D["Liver disease it treats"] = top.set_index("Drug_ID")[liver_col]
    D = D.reset_index()[["Rank", "Drug", "Drug_ID", "BB routes", "Gene* (n)"] + [f"{s_} routes" for s_ in STAGES]
                        + ["Main stage (most routes)", "% routes in main stage", "All stages reached", "Liver disease it treats"]]
    gs = r.groupby(["drug_id", "drug", "gene_star", "stage", "gene_star_direction"]).size().rename("BB routes").reset_index()
    gs = gs.rename(columns={"drug": "Drug", "gene_star": "Gene*", "stage": "Gene* stage", "gene_star_direction": "Direction"})
    gs["_rank"] = gs.drug_id.map(top.set_index("Drug_ID").Rank)
    gs = gs.sort_values(["_rank", "Drug", "BB routes"], ascending=[True, True, False]).drop(columns=["_rank", "drug_id"])
    tot = pd.DataFrame({"Stage": STAGES, "Drugs reaching it": [int((st[s_] > 0).sum()) for s_ in STAGES],
                        "Routes": [int(st[s_].sum()) for s_ in STAGES],
                        "Main stage for (n drugs)": [int((D["Main stage (most routes)"] == s_).sum()) for s_ in STAGES]})
    with pd.ExcelWriter(path) as xw:
        D.to_excel(xw, sheet_name="Drug stages", index=False)
        gs.to_excel(xw, sheet_name="Drug - Gene star detail", index=False)
        tot.to_excel(xw, sheet_name="Stage totals", index=False)


def main():
    liver = pd.read_csv(LIVER_SET)
    liver_ids = set(liver.loc[~liver.excluded_non_hepatic, "disease_id"])
    drv = driver()
    infos, finals, alls = [], {}, {}
    with read_session(drv) as ses:
        for key, run in RUNS.items():
            if not (RUNS_DIR / f"{run}_BB.xlsx").exists():
                print(f"{run}: no BB output, skipped")
                continue
            info, final, alld = follow_up(ses, run, liver_ids)
            infos.append(info)
            finals[key] = final
            alls[key] = alld
            print(json.dumps(info))
    drv.close()
    runs_tab = pd.DataFrame(infos)
    runs_tab.to_csv(RUNS_DIR / "ranking_run_table.csv", index=False)

    md = compare(finals, "top25_comparison", "Top 25 liver-treating drugs across runs (main lists)")
    md2 = compare(alls, "top25_comparison_all_drugs",
                  "Top 25 of ALL BB drugs (not restricted to a current liver use; liver-contraindicated drugs removed) across runs")
    print(runs_tab.to_string(index=False))
    print(md)
    print(md2)


def compare(finals, stem, title):
    top = {k: f[f.Rank <= TOP_RANK].set_index("Drug_ID").Rank for k, f in finals.items()}
    liver_tx = {d: t for f in finals.values() for d, t in zip(f.Drug_ID, f["Liver diseases it treats"])}
    names = {d: n for f in finals.values() for d, n in zip(f.Drug_ID, f.Drug)}
    t = pd.DataFrame(top)
    t["in_all_runs"] = t[list(top)].notna().all(axis=1)
    t["in_n_runs"] = t[list(top)].notna().sum(axis=1)
    t["liver_diseases_it_treats"] = t.index.map(liver_tx)
    t = t.sort_values(["in_n_runs"] + list(top), ascending=[False] + [True] * len(top))
    t.index.name = "Drug_ID"
    t.insert(0, "Drug", t.index.map(names))
    t.to_csv(RUNS_DIR / f"{stem}.csv")
    sets = {k: set(v.index) for k, v in top.items()}
    keys = list(sets)
    fmt = lambda x: "" if pd.isna(x) else str(int(x))  # noqa: E731
    over = [("All runs", len(set.intersection(*sets.values())))] + [
        (f"{a} & {b}", len(sets[a] & sets[b])) for i, a in enumerate(keys) for b in keys[i + 1:]]
    md = f"""# {title}

Top 25 = rank <= 25 by BB routes to NAFLD (ties included): {", ".join(f"{k} {len(v)}" for k, v in sets.items())} drugs.
Generated {now()}.

| Overlap | Drugs |
|---|---|
""" + "\n".join(f"| {a} | {n} |" for a, n in over) + f"""

| Drug | Drug_ID | {" | ".join("Rank " + k for k in keys)} | In all runs | Liver diseases it treats |
|---|---|{"---|" * len(keys)}---|---|
""" + "\n".join(f"| {r.Drug} | {d} | {' | '.join(fmt(r[k]) for k in keys)} | {'yes' if r.in_all_runs else ''} | {r.liver_diseases_it_treats} |"
                for d, r in t.iterrows()) + "\n"
    (RUNS_DIR / f"{stem}.md").write_text(md, encoding="utf-8")
    return md


if __name__ == "__main__":
    main()
