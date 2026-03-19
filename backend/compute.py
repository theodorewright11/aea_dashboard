"""
compute.py — Core compute engine for the AEA Dashboard.
All @st.cache_data decorators replaced with simple in-process dict caches.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

from config import (
    ECO_BASELINE_FILE, ECO_2015_FILE, CROSSWALK_PATHS,
    AGG_LEVEL_COL, DATASETS, DATASET_SERIES, SORT_COL_MAP,
)

AEI_EXPLORER_DATASETS = ["AEI v1", "AEI v2", "AEI v3", "AEI v4", "AEI API v3", "AEI API v4"]

# ── Simple in-process caches ───────────────────────────────────────────────────
_crosswalk_cache: Optional[pd.DataFrame] = None
_eco_raw_cache:   Optional[pd.DataFrame] = None
_eco2015_raw_cache: Optional[pd.DataFrame] = None
_eco_baseline_cache: dict = {}
_dataset_cache:      dict = {}
_explorer_occ_cache: Optional[list] = None
_explorer_task_cache: dict = {}
_wa_cache: dict = {}
_trends_cache: dict = {}
_explorer_task_lookup_cache: Optional[dict] = None
_explorer_groups_cache: Optional[dict] = None
_wa_explorer_cache: Optional[list] = None
_all_tasks_cache: Optional[list] = None


def _find_crosswalk() -> Optional[Path]:
    for p in CROSSWALK_PATHS:
        if Path(p).exists():
            return Path(p)
    return None


def crosswalk_available() -> bool:
    return _find_crosswalk() is not None


def load_crosswalk() -> Optional[pd.DataFrame]:
    global _crosswalk_cache
    if _crosswalk_cache is None:
        path = _find_crosswalk()
        if path is None:
            return None
        _crosswalk_cache = pd.read_csv(path)
    return _crosswalk_cache


def load_eco_raw() -> Optional[pd.DataFrame]:
    global _eco_raw_cache
    if _eco_raw_cache is None:
        if not Path(ECO_BASELINE_FILE).exists():
            return None
        _eco_raw_cache = pd.read_csv(ECO_BASELINE_FILE)
    return _eco_raw_cache


def load_eco2015_raw() -> Optional[pd.DataFrame]:
    global _eco2015_raw_cache
    if _eco2015_raw_cache is None:
        if not Path(ECO_2015_FILE).exists():
            return None
        _eco2015_raw_cache = pd.read_csv(ECO_2015_FILE)
    return _eco2015_raw_cache


def dataset_exists(name: str) -> bool:
    meta = DATASETS.get(name)
    if meta is None:
        return False
    return Path(meta["file"]).exists()


def eco2015_available() -> bool:
    return Path(ECO_2015_FILE).exists()


# ── Task-level transformations ─────────────────────────────────────────────────

def apply_physical_filter(df: pd.DataFrame, physical_mode: str) -> pd.DataFrame:
    if "physical" not in df.columns or physical_mode == "all":
        return df
    if physical_mode == "exclude":
        return df[df["physical"] != True].copy()
    if physical_mode == "only":
        return df[df["physical"] == True].copy()
    return df


def compute_task_comp(
    df: pd.DataFrame,
    method: str,
    use_auto_aug: bool,
    use_adj_mean: bool,
) -> pd.Series:
    if method == "freq":
        tc = df["freq_mean"].copy().fillna(0.0)
    else:
        tc = df["relevance"].fillna(0.0) * (2.0 ** df["importance"].fillna(0.0))

    if use_auto_aug:
        if use_adj_mean and "auto_aug_mean_adj" in df.columns:
            aug = df["auto_aug_mean_adj"].fillna(0.0)
        elif "auto_aug_mean" in df.columns:
            aug = df["auto_aug_mean"].fillna(0.0)
        else:
            aug = pd.Series(1.0, index=df.index)
        tc = tc * (aug / 5.0)

    return tc


def dedup_and_compute(
    df: pd.DataFrame,
    title_col: str,
    emp_col: str,
    wage_col: str,
    method: str,
    use_auto_aug: bool,
    use_adj_mean: bool,
) -> pd.DataFrame:
    keep = [
        emp_col, wage_col,
        "broad_occ", "minor_occ_category", "major_occ_category",
        "freq_mean", "importance", "relevance", "auto_aug_mean",
    ]
    if "auto_aug_mean_adj" in df.columns:
        keep.append("auto_aug_mean_adj")

    agg_dict = {c: "first" for c in keep if c in df.columns}
    deduped = (
        df.groupby([title_col, "task_normalized"], sort=False)
        .agg(agg_dict)
        .reset_index()
    )
    deduped["task_comp"] = compute_task_comp(deduped, method, use_auto_aug, use_adj_mean)
    return deduped


# ── ECO Baseline ───────────────────────────────────────────────────────────────

def load_eco_baseline(method: str, physical_mode: str, geo: str) -> Optional[pd.DataFrame]:
    key = (method, physical_mode, geo)
    if key in _eco_baseline_cache:
        return _eco_baseline_cache[key]

    eco = load_eco_raw()
    if eco is None:
        return None
    eco = apply_physical_filter(eco, physical_mode)
    if eco.empty:
        return None

    emp_col  = f"emp_tot_{geo}_2024"
    wage_col = f"a_med_{geo}_2024"
    result = dedup_and_compute(eco, "title_current", emp_col, wage_col, method, False, False)
    _eco_baseline_cache[key] = result
    return result


# ── Aggregation ────────────────────────────────────────────────────────────────

def aggregate_results(
    ai_df:     pd.DataFrame,
    eco_df:    pd.DataFrame,
    title_col: str,
    agg_level: str,
    emp_col:   str,
    wage_col:  str,
) -> pd.DataFrame:
    group_col = AGG_LEVEL_COL[agg_level]

    ai_by_occ = (
        ai_df.groupby(title_col)["task_comp"]
        .sum()
        .reset_index()
        .rename(columns={"task_comp": "ai_task_comp"})
    )

    eco_agg: dict = {"eco_task_comp": ("task_comp", "sum")}
    for c in [emp_col, wage_col, "broad_occ", "minor_occ_category", "major_occ_category"]:
        if c in eco_df.columns:
            eco_agg[c] = (c, "first")

    eco_by_occ = eco_df.groupby("title_current").agg(**eco_agg).reset_index()

    occ = eco_by_occ.merge(
        ai_by_occ, left_on="title_current", right_on=title_col, how="left"
    )
    if title_col != "title_current" and title_col in occ.columns:
        occ.drop(columns=[title_col], inplace=True)

    occ["ai_task_comp"] = occ["ai_task_comp"].fillna(0.0)
    occ["pct_tasks_affected"] = (
        (occ["ai_task_comp"] / occ["eco_task_comp"].replace(0, np.nan)) * 100
    ).fillna(0.0).clip(upper=100.0)

    if emp_col in occ.columns:
        occ["workers_affected"] = occ["pct_tasks_affected"] / 100.0 * occ[emp_col]
        if wage_col in occ.columns:
            occ["wages_affected"] = (
                occ["pct_tasks_affected"] / 100.0 * occ[emp_col] * occ[wage_col]
            )
        else:
            occ["wages_affected"] = np.nan
    else:
        occ["workers_affected"] = np.nan
        occ["wages_affected"]   = np.nan

    if agg_level == "occupation":
        return occ[["title_current", "pct_tasks_affected",
                    "workers_affected", "wages_affected"]].copy()

    ai_by_group = (
        ai_df.groupby(group_col)["task_comp"]
        .sum().reset_index()
        .rename(columns={"task_comp": "ai_task_comp_group"})
    )
    eco_by_group = (
        eco_df.groupby(group_col)["task_comp"]
        .sum().reset_index()
        .rename(columns={"task_comp": "eco_task_comp_group"})
    )

    grp = eco_by_group.merge(ai_by_group, on=group_col, how="left")
    grp["ai_task_comp_group"] = grp["ai_task_comp_group"].fillna(0.0)
    grp["pct_tasks_affected"] = (
        (grp["ai_task_comp_group"] / grp["eco_task_comp_group"].replace(0, np.nan)) * 100
    ).fillna(0.0).clip(upper=100.0)

    if group_col in occ.columns:
        occ_by_group = (
            occ.groupby(group_col)
            .agg(workers_affected=("workers_affected", "sum"),
                 wages_affected=("wages_affected", "sum"))
            .reset_index()
        )
        grp = grp.merge(occ_by_group, on=group_col, how="left")
    else:
        grp["workers_affected"] = np.nan
        grp["wages_affected"]   = np.nan

    return grp[[group_col, "pct_tasks_affected", "workers_affected", "wages_affected"]].copy()


# ── Single-dataset compute ─────────────────────────────────────────────────────

def compute_single_dataset(
    file_path:     str,
    is_aei:        bool,
    method:        str,
    use_auto_aug:  bool,
    use_adj_mean:  bool,
    physical_mode: str,
    geo:           str,
    agg_level:     str,
) -> Optional[pd.DataFrame]:
    key = (file_path, is_aei, method, use_auto_aug, use_adj_mean, physical_mode, geo, agg_level)
    if key in _dataset_cache:
        return _dataset_cache[key]

    if not Path(file_path).exists():
        return None

    eco_deduped = load_eco_baseline(method, physical_mode, geo)
    if eco_deduped is None or eco_deduped.empty:
        return None

    df = pd.read_csv(file_path)
    df = apply_physical_filter(df, physical_mode)
    if df.empty:
        return None

    emp_col  = f"emp_tot_{geo}_2024"
    wage_col = f"a_med_{geo}_2024"

    if is_aei:
        crosswalk = load_crosswalk()
        if crosswalk is None:
            return None

        ai_deduped = dedup_and_compute(
            df, "title", emp_col, wage_col, method, use_auto_aug, use_adj_mean
        )

        soc_lookup = df[["title", "soc_code_2010"]].drop_duplicates("title")
        ai_deduped = ai_deduped.merge(soc_lookup, on="title", how="left")

        ai_deduped = ai_deduped.merge(
            crosswalk[["O*NET-SOC 2010 Code", "O*NET-SOC 2019 Title"]],
            left_on="soc_code_2010", right_on="O*NET-SOC 2010 Code",
            how="left",
        )

        split_counts = (
            crosswalk.groupby("O*NET-SOC 2010 Code")["O*NET-SOC 2019 Title"]
            .nunique()
            .reset_index(name="split_count")
        )
        ai_deduped = ai_deduped.merge(
            split_counts,
            left_on="soc_code_2010", right_on="O*NET-SOC 2010 Code",
            how="left", suffixes=("", "_sc"),
        )
        ai_deduped.drop(
            columns=[c for c in ai_deduped.columns if c.endswith("_sc")],
            inplace=True,
        )
        ai_deduped["split_count"] = ai_deduped["split_count"].fillna(1.0)
        ai_deduped["task_comp"] /= ai_deduped["split_count"]
        if emp_col in ai_deduped.columns:
            ai_deduped[emp_col] /= ai_deduped["split_count"]

        agg_cols: dict = {"task_comp": "sum"}
        if emp_col in ai_deduped.columns:
            agg_cols[emp_col] = "sum"
        for c in ["broad_occ", "minor_occ_category", "major_occ_category", wage_col]:
            if c in ai_deduped.columns:
                agg_cols[c] = "first"

        ai_final = (
            ai_deduped
            .groupby(["O*NET-SOC 2019 Title", "task_normalized"], sort=False)
            .agg(agg_cols)
            .reset_index()
            .rename(columns={"O*NET-SOC 2019 Title": "title_current"})
        )

        eco_raw = load_eco_raw()
        if eco_raw is not None and "task_prop" in eco_raw.columns:
            tp = eco_raw[["title_current", "task_prop"]].drop_duplicates("title_current")
            ai_final = ai_final.merge(tp, on="title_current", how="left")
            ai_final["task_prop"] = ai_final["task_prop"].fillna(1.0).clip(lower=1.0)
            ai_final["task_comp"] /= ai_final["task_prop"]
            ai_final.drop(columns=["task_prop"], inplace=True)

        if eco_raw is not None:
            eco_groups = eco_raw[
                ["title_current", "broad_occ", "minor_occ_category", "major_occ_category"]
            ].drop_duplicates("title_current")
            for gc in ["broad_occ", "minor_occ_category", "major_occ_category"]:
                if gc in ai_final.columns:
                    mask = ai_final[gc].isna()
                    if mask.any():
                        fill = ai_final.loc[mask, ["title_current"]].merge(
                            eco_groups[["title_current", gc]],
                            on="title_current", how="left",
                        )
                        ai_final.loc[mask, gc] = fill[gc].values

        title_col_for_agg = "title_current"

    else:
        ai_final = dedup_and_compute(
            df, "title_current", emp_col, wage_col, method, use_auto_aug, use_adj_mean
        )
        title_col_for_agg = "title_current"

    result = aggregate_results(
        ai_final, eco_deduped, title_col_for_agg, agg_level, emp_col, wage_col
    )
    _dataset_cache[key] = result
    return result


# ── Multi-dataset combination ──────────────────────────────────────────────────

def combine_results(
    results:        list[Optional[pd.DataFrame]],
    group_col:      str,
    combine_method: str,
) -> pd.DataFrame:
    valid = [r for r in results if r is not None and not r.empty]
    if not valid:
        return pd.DataFrame()
    if len(valid) == 1:
        return valid[0].copy()

    metric_cols = ["pct_tasks_affected", "workers_affected", "wages_affected"]

    renamed = []
    for i, r in enumerate(valid):
        sub = r[[group_col] + metric_cols].copy()
        sub = sub.rename(columns={mc: f"{mc}_{i}" for mc in metric_cols})
        renamed.append(sub)

    combined = renamed[0]
    for sub in renamed[1:]:
        combined = combined.merge(sub, on=group_col, how="outer")

    for mc in metric_cols:
        cols = [f"{mc}_{i}" for i in range(len(valid))]
        if combine_method == "Max":
            combined[mc] = combined[cols].max(axis=1)
        else:
            combined[mc] = combined[cols].mean(axis=1)

    return combined[[group_col] + metric_cols].copy()


# ── Group data (occupation-level overview) ─────────────────────────────────────

def get_group_data(settings: dict) -> Optional[dict]:
    """
    Returns a dict with:
      - df:               DataFrame of rows (descending order, top_n or search window)
      - group_col:        column name for the category
      - total_categories: total number of categories before top_n/search filter
      - total_emp:        sum of workers_affected across ALL categories
      - total_wages:      sum of wages_affected across ALL categories
      - matched_category: str or None (set when search_query was used)
    """
    selected = settings.get("selected_datasets", [])
    if not selected:
        return None

    method        = settings["method"]
    use_auto_aug  = settings["use_auto_aug"]
    use_adj_mean  = settings["use_adj_mean"]
    physical_mode = settings["physical_mode"]
    geo           = settings["geo"]
    agg_level     = settings["agg_level"]
    sort_by       = settings["sort_by"]
    top_n         = int(settings["top_n"])
    combine       = settings.get("combine_method", "Average")
    search_query  = (settings.get("search_query") or "").strip()
    context_size  = int(settings.get("context_size") or 5)

    results = []
    for name in selected:
        meta = DATASETS.get(name)
        if meta is None:
            continue
        effective_adj_mean = use_adj_mean and meta["is_mcp"]
        r = compute_single_dataset(
            file_path     = meta["file"],
            is_aei        = meta["is_aei"],
            method        = method,
            use_auto_aug  = use_auto_aug,
            use_adj_mean  = effective_adj_mean,
            physical_mode = physical_mode,
            geo           = geo,
            agg_level     = agg_level,
        )
        results.append(r)

    group_col = AGG_LEVEL_COL[agg_level]
    df = combine_results(results, group_col, combine)
    if df is None or df.empty:
        return None

    sort_col = SORT_COL_MAP.get(sort_by, "workers_affected")
    if sort_col not in df.columns:
        for c in ["workers_affected", "wages_affected", "pct_tasks_affected"]:
            if c in df.columns:
                sort_col = c
                break
        else:
            sort_col = group_col

    # Sort descending — highest value first (appears at TOP of horizontal bar chart)
    df = df.sort_values(sort_col, ascending=False, na_position="last").reset_index(drop=True)

    # Compute ranks across ALL categories (rank 1 = highest value)
    for metric_col, rank_col in [
        ("workers_affected",   "rank_workers"),
        ("wages_affected",     "rank_wages"),
        ("pct_tasks_affected", "rank_pct"),
    ]:
        if metric_col in df.columns:
            df[rank_col] = df[metric_col].rank(ascending=False, method="min").astype(int)
        else:
            df[rank_col] = 0

    total_categories = len(df)
    total_emp   = float(df["workers_affected"].sum()) if "workers_affected" in df.columns else 0.0
    total_wages = float(df["wages_affected"].sum())   if "wages_affected"   in df.columns else 0.0

    # Apply search filter or top_n
    matched_category: Optional[str] = None
    if search_query:
        q = search_query.lower()
        mask = df[group_col].str.lower().str.contains(q, na=False, regex=False)
        if mask.any():
            pos = int(mask.idxmax())
            matched_category = str(df.loc[pos, group_col])
            start = max(0, pos - context_size)
            end   = min(len(df), pos + context_size + 1)
            df = df.iloc[start:end].copy()
        else:
            df = df.iloc[0:0].copy()  # empty — no match
    else:
        df = df.head(top_n).copy()

    return {
        "df":               df,
        "group_col":        group_col,
        "total_categories": total_categories,
        "total_emp":        total_emp,
        "total_wages":      total_wages,
        "matched_category": matched_category,
    }


# ── Work Activities (DWA / IWA / GWA) ─────────────────────────────────────────

def _combine_activity_dfs(
    frames: list[pd.DataFrame],
    cat_col: str,
    combine_method: str,
) -> pd.DataFrame:
    """Combine multiple activity-level DataFrames via average or max."""
    if not frames:
        return pd.DataFrame()
    if len(frames) == 1:
        return frames[0].copy()

    metric_cols = ["pct_tasks_affected", "workers_affected", "wages_affected"]
    renamed = []
    for i, f in enumerate(frames):
        sub = f[[cat_col] + [c for c in metric_cols if c in f.columns]].copy()
        sub = sub.rename(columns={mc: f"{mc}_{i}" for mc in metric_cols if mc in f.columns})
        renamed.append(sub)

    combined = renamed[0]
    for sub in renamed[1:]:
        combined = combined.merge(sub, on=cat_col, how="outer")

    for mc in metric_cols:
        cols = [f"{mc}_{i}" for i in range(len(frames)) if f"{mc}_{i}" in combined.columns]
        if not cols:
            continue
        if combine_method == "Max":
            combined[mc] = combined[cols].max(axis=1)
        else:
            combined[mc] = combined[cols].mean(axis=1)

    keep = [cat_col] + [mc for mc in metric_cols if mc in combined.columns]
    return combined[keep].copy()


def _compute_wa_for_group(
    dataset_names: list[str],
    settings: dict,
    use_eco2015: bool,
) -> Optional[dict]:
    """
    Compute DWA/IWA/GWA metrics for a group of datasets sharing the same SOC taxonomy.
    Returns dict with keys "gwa", "iwa", "dwa" → list of activity row dicts.

    Dedup strategy:
    - n_tasks_per_occ uses (title, task_normalized) dedup — for emp_per_task allocation
    - Each activity level uses (title, task_normalized, act_col) dedup — preserves all
      DWA/IWA/GWA associations a task may have (a task can map to multiple DWAs)
    """
    method        = settings["method"]
    use_auto_aug  = settings["use_auto_aug"]
    use_adj_mean  = settings.get("use_adj_mean", False)
    physical_mode = settings["physical_mode"]
    geo           = settings["geo"]
    combine       = settings.get("combine_method", "Average")
    top_n         = int(settings.get("top_n", 20))
    sort_by       = settings.get("sort_by", "workers_affected")

    emp_col  = f"emp_tot_{geo}_2024"
    wage_col = f"a_med_{geo}_2024"

    # -- Load ECO baseline
    eco_raw = load_eco2015_raw() if use_eco2015 else load_eco_raw()
    if eco_raw is None:
        return None

    eco = apply_physical_filter(eco_raw, physical_mode)
    if eco.empty:
        return None

    title_col = "title" if use_eco2015 else "title_current"

    activity_cols = {
        "gwa": "gwa_title",
        "iwa": "iwa_title",
        "dwa": "dwa_title",
    }

    # -- n_tasks per occ: (title, task_normalized) dedup only — for emp allocation
    eco_task_dedup = (
        eco.groupby([title_col, "task_normalized"], sort=False)
        .first()
        .reset_index()
    )
    n_tasks_per_occ = (
        eco_task_dedup.groupby(title_col)["task_normalized"]
        .count()
        .reset_index(name="n_tasks")
    )

    # Employment / wage per occupation (from raw, first occurrence)
    occ_emp_wage = (
        eco.groupby(title_col)[[emp_col, wage_col]]
        .first()
        .reset_index()
    )

    # -- Pre-compute eco_for_act per activity level
    # Each uses (title, task_normalized, act_col) dedup to preserve all DWA/IWA/GWA associations
    eco_for_acts: dict[str, pd.DataFrame] = {}
    for act_key, act_col in activity_cols.items():
        if act_col not in eco.columns:
            continue
        eco_for_act = (
            eco.groupby([title_col, "task_normalized", act_col], sort=False)
            .first()
            .reset_index()
        )
        eco_for_act["eco_tc"] = compute_task_comp(eco_for_act, method, False, False)
        eco_for_act = eco_for_act.merge(n_tasks_per_occ, on=title_col, how="left")
        eco_for_act = eco_for_act.merge(occ_emp_wage, on=title_col, how="left", suffixes=("", "_ow"))
        for col in [emp_col, wage_col]:
            ow = f"{col}_ow"
            if ow in eco_for_act.columns:
                eco_for_act[col] = eco_for_act[ow].fillna(eco_for_act[col])
                eco_for_act.drop(columns=[ow], inplace=True)
        eco_for_act["emp_per_task"] = (eco_for_act[emp_col] / eco_for_act["n_tasks"]).fillna(0.0)
        eco_for_acts[act_key] = eco_for_act

    # -- Process each AI dataset
    per_dataset: dict[str, list] = {}

    for name in dataset_names:
        meta = DATASETS.get(name)
        if meta is None or not Path(meta["file"]).exists():
            continue

        ai_raw = pd.read_csv(meta["file"])
        ai_raw = apply_physical_filter(ai_raw, physical_mode)
        if ai_raw.empty:
            continue

        ai_title_col  = "title" if meta["is_aei"] else "title_current"
        effective_adj = use_adj_mean and meta["is_mcp"]

        for act_key, act_col in activity_cols.items():
            if act_key not in eco_for_acts:
                continue
            if act_col not in ai_raw.columns:
                continue

            eco_for_act = eco_for_acts[act_key]

            # Dedup AI on (ai_title, task_normalized, act_col) to match eco dedup
            ai_for_act = (
                ai_raw.groupby([ai_title_col, "task_normalized", act_col], sort=False)
                .first()
                .reset_index()
            )
            ai_for_act["ai_tc"] = compute_task_comp(ai_for_act, method, use_auto_aug, effective_adj)

            merged = eco_for_act.merge(
                ai_for_act[[ai_title_col, "task_normalized", act_col, "ai_tc"]].rename(
                    columns={ai_title_col: title_col}
                ),
                on=[title_col, "task_normalized", act_col],
                how="left",
            )
            merged["ai_tc"] = merged["ai_tc"].fillna(0.0)

            eco_tc_safe = merged["eco_tc"].replace(0, np.nan)
            merged["workers_contribution"] = (
                (merged["ai_tc"] / eco_tc_safe) * merged["emp_per_task"]
            ).fillna(0.0).clip(lower=0)
            merged["wages_contribution"] = (
                merged["workers_contribution"] * merged[wage_col].fillna(0.0)
            )

            by_act = (
                merged.groupby(act_col)
                .agg(
                    ai_tc_sum=("ai_tc", "sum"),
                    eco_tc_sum=("eco_tc", "sum"),
                    workers_affected=("workers_contribution", "sum"),
                    wages_affected=("wages_contribution", "sum"),
                )
                .reset_index()
                .rename(columns={act_col: "category"})
            )
            by_act["pct_tasks_affected"] = (
                by_act["ai_tc_sum"] / by_act["eco_tc_sum"].replace(0, np.nan) * 100
            ).fillna(0.0).clip(upper=100.0)
            by_act = by_act[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]]

            per_dataset.setdefault(act_key, []).append(by_act)

    if not per_dataset:
        return None

    # -- Combine across datasets and sort descending (highest at top of chart)
    combined: dict = {}
    sort_col_map = {
        "Workers Affected":   "workers_affected",
        "Wages Affected":     "wages_affected",
        "% Tasks Affected":   "pct_tasks_affected",
        "workers_affected":   "workers_affected",
        "wages_affected":     "wages_affected",
        "pct_tasks_affected": "pct_tasks_affected",
    }
    sort_col = sort_col_map.get(sort_by, "workers_affected")

    for act_key, frames in per_dataset.items():
        df = _combine_activity_dfs(frames, "category", combine)
        if df.empty:
            continue
        sc = sort_col if sort_col in df.columns else "pct_tasks_affected"
        # Sort descending — highest at top of chart
        df = (
            df
            .sort_values(sc, ascending=False, na_position="last")
            .head(top_n)
            .reset_index(drop=True)
        )
        combined[act_key] = df.to_dict(orient="records")

    return combined if combined else None


def compute_work_activities(settings: dict) -> dict:
    """
    Splits selected datasets into AEI group (eco_2015 baseline) and
    MCP/Microsoft group (eco_2025 baseline), then computes DWA/IWA/GWA metrics.
    Returns {"aei_group": {...}, "mcp_group": {...}}.
    """
    selected = settings.get("selected_datasets", [])

    aei_datasets    = [d for d in selected if DATASETS.get(d, {}).get("is_aei")]
    mcp_ms_datasets = [d for d in selected if d in DATASETS and not DATASETS[d]["is_aei"]]

    result: dict = {}

    if aei_datasets:
        aei_result = _compute_wa_for_group(aei_datasets, settings, use_eco2015=True)
        if aei_result:
            result["aei_group"] = {"datasets": aei_datasets, **aei_result}

    if mcp_ms_datasets:
        mcp_result = _compute_wa_for_group(mcp_ms_datasets, settings, use_eco2015=False)
        if mcp_result:
            result["mcp_group"] = {"datasets": mcp_ms_datasets, **mcp_result}

    return result


# ── Time Trends ────────────────────────────────────────────────────────────────

def _get_dataset_date(file_path: str) -> str:
    try:
        row = pd.read_csv(file_path, nrows=1)
        if "date" in row.columns:
            return str(row["date"].iloc[0])
    except Exception:
        pass
    return ""


def _safe_num(v) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
        if np.isnan(f) or np.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def compute_trends(settings: dict) -> dict:
    """
    For each requested series (AEI, MCP, etc.), runs compute_single_dataset for
    every version and returns time-series data grouped by date.
    """
    series_names  = settings.get("series", ["AEI", "MCP"])
    method        = settings["method"]
    use_auto_aug  = settings["use_auto_aug"]
    use_adj_mean  = settings.get("use_adj_mean", False)
    physical_mode = settings["physical_mode"]
    geo           = settings["geo"]
    agg_level     = settings["agg_level"]
    top_n         = int(settings.get("top_n", 10))
    sort_by       = settings.get("sort_by", "Workers Affected")

    group_col = AGG_LEVEL_COL[agg_level]
    sort_col  = SORT_COL_MAP.get(sort_by, "workers_affected")

    result_series = []

    for series_name in series_names:
        ds_list = DATASET_SERIES.get(series_name, [])
        series_data = []
        latest_categories: list[str] = []

        for ds_name in ds_list:
            meta = DATASETS.get(ds_name)
            if meta is None or not Path(meta["file"]).exists():
                continue

            effective_adj = use_adj_mean and meta["is_mcp"]
            date = _get_dataset_date(meta["file"])

            df = compute_single_dataset(
                file_path     = meta["file"],
                is_aei        = meta["is_aei"],
                method        = method,
                use_auto_aug  = use_auto_aug,
                use_adj_mean  = effective_adj,
                physical_mode = physical_mode,
                geo           = geo,
                agg_level     = agg_level,
            )

            if df is None or df.empty:
                continue

            sc = sort_col if sort_col in df.columns else group_col
            top_df = (
                df
                .sort_values(sc, ascending=False, na_position="last")
                .head(top_n)
            )
            latest_categories = top_df[group_col].tolist()

            rows = []
            for _, row in df.iterrows():
                rows.append({
                    "category":           str(row[group_col]),
                    "pct_tasks_affected": _safe_num(row.get("pct_tasks_affected", 0)),
                    "workers_affected":   _safe_num(row.get("workers_affected", 0)),
                    "wages_affected":     _safe_num(row.get("wages_affected", 0)),
                })

            series_data.append({
                "dataset": ds_name,
                "date":    date,
                "rows":    rows,
            })

        if series_data:
            result_series.append({
                "name":              series_name,
                "data_points":       series_data,
                "top_categories":    latest_categories,
                "group_col":         group_col,
            })

    return {"series": result_series}


# ── Work Activity Trends ───────────────────────────────────────────────────────

def compute_wa_trends(settings: dict) -> dict:
    """
    Computes work-activity time trends for AEI and MCP/Microsoft series separately.
    For each dataset version, calls _compute_wa_for_group and records the date.
    Returns {"series": [{"name": ..., "data_points": [...], "top_categories": [...]}]}
    where each series is either "AEI" (eco_2015 baseline) or "MCP" (eco_2025 baseline).
    """
    series_names  = settings.get("series", ["AEI", "MCP"])
    method        = settings["method"]
    use_auto_aug  = settings["use_auto_aug"]
    use_adj_mean  = settings.get("use_adj_mean", False)
    physical_mode = settings["physical_mode"]
    geo           = settings["geo"]
    top_n         = int(settings.get("top_n", 10))
    sort_by       = settings.get("sort_by", "Workers Affected")
    activity_level = settings.get("activity_level", "gwa")  # gwa | iwa | dwa

    # Map series name → (dataset family names, use_eco2015)
    SERIES_MAP = {
        "AEI":       (["AEI", "AEI API"], True),
        "MCP":       (["MCP"],            False),
        "Microsoft": (["Microsoft"],      False),
    }

    result_series = []

    for series_name in series_names:
        if series_name not in SERIES_MAP:
            continue
        family_names, use_eco2015 = SERIES_MAP[series_name]

        # Collect all datasets in this series family
        ds_list = []
        for family in family_names:
            ds_list.extend(DATASET_SERIES.get(family, []))

        series_data = []
        latest_categories: list[str] = []

        for ds_name in ds_list:
            meta = DATASETS.get(ds_name)
            if meta is None or not Path(meta["file"]).exists():
                continue

            date = _get_dataset_date(meta["file"])
            effective_adj = use_adj_mean and meta["is_mcp"]

            wa_settings = {
                "method":        method,
                "use_auto_aug":  use_auto_aug,
                "use_adj_mean":  effective_adj,
                "physical_mode": physical_mode,
                "geo":           geo,
                "combine_method": "Average",
                "top_n":         top_n,
                "sort_by":       sort_by,
            }

            wa_result = _compute_wa_for_group([ds_name], wa_settings, use_eco2015)
            if wa_result is None or activity_level not in wa_result:
                continue

            rows_raw = wa_result[activity_level]
            # rows_raw is already sorted descending, top_n already applied
            latest_categories = [r["category"] for r in rows_raw]

            # For time series we want ALL categories, not just top_n
            # Re-run without top_n limit
            wa_settings_all = dict(wa_settings)
            wa_settings_all["top_n"] = 9999
            wa_result_all = _compute_wa_for_group([ds_name], wa_settings_all, use_eco2015)
            rows_all = wa_result_all.get(activity_level, []) if wa_result_all else rows_raw

            series_data.append({
                "dataset": ds_name,
                "date":    date,
                "rows": [
                    {
                        "category":           str(r["category"]),
                        "pct_tasks_affected": _safe_num(r.get("pct_tasks_affected", 0)),
                        "workers_affected":   _safe_num(r.get("workers_affected", 0)),
                        "wages_affected":     _safe_num(r.get("wages_affected", 0)),
                    }
                    for r in rows_all
                ],
            })

        if series_data:
            result_series.append({
                "name":           series_name,
                "data_points":    series_data,
                "top_categories": latest_categories,
                "group_col":      activity_level,
            })

    return {"series": result_series}


# ── Explorer ───────────────────────────────────────────────────────────────────

def _safe_float(v) -> float:
    f = _safe_num(v)
    return 0.0 if f is None else f


def get_explorer_occupations() -> list:
    """
    Returns list of all occupations from eco_2025 with hierarchy, employment,
    wage stats, and AI metrics from all AEI versions, MCP v4, and Microsoft.
    Results are cached.
    """
    global _explorer_occ_cache
    if _explorer_occ_cache is not None:
        return _explorer_occ_cache

    eco = load_eco_raw()
    if eco is None:
        return []

    lookup = _build_explorer_task_lookup()

    # Unique (title, task_norm) pairs with physical flag
    def _phys_bool(v):
        if v is None: return False
        if isinstance(v, float) and np.isnan(v): return False
        return bool(v)

    task_pairs = eco[["title_current", "task_normalized", "physical"]].drop_duplicates(
        subset=["title_current", "task_normalized"]
    ).copy()
    task_pairs["physical_bool"] = task_pairs["physical"].apply(_phys_bool)

    # Build occ → task list and physical count
    occ_task_map: dict = {}
    occ_physical_map: dict = {}
    for _, row in task_pairs.iterrows():
        title = row["title_current"]
        tn = row["task_normalized"]
        if title not in occ_task_map:
            occ_task_map[title] = []
            occ_physical_map[title] = 0
        occ_task_map[title].append(tn)
        if row["physical_bool"]:
            occ_physical_map[title] += 1

    # Basic occ stats
    occ_stats = (
        eco.groupby("title_current")
        .agg(
            major   =("major_occ_category", "first"),
            minor   =("minor_occ_category", "first"),
            broad   =("broad_occ",           "first"),
            emp_nat =("emp_tot_nat_2024",    "first"),
            emp_ut  =("emp_tot_ut_2024",     "first"),
            wage_nat=("a_med_nat_2024",      "first"),
            wage_ut =("a_med_ut_2024",       "first"),
        )
        .reset_index()
    )

    result = []
    for _, row in occ_stats.iterrows():
        title = row["title_current"]
        task_norms = occ_task_map.get(title, [])
        n_tasks = len(task_norms)
        n_phys  = occ_physical_map.get(title, 0)

        metrics = _compute_task_metrics(task_norms, lookup)

        occ_dict: dict = {
            "title_current": title,
            "major":   row.get("major"),
            "minor":   row.get("minor"),
            "broad":   row.get("broad"),
            "emp_nat":  _safe_num(row.get("emp_nat")),
            "emp_ut":   _safe_num(row.get("emp_ut")),
            "wage_nat": _safe_num(row.get("wage_nat")),
            "wage_ut":  _safe_num(row.get("wage_ut")),
            "n_tasks":  n_tasks,
            "n_physical_tasks": n_phys,
            "pct_physical": round(n_phys / n_tasks, 4) if n_tasks else None,
            **metrics,
        }
        result.append(occ_dict)

    _explorer_occ_cache = result
    return result


def get_occupation_tasks(title: str) -> Optional[dict]:
    """
    Returns task-level details for one occupation, cross-referenced with
    all AEI versions, MCP v4, and Microsoft by task_normalized.
    Tasks are sorted alphabetically by the `task` column.
    pct_norm values are stored as-is from the CSV (already in % form, 0-100 range).
    """
    if title in _explorer_task_cache:
        return _explorer_task_cache[title]

    eco = load_eco_raw()
    if eco is None:
        return None

    occ_tasks = eco[eco["title_current"] == title].copy()
    if occ_tasks.empty:
        return None

    lookup = _build_explorer_task_lookup()

    # Sort by task name alphabetically
    occ_tasks = occ_tasks.sort_values("task")

    tasks_list = []
    seen_task_norm: set = set()

    for _, row in occ_tasks.iterrows():
        tn = row["task_normalized"]
        if tn in seen_task_norm:
            continue
        seen_task_norm.add(tn)

        sources = dict(lookup.get(tn, {}))

        # Avg/max across all sources
        auto_vals = [v["auto_aug"] for v in sources.values() if v.get("auto_aug") is not None]
        pct_vals  = [v["pct_norm"]  for v in sources.values() if v.get("pct_norm")  is not None]

        phys_val = row.get("physical")
        if phys_val is None or (isinstance(phys_val, float) and np.isnan(phys_val)):
            is_physical = None
        else:
            is_physical = bool(phys_val)

        tasks_list.append({
            "task":           row["task"],
            "task_normalized": tn,
            "dwa_title":      row.get("dwa_title"),
            "iwa_title":      row.get("iwa_title"),
            "gwa_title":      row.get("gwa_title"),
            "freq_mean":      _safe_num(row.get("freq_mean")),
            "importance":     _safe_num(row.get("importance")),
            "relevance":      _safe_num(row.get("relevance")),
            "physical":       is_physical,
            "sources":        sources,
            "avg_auto_aug":   round(sum(auto_vals) / len(auto_vals), 3) if auto_vals else None,
            "max_auto_aug":   round(max(auto_vals), 3)                  if auto_vals else None,
            "avg_pct_norm":   round(sum(pct_vals) / len(pct_vals), 4)  if pct_vals  else None,
            "max_pct_norm":   round(max(pct_vals), 4)                  if pct_vals  else None,
        })

    result = {"title": title, "tasks": tasks_list}
    _explorer_task_cache[title] = result
    return result


def _build_explorer_task_lookup() -> dict:
    """
    Builds and caches a dict: task_normalized -> {source_name: {"auto_aug": float|None, "pct_norm": float|None}}
    Sources: all AEI versions (using auto_aug_mean), MCP v4 (auto_aug_mean_adj), Microsoft (auto_aug_mean).
    """
    global _explorer_task_lookup_cache
    if _explorer_task_lookup_cache is not None:
        return _explorer_task_lookup_cache

    result: dict = {}

    for ds_name in AEI_EXPLORER_DATASETS:
        meta = DATASETS.get(ds_name, {})
        fpath = meta.get("file", "")
        if not Path(fpath).exists():
            continue
        df = pd.read_csv(fpath)
        if "task_normalized" not in df.columns:
            continue
        if "auto_aug_mean" not in df.columns:
            df["auto_aug_mean"] = np.nan
        if "pct_normalized" not in df.columns:
            df["pct_normalized"] = np.nan
        df["auto_aug_mean"] = pd.to_numeric(df["auto_aug_mean"], errors="coerce")
        df["pct_normalized"] = pd.to_numeric(df["pct_normalized"], errors="coerce")
        agg = df.groupby("task_normalized", sort=False).agg(
            auto_aug=("auto_aug_mean", "mean"),
            pct_norm=("pct_normalized", "mean"),
        ).reset_index()
        for _, row in agg.iterrows():
            tn = row["task_normalized"]
            if tn not in result:
                result[tn] = {}
            result[tn][ds_name] = {
                "auto_aug": _safe_num(row["auto_aug"]),
                "pct_norm": _safe_num(row["pct_norm"]),
            }

    # MCP v4
    mcp_meta = DATASETS.get("MCP v4", {})
    mcp_file = mcp_meta.get("file", "")
    if Path(mcp_file).exists():
        mcp = pd.read_csv(mcp_file)
        if "auto_aug_mean_adj" not in mcp.columns:
            mcp["auto_aug_mean_adj"] = np.nan
        if "pct_normalized" not in mcp.columns:
            mcp["pct_normalized"] = np.nan
        mcp["auto_aug_mean_adj"] = pd.to_numeric(mcp["auto_aug_mean_adj"], errors="coerce")
        mcp["pct_normalized"] = pd.to_numeric(mcp["pct_normalized"], errors="coerce")
        if "task_normalized" in mcp.columns:
            agg = mcp.groupby("task_normalized", sort=False).agg(
                auto_aug=("auto_aug_mean_adj", "mean"),
                pct_norm=("pct_normalized", "mean"),
            ).reset_index()
            for _, row in agg.iterrows():
                tn = row["task_normalized"]
                if tn not in result:
                    result[tn] = {}
                result[tn]["MCP"] = {
                    "auto_aug": _safe_num(row["auto_aug"]),
                    "pct_norm": _safe_num(row["pct_norm"]),
                }

    # Microsoft
    ms_meta = DATASETS.get("Microsoft", {})
    ms_file = ms_meta.get("file", "")
    if Path(ms_file).exists():
        ms = pd.read_csv(ms_file)
        if "auto_aug_mean" not in ms.columns:
            ms["auto_aug_mean"] = np.nan
        if "pct_normalized" not in ms.columns:
            ms["pct_normalized"] = np.nan
        ms["auto_aug_mean"] = pd.to_numeric(ms["auto_aug_mean"], errors="coerce")
        ms["pct_normalized"] = pd.to_numeric(ms["pct_normalized"], errors="coerce")
        if "task_normalized" in ms.columns:
            agg = ms.groupby("task_normalized", sort=False).agg(
                auto_aug=("auto_aug_mean", "mean"),
                pct_norm=("pct_normalized", "mean"),
            ).reset_index()
            for _, row in agg.iterrows():
                tn = row["task_normalized"]
                if tn not in result:
                    result[tn] = {}
                result[tn]["Microsoft"] = {
                    "auto_aug": _safe_num(row["auto_aug"]),
                    "pct_norm": _safe_num(row["pct_norm"]),
                }

    _explorer_task_lookup_cache = result
    return result


def _compute_task_metrics(task_norms: list, lookup: dict) -> dict:
    """
    Given a list of unique task_normalized values and the lookup, compute 10 metrics:
    - auto_avg_with_vals: avg of (per-task avg-across-sources), only tasks with >=1 source
    - auto_max_with_vals: avg of (per-task max-across-sources), only tasks with >=1 source
    - auto_avg_all:       sum of (per-task avg, nulls=0) / total_n_tasks
    - auto_max_all:       sum of (per-task max, nulls=0) / total_n_tasks
    - pct_avg_with_vals, pct_max_with_vals, pct_avg_all, pct_max_all  (same pattern)
    - sum_pct_avg:        sum of per-task pct_avg (only tasks with pct values)
    - sum_pct_max:        sum of per-task pct_max (only tasks with pct values)
    """
    total_n = len(task_norms)
    auto_avgs_with: list = []
    auto_maxs_with: list = []
    auto_avgs_sum = 0.0
    auto_maxs_sum = 0.0

    pct_avgs_with: list = []
    pct_maxs_with: list = []
    pct_avgs_sum = 0.0
    pct_maxs_sum = 0.0

    for tn in task_norms:
        sources = lookup.get(tn, {})

        auto_vals = [v["auto_aug"] for v in sources.values() if v.get("auto_aug") is not None]
        if auto_vals:
            t_avg = sum(auto_vals) / len(auto_vals)
            t_max = max(auto_vals)
            auto_avgs_with.append(t_avg)
            auto_maxs_with.append(t_max)
            auto_avgs_sum += t_avg
            auto_maxs_sum += t_max

        pct_vals = [v["pct_norm"] for v in sources.values() if v.get("pct_norm") is not None]
        if pct_vals:
            t_pct_avg = sum(pct_vals) / len(pct_vals)
            t_pct_max = max(pct_vals)
            pct_avgs_with.append(t_pct_avg)
            pct_maxs_with.append(t_pct_max)
            pct_avgs_sum += t_pct_avg
            pct_maxs_sum += t_pct_max

    n_with_auto = len(auto_avgs_with)
    n_with_pct  = len(pct_avgs_with)

    def _r3(v): return round(v, 3) if v is not None else None
    def _r4(v): return round(v, 4) if v is not None else None

    return {
        "auto_avg_with_vals": _r3(sum(auto_avgs_with) / n_with_auto) if n_with_auto else None,
        "auto_max_with_vals": _r3(sum(auto_maxs_with) / n_with_auto) if n_with_auto else None,
        "auto_avg_all":       _r3(auto_avgs_sum / total_n) if total_n else None,
        "auto_max_all":       _r3(auto_maxs_sum / total_n) if total_n else None,
        "pct_avg_with_vals":  _r4(sum(pct_avgs_with) / n_with_pct)  if n_with_pct  else None,
        "pct_max_with_vals":  _r4(sum(pct_maxs_with) / n_with_pct)  if n_with_pct  else None,
        "pct_avg_all":        _r4(pct_avgs_sum / total_n) if total_n else None,
        "pct_max_all":        _r4(pct_maxs_sum / total_n) if total_n else None,
        "sum_pct_avg":        _r4(pct_avgs_sum) if pct_avgs_with else None,
        "sum_pct_max":        _r4(pct_maxs_sum) if pct_maxs_with else None,
    }


def get_explorer_groups() -> dict:
    """
    Returns pre-computed aggregations for major/minor/broad levels.
    Each group's metrics are computed from unique task_norms across all occupations
    in that group (NOT averaged from occ-level values).
    Each row also includes parent hierarchy fields.
    Results are cached.
    """
    global _explorer_groups_cache
    if _explorer_groups_cache is not None:
        return _explorer_groups_cache

    eco = load_eco_raw()
    if eco is None:
        return {"major": [], "minor": [], "broad": []}

    lookup = _build_explorer_task_lookup()

    # Basic occ stats
    occ_basic = (
        eco.groupby("title_current")
        .agg(
            major   =("major_occ_category", "first"),
            minor   =("minor_occ_category", "first"),
            broad   =("broad_occ",          "first"),
            emp_nat =("emp_tot_nat_2024",    "first"),
            emp_ut  =("emp_tot_ut_2024",     "first"),
            wage_nat=("a_med_nat_2024",      "first"),
            wage_ut =("a_med_ut_2024",       "first"),
        )
        .reset_index()
    )

    # Unique (title, task_norm) pairs with physical flag
    task_pairs = eco[["title_current", "task_normalized", "physical"]].drop_duplicates(
        subset=["title_current", "task_normalized"]
    ).copy()

    def _phys_bool(v):
        if v is None:
            return False
        if isinstance(v, float) and np.isnan(v):
            return False
        return bool(v)

    task_pairs["physical_bool"] = task_pairs["physical"].apply(_phys_bool)

    # Build occ→level mappings
    occ_to_major = dict(zip(occ_basic["title_current"], occ_basic["major"]))
    occ_to_minor = dict(zip(occ_basic["title_current"], occ_basic["minor"]))
    occ_to_broad = dict(zip(occ_basic["title_current"], occ_basic["broad"]))
    occ_to_emp_nat  = dict(zip(occ_basic["title_current"], occ_basic["emp_nat"]))
    occ_to_emp_ut   = dict(zip(occ_basic["title_current"], occ_basic["emp_ut"]))
    occ_to_wage_nat = dict(zip(occ_basic["title_current"], occ_basic["wage_nat"]))
    occ_to_wage_ut  = dict(zip(occ_basic["title_current"], occ_basic["wage_ut"]))

    result: dict = {}

    level_configs = [
        ("major", occ_to_major, None,       None),
        ("minor", occ_to_minor, occ_to_major, None),
        ("broad", occ_to_broad, occ_to_minor, occ_to_major),
    ]

    for level_key, occ_to_level, occ_to_parent, occ_to_grandparent in level_configs:
        from collections import defaultdict
        level_to_occs: dict = defaultdict(set)
        for title in occ_basic["title_current"]:
            lv = occ_to_level.get(title) or "Unknown"
            level_to_occs[lv].add(title)

        groups_data = []
        for group_name in sorted(level_to_occs.keys()):
            occs = level_to_occs[group_name]

            # Unique task_norms for this group
            group_tasks = task_pairs[task_pairs["title_current"].isin(occs)]
            unique_task_norms = group_tasks["task_normalized"].unique().tolist()
            n_tasks = len(unique_task_norms)

            # Physical: count unique task_norms that are physical
            phys_by_task = group_tasks.groupby("task_normalized")["physical_bool"].any()
            n_phys = int(phys_by_task.sum())

            metrics = _compute_task_metrics(unique_task_norms, lookup)

            # Emp and wage
            total_emp_nat = sum((_safe_num(occ_to_emp_nat.get(t)) or 0) for t in occs)
            total_emp_ut  = sum((_safe_num(occ_to_emp_ut.get(t))  or 0) for t in occs)
            wage_sum_nat = 0.0; wage_emp_nat = 0.0
            wage_sum_ut  = 0.0; wage_emp_ut  = 0.0
            for t in occs:
                en = _safe_num(occ_to_emp_nat.get(t)) or 0
                eu = _safe_num(occ_to_emp_ut.get(t))  or 0
                wn = _safe_num(occ_to_wage_nat.get(t))
                wu = _safe_num(occ_to_wage_ut.get(t))
                if wn is not None and en > 0:
                    wage_sum_nat += wn * en; wage_emp_nat += en
                if wu is not None and eu > 0:
                    wage_sum_ut  += wu * eu; wage_emp_ut  += eu

            # Parent info (take mode from occs)
            parent_name = None
            grandparent_name = None
            if occ_to_parent is not None:
                from collections import Counter
                parents = [occ_to_parent.get(t) for t in occs if occ_to_parent.get(t)]
                if parents:
                    parent_name = Counter(parents).most_common(1)[0][0]
            if occ_to_grandparent is not None:
                from collections import Counter
                grandparents = [occ_to_grandparent.get(t) for t in occs if occ_to_grandparent.get(t)]
                if grandparents:
                    grandparent_name = Counter(grandparents).most_common(1)[0][0]

            row = {
                "name":    group_name,
                "parent":  parent_name,
                "grandparent": grandparent_name,
                "emp_nat": round(total_emp_nat, 0) if total_emp_nat else None,
                "emp_ut":  round(total_emp_ut,  0) if total_emp_ut  else None,
                "wage_nat": round(wage_sum_nat / wage_emp_nat, 0) if wage_emp_nat else None,
                "wage_ut":  round(wage_sum_ut  / wage_emp_ut,  0) if wage_emp_ut  else None,
                "n_occs":  len(occs),
                "n_tasks": n_tasks,
                "n_physical_tasks": n_phys,
                "pct_physical": round(n_phys / n_tasks, 4) if n_tasks else None,
                **metrics,
            }
            groups_data.append(row)

        result[level_key] = groups_data

    _explorer_groups_cache = result
    return result


def get_wa_explorer_data() -> list:
    """
    Returns WA explorer data: list of rows for GWA, IWA, DWA levels.
    Each row includes: level, name, parent, gwa, emp, wage, n_occs, n_tasks, metrics.
    emp uses the same allocation logic as the WA backend (emp_occ / n_unique_tasks_in_occ).
    AI metrics are computed from tasks deduplicated at each level (task_norm x activity).
    Results are cached.
    """
    global _wa_explorer_cache
    if _wa_explorer_cache is not None:
        return _wa_explorer_cache

    eco = load_eco_raw()
    if eco is None:
        return []

    lookup = _build_explorer_task_lookup()

    needed_cols = [
        "title_current", "task_normalized", "task",
        "dwa_title", "iwa_title", "gwa_title",
        "physical", "emp_tot_nat_2024", "emp_tot_ut_2024",
        "a_med_nat_2024", "a_med_ut_2024",
    ]
    avail_cols = [c for c in needed_cols if c in eco.columns]
    df = eco[avail_cols].copy()

    # n_unique_tasks_per_occ
    n_tasks_per_occ = (
        df.groupby("title_current")["task_normalized"]
        .nunique()
        .reset_index()
        .rename(columns={"task_normalized": "n_tasks_occ"})
    )
    df = df.merge(n_tasks_per_occ, on="title_current", how="left")

    for geo_col, emp_col in [("emp_per_task_nat", "emp_tot_nat_2024"), ("emp_per_task_ut", "emp_tot_ut_2024")]:
        if emp_col in df.columns:
            df[geo_col] = df[emp_col].fillna(0) / df["n_tasks_occ"].replace(0, np.nan)
        else:
            df[geo_col] = 0.0

    def _phys_bool(v):
        if v is None:
            return False
        if isinstance(v, float) and np.isnan(v):
            return False
        return bool(v)

    df["physical_bool"] = df["physical"].apply(_phys_bool)

    rows_out: list = []

    level_specs = [
        ("gwa", "gwa_title", None,        "gwa_title"),
        ("iwa", "iwa_title", "gwa_title", "gwa_title"),
        ("dwa", "dwa_title", "iwa_title", "gwa_title"),
    ]

    for level_key, act_col, parent_col, gwa_col in level_specs:
        if act_col not in df.columns:
            continue

        level_df = df[df[act_col].notna()].copy()
        if level_df.empty:
            continue

        # Unique (task_norm, act) pairs for deduplication at this level
        unique_pairs = level_df[[act_col, "task_normalized"]].drop_duplicates()

        for act_name, act_df in sorted(level_df.groupby(act_col), key=lambda x: x[0]):
            # emp: sum emp_per_task across unique (occ, task_norm) combos
            occ_task_dedup = act_df.drop_duplicates(subset=["title_current", "task_normalized"])
            total_emp_nat = occ_task_dedup["emp_per_task_nat"].fillna(0).sum()
            total_emp_ut  = occ_task_dedup["emp_per_task_ut"].fillna(0).sum()

            # wage: emp-weighted avg
            wage_sum_nat = 0.0; wage_emp_nat = 0.0
            wage_sum_ut  = 0.0; wage_emp_ut  = 0.0
            for _, r in occ_task_dedup.iterrows():
                en = _safe_num(r.get("emp_per_task_nat")) or 0
                eu = _safe_num(r.get("emp_per_task_ut"))  or 0
                wn = _safe_num(r.get("a_med_nat_2024"))
                wu = _safe_num(r.get("a_med_ut_2024"))
                if wn is not None and en > 0:
                    wage_sum_nat += wn * en; wage_emp_nat += en
                if wu is not None and eu > 0:
                    wage_sum_ut  += wu * eu; wage_emp_ut  += eu

            n_occs = int(act_df["title_current"].nunique())

            # Unique task_norms at this activity level
            unique_task_norms = unique_pairs[unique_pairs[act_col] == act_name]["task_normalized"].unique().tolist()
            n_tasks = len(unique_task_norms)

            # Physical: unique tasks that are physical
            phys_by_task = act_df.drop_duplicates(subset=["task_normalized"]).set_index("task_normalized")["physical_bool"]
            n_phys = int(phys_by_task.sum())

            metrics = _compute_task_metrics(unique_task_norms, lookup)

            # Parent / gwa info
            parent_name = None
            gwa_name    = None
            if parent_col and parent_col in act_df.columns:
                from collections import Counter
                parents = [v for v in act_df[parent_col].dropna() if v]
                parent_name = Counter(parents).most_common(1)[0][0] if parents else None
            if gwa_col and gwa_col in act_df.columns:
                from collections import Counter
                gwas = [v for v in act_df[gwa_col].dropna() if v]
                gwa_name = Counter(gwas).most_common(1)[0][0] if gwas else None
            elif level_key == "gwa":
                gwa_name = act_name

            rows_out.append({
                "level":   level_key,
                "name":    str(act_name),
                "parent":  parent_name,
                "gwa":     gwa_name,
                "emp_nat": round(float(total_emp_nat), 1) if total_emp_nat else None,
                "emp_ut":  round(float(total_emp_ut),  1) if total_emp_ut  else None,
                "wage_nat": round(wage_sum_nat / wage_emp_nat, 0) if wage_emp_nat else None,
                "wage_ut":  round(wage_sum_ut  / wage_emp_ut,  0) if wage_emp_ut  else None,
                "n_occs":  n_occs,
                "n_tasks": n_tasks,
                "n_physical_tasks": n_phys,
                "pct_physical": round(n_phys / n_tasks, 4) if n_tasks else None,
                **metrics,
            })

    _wa_explorer_cache = rows_out
    return rows_out


def get_wa_tasks_for_activity(level: str, name: str) -> list:
    """
    Returns task-level details for a specific WA activity (gwa/iwa/dwa).
    Tasks are deduplicated by task_normalized, with emp summed across all occupations.
    """
    eco = load_eco_raw()
    if eco is None:
        return []

    lookup = _build_explorer_task_lookup()

    act_col_map = {"gwa": "gwa_title", "iwa": "iwa_title", "dwa": "dwa_title"}
    act_col = act_col_map.get(level)
    if not act_col or act_col not in eco.columns:
        return []

    # Filter to this activity
    act_df = eco[eco[act_col] == name].copy()
    if act_df.empty:
        return []

    # emp allocation
    n_tasks_per_occ = (
        eco.groupby("title_current")["task_normalized"]
        .nunique()
        .reset_index()
        .rename(columns={"task_normalized": "n_tasks_occ"})
    )
    act_df = act_df.merge(n_tasks_per_occ, on="title_current", how="left")
    if "emp_tot_nat_2024" in act_df.columns:
        act_df["emp_per_task_nat"] = act_df["emp_tot_nat_2024"].fillna(0) / act_df["n_tasks_occ"].replace(0, np.nan)
    else:
        act_df["emp_per_task_nat"] = 0.0
    if "emp_tot_ut_2024" in act_df.columns:
        act_df["emp_per_task_ut"] = act_df["emp_tot_ut_2024"].fillna(0) / act_df["n_tasks_occ"].replace(0, np.nan)
    else:
        act_df["emp_per_task_ut"] = 0.0

    def _phys_bool(v):
        if v is None: return False
        if isinstance(v, float) and np.isnan(v): return False
        return bool(v)

    tasks_out = []
    seen_norms = set()

    for tn, grp in act_df.groupby("task_normalized"):
        if tn in seen_norms:
            continue
        seen_norms.add(tn)

        # Use first row for task text, hierarchy, physical
        first = grp.iloc[0]
        emp_nat = float(grp.drop_duplicates(subset=["title_current"])["emp_per_task_nat"].fillna(0).sum())
        emp_ut  = float(grp.drop_duplicates(subset=["title_current"])["emp_per_task_ut"].fillna(0).sum())

        # wage: emp-weighted avg
        wage_sum_nat = 0.0; wage_emp_nat = 0.0
        for _, r in grp.drop_duplicates(subset=["title_current"]).iterrows():
            en = _safe_num(r.get("emp_per_task_nat")) or 0
            wn = _safe_num(r.get("a_med_nat_2024"))
            if wn is not None and en > 0:
                wage_sum_nat += wn * en; wage_emp_nat += en

        sources = lookup.get(tn, {})
        auto_vals = [v["auto_aug"] for v in sources.values() if v.get("auto_aug") is not None]
        pct_vals  = [v["pct_norm"]  for v in sources.values() if v.get("pct_norm")  is not None]

        phys_val = first.get("physical")
        is_physical = None
        if phys_val is not None and not (isinstance(phys_val, float) and np.isnan(phys_val)):
            is_physical = bool(phys_val)

        tasks_out.append({
            "task":           str(first.get("task", tn)),
            "task_normalized": tn,
            "dwa_title":      first.get("dwa_title"),
            "iwa_title":      first.get("iwa_title"),
            "gwa_title":      first.get("gwa_title"),
            "physical":       is_physical,
            "emp_nat":        round(emp_nat, 2) if emp_nat else None,
            "emp_ut":         round(emp_ut,  2) if emp_ut  else None,
            "wage_nat":       round(wage_sum_nat / wage_emp_nat, 0) if wage_emp_nat else None,
            "sources":        dict(sources),
            "avg_auto_aug":   round(sum(auto_vals) / len(auto_vals), 3) if auto_vals else None,
            "max_auto_aug":   round(max(auto_vals), 3) if auto_vals else None,
            "avg_pct_norm":   round(sum(pct_vals) / len(pct_vals), 4) if pct_vals else None,
            "max_pct_norm":   round(max(pct_vals), 4) if pct_vals else None,
        })

    tasks_out.sort(key=lambda t: t["task"])
    return tasks_out


def get_all_tasks() -> list:
    """
    Returns all unique tasks from eco_2025 with their AI metrics from the task lookup.
    Each task row includes: task, task_normalized, dwa_title, iwa_title, gwa_title,
    physical, n_occs (unique occ count), avg_auto_aug, max_auto_aug, avg_pct_norm, max_pct_norm,
    plus the sources dict.
    Results are cached.
    """
    global _all_tasks_cache
    if _all_tasks_cache is not None:
        return _all_tasks_cache

    eco = load_eco_raw()
    if eco is None:
        return []

    lookup = _build_explorer_task_lookup()

    # Get unique tasks with their metadata (use first occurrence for text/hierarchy)
    task_cols = ["task_normalized", "task", "dwa_title", "iwa_title", "gwa_title", "physical"]
    avail = [c for c in task_cols if c in eco.columns]
    task_meta = eco[avail].drop_duplicates(subset=["task_normalized"]).copy()

    # Count unique occs per task
    occ_counts = (
        eco.groupby("task_normalized")["title_current"]
        .nunique()
        .reset_index()
        .rename(columns={"title_current": "n_occs"})
    )
    task_meta = task_meta.merge(occ_counts, on="task_normalized", how="left")

    def _phys_bool(v):
        if v is None: return False
        if isinstance(v, float) and np.isnan(v): return False
        return bool(v)

    result = []
    for _, row in task_meta.sort_values("task").iterrows():
        tn = row["task_normalized"]
        sources = dict(lookup.get(tn, {}))
        auto_vals = [v["auto_aug"] for v in sources.values() if v.get("auto_aug") is not None]
        pct_vals  = [v["pct_norm"]  for v in sources.values() if v.get("pct_norm")  is not None]

        phys_val = row.get("physical")
        is_physical = None
        if phys_val is not None and not (isinstance(phys_val, float) and np.isnan(phys_val)):
            is_physical = bool(phys_val)

        result.append({
            "task":           str(row.get("task", tn)),
            "task_normalized": tn,
            "dwa_title":      row.get("dwa_title"),
            "iwa_title":      row.get("iwa_title"),
            "gwa_title":      row.get("gwa_title"),
            "physical":       is_physical,
            "n_occs":         int(row.get("n_occs", 0)),
            "sources":        sources,
            "avg_auto_aug":   round(sum(auto_vals) / len(auto_vals), 3) if auto_vals else None,
            "max_auto_aug":   round(max(auto_vals), 3)                  if auto_vals else None,
            "avg_pct_norm":   round(sum(pct_vals) / len(pct_vals), 4)  if pct_vals  else None,
            "max_pct_norm":   round(max(pct_vals), 4)                  if pct_vals  else None,
        })

    _all_tasks_cache = result
    return result
