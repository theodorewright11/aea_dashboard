/**
 * datasetRules.ts — Shared dataset selection enforcement rules.
 *
 * Families and rules:
 *
 * AEI Conversation family:
 *   Snapshots: AEI Conv. v1–v4
 *   Cumulative: AEI Cumul. Conv. v1–v4
 *   - Only one cumulative at a time.
 *   - Cannot mix snapshots with cumulative in same family.
 *
 * AEI API family:
 *   Snapshots: AEI API v3–v4
 *   Cumulative: AEI API Cumul. v4
 *   - Only one cumulative at a time.
 *   - Cannot mix snapshots with cumulative in same family.
 *
 * AEI Cumul. (Both) family:
 *   AEI Cumul. (Both) v3–v4
 *   - Only one at a time.
 *   - If selected, blocks ALL other AEI datasets (conv snapshots, conv cumul,
 *     API snapshots, API cumul).
 *
 * MCP family:
 *   MCP Cumul. v1–v4
 *   - Only one at a time.
 */

export interface DatasetClassification {
  aeiConvSnapshotDatasets: string[];
  aeiApiSnapshotDatasets: string[];
  aeiConvCumulativeDatasets: string[];
  aeiApiCumulativeDatasets: string[];
  aeiBothCumulativeDatasets: string[];
  mcpDatasets: string[];
}

/** All AEI dataset names (every family). */
function allAeiNames(cls: DatasetClassification): string[] {
  return [
    ...cls.aeiConvSnapshotDatasets,
    ...cls.aeiApiSnapshotDatasets,
    ...cls.aeiConvCumulativeDatasets,
    ...cls.aeiApiCumulativeDatasets,
    ...cls.aeiBothCumulativeDatasets,
  ];
}

/**
 * Returns the new selection after toggling `name`, with enforcement rules applied.
 * Auto-deselects conflicting choices.
 */
export function enforceDatasetToggle(
  current: string[],
  name: string,
  cls: DatasetClassification,
): string[] {
  const isConvSnap   = cls.aeiConvSnapshotDatasets.includes(name);
  const isApiSnap    = cls.aeiApiSnapshotDatasets.includes(name);
  const isConvCumul  = cls.aeiConvCumulativeDatasets.includes(name);
  const isApiCumul   = cls.aeiApiCumulativeDatasets.includes(name);
  const isBothCumul  = cls.aeiBothCumulativeDatasets.includes(name);
  const isMCP        = cls.mcpDatasets.includes(name);
  const isSel        = current.includes(name);

  // Deselect — always allowed
  if (isSel) {
    return current.filter((d) => d !== name);
  }

  // Adding — apply rules
  let next = [...current];
  const allAei = allAeiNames(cls);

  if (isBothCumul) {
    // Remove ALL other AEI datasets + other "Both" cumulative
    next = next.filter((d) => !allAei.includes(d));
  } else if (isConvSnap) {
    // Remove conv cumulative (no mixing snapshot + cumulative in same family)
    // Also remove "Both" cumulative (blocks all AEI)
    next = next.filter(
      (d) =>
        !cls.aeiConvCumulativeDatasets.includes(d) &&
        !cls.aeiBothCumulativeDatasets.includes(d),
    );
  } else if (isConvCumul) {
    // Remove other conv cumulative (only one) + conv snapshots (no mixing) + "Both"
    next = next.filter(
      (d) =>
        !cls.aeiConvCumulativeDatasets.includes(d) &&
        !cls.aeiConvSnapshotDatasets.includes(d) &&
        !cls.aeiBothCumulativeDatasets.includes(d),
    );
  } else if (isApiSnap) {
    // Remove API cumulative (no mixing) + "Both"
    next = next.filter(
      (d) =>
        !cls.aeiApiCumulativeDatasets.includes(d) &&
        !cls.aeiBothCumulativeDatasets.includes(d),
    );
  } else if (isApiCumul) {
    // Remove other API cumulative (only one) + API snapshots (no mixing) + "Both"
    next = next.filter(
      (d) =>
        !cls.aeiApiCumulativeDatasets.includes(d) &&
        !cls.aeiApiSnapshotDatasets.includes(d) &&
        !cls.aeiBothCumulativeDatasets.includes(d),
    );
  } else if (isMCP) {
    // Remove all other MCP (only one allowed)
    next = next.filter((d) => !cls.mcpDatasets.includes(d));
  }

  return [...next, name];
}

/**
 * Returns a conflict message if the current selection violates the rules,
 * or null if valid.
 */
export function getDatasetConflictMessage(
  current: string[],
  cls: DatasetClassification,
): string | null {
  const allAei = allAeiNames(cls);
  const selBoth     = current.filter((d) => cls.aeiBothCumulativeDatasets.includes(d));
  const selConvCum  = current.filter((d) => cls.aeiConvCumulativeDatasets.includes(d));
  const selConvSnap = current.filter((d) => cls.aeiConvSnapshotDatasets.includes(d));
  const selApiCum   = current.filter((d) => cls.aeiApiCumulativeDatasets.includes(d));
  const selApiSnap  = current.filter((d) => cls.aeiApiSnapshotDatasets.includes(d));
  const selMCP      = current.filter((d) => cls.mcpDatasets.includes(d));

  if (selBoth.length > 1) return "Only one AEI Cumul. (Both) version can be selected at a time.";
  if (selBoth.length > 0) {
    const otherAei = current.filter((d) => allAei.includes(d) && !cls.aeiBothCumulativeDatasets.includes(d));
    if (otherAei.length > 0) return "AEI Cumul. (Both) cannot be mixed with other AEI datasets.";
  }
  if (selConvCum.length > 1) return "Only one AEI Cumul. Conv. version can be selected at a time.";
  if (selConvCum.length > 0 && selConvSnap.length > 0) return "Cannot mix AEI Conv. snapshots with AEI Cumul. Conv. datasets.";
  if (selApiCum.length > 1) return "Only one AEI API Cumul. version can be selected at a time.";
  if (selApiCum.length > 0 && selApiSnap.length > 0) return "Cannot mix AEI API snapshots with AEI API Cumul. datasets.";
  if (selMCP.length > 1) return "Only one MCP Cumul. version can be selected at a time.";
  return null;
}

/** Dataset UI subsections for organized display. */
export interface DatasetSubsection {
  label: string;
  datasets: string[];
}

export function getDatasetSubsections(cls: DatasetClassification): DatasetSubsection[] {
  return [
    { label: "AEI Conversation",  datasets: [...cls.aeiConvSnapshotDatasets, ...cls.aeiConvCumulativeDatasets] },
    { label: "AEI API",           datasets: [...cls.aeiApiSnapshotDatasets, ...cls.aeiApiCumulativeDatasets] },
    { label: "AEI Cumul. (Both)", datasets: cls.aeiBothCumulativeDatasets },
    { label: "MCP",               datasets: cls.mcpDatasets },
    { label: "Microsoft",         datasets: ["Microsoft"] },
  ];
}

/** Build a DatasetClassification from a ConfigResponse. */
export function classificationFromConfig(config: {
  aei_conv_snapshot_datasets: string[];
  aei_api_snapshot_datasets: string[];
  aei_conv_cumulative_datasets: string[];
  aei_api_cumulative_datasets: string[];
  aei_both_cumulative_datasets: string[];
  mcp_datasets: string[];
}): DatasetClassification {
  return {
    aeiConvSnapshotDatasets: config.aei_conv_snapshot_datasets,
    aeiApiSnapshotDatasets: config.aei_api_snapshot_datasets,
    aeiConvCumulativeDatasets: config.aei_conv_cumulative_datasets,
    aeiApiCumulativeDatasets: config.aei_api_cumulative_datasets,
    aeiBothCumulativeDatasets: config.aei_both_cumulative_datasets,
    mcpDatasets: config.mcp_datasets,
  };
}
