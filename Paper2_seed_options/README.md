# Public seed genes for the metapath drug-repurposing analysis

These files replace the old seed gene list (the `gene_star` column in the metapath runs).
Every gene here comes from public, citable sources, so no other in-house data is needed.

## What to use

**Main file: `seed_genes_main_Ryaboshapkina2017.csv` (280 genes)**

Source: Ryaboshapkina M, Hammar M. *Human hepatic gene expression signature of
non-alcoholic fatty liver disease progression, a meta-analysis.* Sci Rep 2017;7:12361.
doi:10.1038/s41598-017-10930-w (open access). Taken from Supplementary Table S2.

- 218 genes whose liver expression tracks NAFLD histology, each replicated with the
  same direction in at least 3 independent public studies.
- 62 genes with genetic association to NAFLD, compiled by the same authors
  (52 of them have no histology signal and are labelled `0_genetic_risk`).

| Column | Meaning |
|---|---|
| `gene` | Current HGNC symbol (6 old 2016 names were updated, e.g. PAPD7 → TENT4A) |
| `ensembl_id` | OptimusKG gene ID |
| `main_stage` | Earliest disease stage the gene is linked to (see below) |
| `all_stages` | Every stage the gene is linked to |
| `evidence` | Which histology traits the paper reported for the gene |
| `direction` | `increasing` / `decreasing` as disease gets worse; `mixed` if stages disagree |
| `n_gene_partners`, `n_pathways`, `n_drugs_targeting` | Connections in OptimusKG |
| `usable_for_metapath` | True if the gene has ≥1 gene partner and ≥1 pathway in OptimusKG |
| `also_in_GWAS_Catalog` | Gene also appears in current GWAS Catalog liver hits |

**Disease stages (replace the old F0→F1 … F3→F4 stage column)**

| Stage | From paper trait | Genes (main stage) | Up / down |
|---|---|---|---|
| `0_genetic_risk` | genetic association | 52 | n/a |
| `1_steatosis` | degree of steatosis | 13 | 10 / 3 |
| `2_NASH` | NASH vs simple steatosis, inflammation, NAS | 83 | 56 / 27 |
| `3_fibrosis` | fibrosis progression | 122 | 93 / 29 |
| `4_HCC` | progression to HCC | 10 | 1 / 9 |

All 280 genes are found in OptimusKG; 211 have both gene partners and pathways.

**Optional add-on: `seed_genes_optional_GWAS_Catalog.csv` (310 genes)**

Genome-wide significant (p ≤ 5×10⁻⁸) genes for fatty liver disease, MASLD, MASH,
NAFLD severity, cirrhosis and liver fibrosis from the GWAS Catalog (downloaded
2026-11-11). Pseudogenes, antisense and lncRNA names removed. Adds newer risk genes
not in the 2017 paper (e.g. PNPLA3, TM6SF2, HSD17B13, MTARC1, GCKR). These have
no stage or direction, so use them as stage `0_genetic_risk` if added.

`seed_genes_main_long_format.csv` has one row per gene × trait, if a per-stage
breakdown is needed.

## How to rerun

1. Use `seed_genes_main_Ryaboshapkina2017.csv` as the seed (`gene_star`) list.
   Optionally keep only `usable_for_metapath == True`.
2. Use `main_stage` in place of the old stage column and `direction` in place of
   `gene_star_direction`.
3. Keep everything else the same: OptimusKG graph, added drug/pathway data,
   metapath drug → gene → gene → seed gene → pathway → NAFLD, route counting,
   liver-treating filter, contraindication removal.
4. Start from a clean run; do not reuse old route files or rankings.

## Suggested methods wording

> Seed genes were obtained from a published meta-analysis of human liver
> transcriptomes across the NAFLD spectrum (Ryaboshapkina & Hammar, 2017;
> Supplementary Table S2), comprising genes with replicated, same-direction
> association with steatosis, steatohepatitis, fibrosis or progression to HCC,
> together with genes with reported genetic association to NAFLD. Genes were
> mapped to OptimusKG by HGNC symbol.
> [Optional:] Genome-wide significant loci for NAFLD/MASLD, MASH, cirrhosis and
> liver fibrosis (p ≤ 5×10⁻⁸) were added from the GWAS Catalog.

## Folder contents

- `source/Ryaboshapkina2017_SciRep_SupplementaryTables.xls`: original supplement (CC BY 4.0)
- `source/gwas_catalog_liver_hits_2026-11-11.csv`: raw GWAS Catalog download
- `scripts/fetch_gwas_catalog.py`: re-download GWAS hits
- `scripts/build_seeds.py`: builds the seed files from the two sources and OptimusKG

Rebuild:

```
python scripts/fetch_gwas_catalog.py source/gwas_catalog_liver_hits_2026-11-11.csv
python scripts/build_seeds.py source/Ryaboshapkina2017_SciRep_SupplementaryTables.xls source/gwas_catalog_liver_hits_2026-11-11.csv <path-to-optimuskg-parquets> .
```
