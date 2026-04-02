/**
 * datasetRules.ts — Dataset category helpers for the new UI organization.
 *
 * Datasets are organized into categories (Snapshots, Usage, Agentic, All),
 * each containing sub_types, each with date-indexed datasets.
 *
 * Chart pages, PctComputePanel, and Task Changes use single-dataset selection
 * (one sub_type + one date). Trends uses date-range + multi-select sub_types.
 */

import type { DatasetCategory, SubType, DatasetEntry, ConfigResponse } from "./types";

/** Flat lookup: dataset name → { categoryKey, subTypeKey, date } */
export interface DatasetInfo {
  categoryKey: string;
  subTypeKey: string;
  date: string;
}

/** Build a flat lookup from dataset name → info. */
export function buildDatasetLookup(
  categories: DatasetCategory[],
): Record<string, DatasetInfo> {
  const lookup: Record<string, DatasetInfo> = {};
  for (const cat of categories) {
    for (const st of cat.sub_types) {
      for (const ds of st.datasets) {
        lookup[ds.name] = {
          categoryKey: cat.key,
          subTypeKey: st.key,
          date: ds.date,
        };
      }
    }
  }
  return lookup;
}

/** Get all unique dates across all sub_types, sorted ascending. */
export function getAllDates(categories: DatasetCategory[]): string[] {
  const dateSet = new Set<string>();
  for (const cat of categories) {
    for (const st of cat.sub_types) {
      for (const ds of st.datasets) {
        dateSet.add(ds.date);
      }
    }
  }
  return Array.from(dateSet).sort();
}

/** Get all unique dates for a specific sub_type. */
export function getDatesForSubType(
  categories: DatasetCategory[],
  subTypeKey: string,
): string[] {
  for (const cat of categories) {
    for (const st of cat.sub_types) {
      if (st.key === subTypeKey) {
        return st.datasets.map((d) => d.date);
      }
    }
  }
  return [];
}

/** Resolve a sub_type key + date to a dataset name. Returns undefined if not found. */
export function resolveDataset(
  categories: DatasetCategory[],
  subTypeKey: string,
  date: string,
): string | undefined {
  for (const cat of categories) {
    for (const st of cat.sub_types) {
      if (st.key === subTypeKey) {
        const entry = st.datasets.find((d) => d.date === date);
        return entry?.name;
      }
    }
  }
  return undefined;
}

/** Find a sub_type by key across all categories. */
export function findSubType(
  categories: DatasetCategory[],
  subTypeKey: string,
): SubType | undefined {
  for (const cat of categories) {
    for (const st of cat.sub_types) {
      if (st.key === subTypeKey) return st;
    }
  }
  return undefined;
}

/** Get all sub_types across all categories as a flat list with category info. */
export function getAllSubTypes(
  categories: DatasetCategory[],
): Array<{ categoryKey: string; categoryLabel: string; subType: SubType }> {
  const result: Array<{ categoryKey: string; categoryLabel: string; subType: SubType }> = [];
  for (const cat of categories) {
    for (const st of cat.sub_types) {
      result.push({ categoryKey: cat.key, categoryLabel: cat.label, subType: st });
    }
  }
  return result;
}

/** Get the latest (most recent) dataset name for a given sub_type key. */
export function getLatestDataset(
  categories: DatasetCategory[],
  subTypeKey: string,
): string | undefined {
  const st = findSubType(categories, subTypeKey);
  if (!st || st.datasets.length === 0) return undefined;
  return st.datasets[st.datasets.length - 1].name;
}

/**
 * Filter sub_types that have at least one dataset within the given date range.
 * Returns sub_types with their datasets filtered to only include dates in range.
 */
export function filterSubTypesByDateRange(
  categories: DatasetCategory[],
  fromDate: string,
  toDate: string,
): Array<{ categoryKey: string; categoryLabel: string; subType: SubType; filteredDatasets: DatasetEntry[] }> {
  const result: Array<{ categoryKey: string; categoryLabel: string; subType: SubType; filteredDatasets: DatasetEntry[] }> = [];
  for (const cat of categories) {
    for (const st of cat.sub_types) {
      const filtered = st.datasets.filter((d) => d.date >= fromDate && d.date <= toDate);
      if (filtered.length > 0) {
        result.push({ categoryKey: cat.key, categoryLabel: cat.label, subType: st, filteredDatasets: filtered });
      }
    }
  }
  return result;
}
