export function SemanticLabel({ kind }: { kind: "Evidence" | "Interpretation" | "Prediction" }) {
  return <span className={`semantic semantic-${kind.toLowerCase()}`}>{kind}</span>;
}
