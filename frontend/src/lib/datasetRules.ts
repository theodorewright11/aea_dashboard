/**
 * datasetRules.ts — Shared dataset selection enforcement rules.
 *
 * Rules:
 * - Multiple snapshot AEI versions can be selected together (existing behavior).
 * - Only ONE cumulative AEI version at a time (v4 contains v1–v3; selecting multiple is meaningless).
 * - Cannot mix snapshot AEI and cumulative AEI in the same group.
 * - Only ONE MCP version at a time.
 * - AEI (snapshot or cumulative) can be freely mixed with MCP and Microsoft.
 */

export interface DatasetClassification {
  aeiSnapshotDatasets: string[];
  aeiCumulativeDatasets: string[];
  mcpDatasets: string[];
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
  const isCumul    = cls.aeiCumulativeDatasets.includes(name);
  const isSnapshot = cls.aeiSnapshotDatasets.includes(name);
  const isMCP      = cls.mcpDatasets.includes(name);
  const isSel      = current.includes(name);

  // Deselect — always allowed
  if (isSel) {
    return current.filter((d) => d !== name);
  }

  // Adding — apply rules
  let next = [...current];

  if (isCumul) {
    // Remove all cumulative (only one allowed) and all snapshot AEI (no mixing)
    next = next.filter(
      (d) => !cls.aeiCumulativeDatasets.includes(d) && !cls.aeiSnapshotDatasets.includes(d),
    );
  } else if (isSnapshot) {
    // Remove all cumulative AEI (no mixing)
    next = next.filter((d) => !cls.aeiCumulativeDatasets.includes(d));
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
  const selCumul    = current.filter((d) => cls.aeiCumulativeDatasets.includes(d));
  const selSnapshot = current.filter((d) => cls.aeiSnapshotDatasets.includes(d));
  const selMCP      = current.filter((d) => cls.mcpDatasets.includes(d));

  if (selCumul.length > 1) return "Only one cumulative AEI version can be selected at a time.";
  if (selCumul.length > 0 && selSnapshot.length > 0) return "Cannot mix snapshot and cumulative AEI datasets.";
  if (selMCP.length > 1) return "Only one MCP version can be selected at a time.";
  return null;
}
