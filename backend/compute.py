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
    Returns a list of all occupations from eco_2025 with hierarchy, employment,
    wage stats, and average AI metrics (auto_aug, pct_normalized) from AEI v4,
    MCP v4, and Microsoft — looked up by task_normalized.
    """
    global _explorer_occ_cache
    if _explorer_occ_cache is not None:
        return _explorer_occ_cache

    eco = load_eco_raw()
    if eco is None:
        return []

    # Load AI datasets
    aei_file = DATASETS.get("AEI v4", {}).get("file", "")
    mcp_file = DATASETS.get("MCP v4", {}).get("file", "")
    ms_file  = DATASETS.get("Microsoft", {}).get("file", "")

    aei = pd.read_csv(aei_file) if Path(aei_file).exists() else None
    mcp = pd.read_csv(mcp_file) if Path(mcp_file).exists() else None
    ms  = pd.read_csv(ms_file)  if Path(ms_file).exists()  else None

    def build_task_lookup(df, auto_col, pct_col="pct_normalized"):
        if df is None or df.empty:
            return {}
        cols = [c for c in [auto_col, pct_col, "task_normalized"] if c in df.columns]
        if "task_normalized" not in cols:
            return {}
        sub = df[cols].copy()
        sub[auto_col] = pd.to_numeric(sub[auto_col], errors="coerce")
        sub[pct_col]  = pd.to_numeric(sub.get(pct_col, pd.Series(dtype=float)), errors="coerce")
        agg = sub.groupby("task_normalized").agg(
            auto_aug=(auto_col, "mean"),
            pct_norm=(pct_col,  "mean"),
        )
        return agg.to_dict(orient="index")

    aei_lookup = build_task_lookup(aei, "auto_aug_mean")
    mcp_lookup = build_task_lookup(mcp, "auto_aug_mean_adj")
    ms_lookup  = build_task_lookup(ms,  "auto_aug_mean")

    task_occ = eco[["title_current", "task_normalized"]].drop_duplicates()

    def occ_avg_stats(lookup):
        if not lookup:
            return {}
        rows = []
        for _, r in task_occ.iterrows():
            tn = r["task_normalized"]
            if tn in lookup:
                rows.append({"title_current": r["title_current"], **lookup[tn]})
        if not rows:
            return {}
        df2 = pd.DataFrame(rows)
        return (
            df2.groupby("title_current")
            .agg(avg_auto=("auto_aug", "mean"), avg_pct=("pct_norm", "mean"))
            .to_dict(orient="index")
        )

    aei_occ = occ_avg_stats(aei_lookup)
    mcp_occ = occ_avg_stats(mcp_lookup)
    ms_occ  = occ_avg_stats(ms_lookup)

    occ_stats = (
        eco.groupby("title_current")
        .agg(
            major  =("major_occ_category", "first"),
            minor  =("minor_occ_category", "first"),
            broad  =("broad_occ",           "first"),
            emp_nat=("emp_tot_nat_2024",    "first"),
            emp_ut =("emp_tot_ut_2024",     "first"),
            wage_nat=("a_med_nat_2024",     "first"),
            wage_ut =("a_med_ut_2024",      "first"),
            n_tasks =("task_normalized",    "nunique"),
        )
        .reset_index()
    )

    result = []
    for _, row in occ_stats.iterrows():
        title = row["title_current"]
        occ_dict: dict = {
            "title_current": title,
            "major":   row.get("major"),
            "minor":   row.get("minor"),
            "broad":   row.get("broad"),
            "emp_nat":  _safe_num(row.get("emp_nat")),
            "emp_ut":   _safe_num(row.get("emp_ut")),
            "wage_nat": _safe_num(row.get("wage_nat")),
            "wage_ut":  _safe_num(row.get("wage_ut")),
            "n_tasks":  int(row.get("n_tasks", 0)),
        }
        for src_key, src_dict in [("aei", aei_occ), ("mcp", mcp_occ), ("ms", ms_occ)]:
            if title in src_dict:
                s = src_dict[title]
                occ_dict[f"avg_auto_aug_{src_key}"] = round(float(s["avg_auto"]), 3) if s["avg_auto"] is not None and not np.isnan(s["avg_auto"]) else None
                occ_dict[f"avg_pct_norm_{src_key}"] = round(float(s["avg_pct"]),  4) if s["avg_pct"]  is not None and not np.isnan(s["avg_pct"])  else None
            else:
                occ_dict[f"avg_auto_aug_{src_key}"] = None
                occ_dict[f"avg_pct_norm_{src_key}"] = None
        result.append(occ_dict)

    _explorer_occ_cache = result
    return result


def get_occupation_tasks(title: str) -> Optional[dict]:
    """
    Returns task-level details for one occupation, cross-referenced with
    AEI v4, MCP v4, and Microsoft by task_normalized.
    Includes 'physical' flag from eco_2025.
    """
    if title in _explorer_task_cache:
        return _explorer_task_cache[title]

    eco = load_eco_raw()
    if eco is None:
        return None

    occ_tasks = eco[eco["title_current"] == title].copy()
    if occ_tasks.empty:
        return None

    aei_file = DATASETS.get("AEI v4", {}).get("file", "")
    mcp_file = DATASETS.get("MCP v4", {}).get("file", "")
    ms_file  = DATASETS.get("Microsoft", {}).get("file", "")

    aei = pd.read_csv(aei_file) if Path(aei_file).exists() else None
    mcp = pd.read_csv(mcp_file) if Path(mcp_file).exists() else None
    ms  = pd.read_csv(ms_file)  if Path(ms_file).exists()  else None

    def task_lookup(df, auto_col, pct_col="pct_normalized"):
        if df is None:
            return {}
        cols = [c for c in [auto_col, pct_col, "task_normalized"] if c in df.columns]
        if "task_normalized" not in cols:
            return {}
        sub = df[cols].copy()
        for c in [auto_col, pct_col]:
            if c in sub.columns:
                sub[c] = pd.to_numeric(sub[c], errors="coerce")
        agg = sub.groupby("task_normalized").agg(
            auto=(auto_col, "mean"),
            pct =(pct_col,  "mean"),
        )
        return {tn: {"auto": row["auto"], "pct": row["pct"]} for tn, row in agg.iterrows()}

    aei_tasks = task_lookup(aei, "auto_aug_mean")
    mcp_tasks = task_lookup(mcp, "auto_aug_mean_adj")
    ms_tasks  = task_lookup(ms,  "auto_aug_mean")

    tasks_list = []
    seen_task_norm = set()
    for _, row in occ_tasks.iterrows():
        tn = row["task_normalized"]
        if tn in seen_task_norm:
            continue
        seen_task_norm.add(tn)

        aei_info = None
        mcp_info = None
        ms_info  = None

        if tn in aei_tasks:
            r = aei_tasks[tn]
            aei_info = {
                "auto_aug_mean":   round(float(r["auto"]), 3) if _safe_num(r["auto"]) is not None else None,
                "pct_normalized":  round(float(r["pct"]),  4) if _safe_num(r["pct"])  is not None else None,
            }
        if tn in mcp_tasks:
            r = mcp_tasks[tn]
            mcp_info = {
                "auto_aug_mean_adj": round(float(r["auto"]), 3) if _safe_num(r["auto"]) is not None else None,
                "pct_normalized":    round(float(r["pct"]),  4) if _safe_num(r["pct"])  is not None else None,
            }
        if tn in ms_tasks:
            r = ms_tasks[tn]
            ms_info = {
                "auto_aug_mean":  round(float(r["auto"]), 3) if _safe_num(r["auto"]) is not None else None,
                "pct_normalized": round(float(r["pct"]),  4) if _safe_num(r["pct"])  is not None else None,
            }

        auto_vals = [
            v for v in [
                aei_info["auto_aug_mean"]     if aei_info else None,
                mcp_info["auto_aug_mean_adj"] if mcp_info else None,
                ms_info["auto_aug_mean"]      if ms_info  else None,
            ] if v is not None
        ]
        pct_vals = [
            v for v in [
                aei_info["pct_normalized"] if aei_info else None,
                mcp_info["pct_normalized"] if mcp_info else None,
                ms_info["pct_normalized"]  if ms_info  else None,
            ] if v is not None
        ]

        # Physical flag from eco_2025
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
            "aei":            aei_info,
            "mcp":            mcp_info,
            "microsoft":      ms_info,
            "avg_auto_aug":     round(sum(auto_vals) / len(auto_vals), 3) if auto_vals else None,
            "max_auto_aug":     round(max(auto_vals), 3)                  if auto_vals else None,
            "avg_pct_normalized": round(sum(pct_vals) / len(pct_vals), 4) if pct_vals else None,
            "max_pct_normalized": round(max(pct_vals), 4)                 if pct_vals else None,
        })

    result = {"title": title, "tasks": tasks_list}
    _explorer_task_cache[title] = result
    return result
