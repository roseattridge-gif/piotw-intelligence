import { SemanticLabel } from "./semantic-label";
import type {
  FinancialLinkage,
  InterventionPriority,
  OperationalDimensionScore,
  OperationalIndex,
  PeerBenchmark,
  RatingDriver,
} from "@/types/intelligence";

const trendMark = (trend: string) => trend === "Improving" ? "↑" : trend === "Deteriorating" ? "↓" : "→";

export function OperationalIndexPanel({ index, benchmark }: { index: OperationalIndex; benchmark: PeerBenchmark }) {
  return <section className="index-section section">
    <div className="index-heading"><div><p className="eyebrow">PIOTW rating</p><h2>Operational strength, benchmarked and explained.</h2></div><span className="development-status">{index.methodologyStatus}</span></div>
    <div className="index-layout">
      <div className="index-primary">
        <div className="index-score" style={{background:`conic-gradient(var(--rust) 0 ${index.score}%, var(--paper-deep) ${index.score}% 100%)`}}><div><strong>{index.score}</strong><span>/ 100</span></div></div>
        <div className="index-rating"><span>Rating</span><strong>{index.rating}</strong><em>{index.outlook ?? index.trend}</em><p>Development benchmark position is below the displayed sector median. Evidence confidence is reported separately.</p></div>
        <dl className="index-facts"><div><dt>Operational outlook</dt><dd>{index.outlook ?? index.trend}</dd></div><div><dt>Trend</dt><dd className="negative">{trendMark(index.trend)} {index.change !== undefined ? `${Math.abs(index.change)} points` : index.trend}</dd></div><div><dt>Sector position</dt><dd>{index.sectorPercentile ? `${index.sectorPercentile}rd percentile` : "Not available"}</dd></div></dl>
      </div>
      <div className="benchmark-panel">
        <div className="benchmark-heading"><p className="eyebrow">Peer benchmark</p><strong>{benchmark.name}</strong></div>
        <div className="benchmark-scale" aria-label={`Company score ${benchmark.companyScore}; lower quartile ${benchmark.lowerQuartile}; median ${benchmark.medianScore}; upper quartile ${benchmark.upperQuartile}`}>
          <div className="benchmark-track"><span className="quartile lower" style={{left:`${benchmark.lowerQuartile}%`}}/><span className="quartile median" style={{left:`${benchmark.medianScore}%`}}/><span className="quartile upper" style={{left:`${benchmark.upperQuartile}%`}}/><span className="company-marker" style={{left:`${benchmark.companyScore}%`}}><i>Northstar</i></span></div>
          <div className="benchmark-labels"><span>Weaker</span><span>Stronger</span></div>
        </div>
        <dl className="benchmark-values"><div><dt>Company</dt><dd>{benchmark.companyScore}</dd></div><div><dt>Lower quartile</dt><dd>{benchmark.lowerQuartile ?? "—"}</dd></div><div><dt>Sector median</dt><dd>{benchmark.medianScore ?? "—"}</dd></div><div><dt>Upper quartile</dt><dd>{benchmark.upperQuartile ?? "—"}</dd></div><div><dt>Percentile</dt><dd>{benchmark.companyPercentile}rd</dd></div></dl>
      </div>
      <div className="confidence-panel"><p className="eyebrow">Evidence confidence</p><div><strong>{index.evidenceConfidence.score ?? "—"}</strong><span>/ 100</span></div><h3>{index.evidenceConfidence.label}</h3><p>{index.evidenceConfidence.explanation}</p><small>Evidence strength is separate from operational performance.</small></div>
    </div>
    <details className="methodology-note"><summary>About this rating</summary><div><p>The Northstar rating is a development demonstration, not a validated investment or operational rating.</p><ul><li>Future scores are intended to be calculated from structured operational evidence.</li><li>Operational dimensions are intended to be standardised against relevant peer distributions.</li><li>Weighting should ultimately be derived from validated methodology and predictive evidence.</li><li>Evidence confidence remains separate from operational performance.</li><li>The methodology is currently under development.</li></ul></div></details>
  </section>;
}

export function RatingDrivers({ drivers }: { drivers: RatingDriver[] }) {
  return <section className="drivers-section section"><div className="section-heading"><div><p className="eyebrow">What matters now</p><h2>What is driving the rating?</h2><p>Development-only downside weights show how a future interface could rank attention. They are fixture values, not calculated results.</p></div><span className="development-status">Development weights — not validated</span></div><ol className="driver-list">{drivers.map(driver=><li key={driver.id}><span className="driver-rank">0{driver.rank}</span><div className="driver-name"><h3>{driver.category}</h3><p>{driver.explanation}</p></div><div className="driver-weight"><strong>{driver.downsideWeight}%</strong><span>of downside weighting</span></div><dl><div><dt>Materiality</dt><dd>{driver.materiality}</dd></div><div><dt>Direction</dt><dd>{trendMark(driver.direction)} {driver.direction}</dd></div><div><dt>Evidence</dt><dd>{driver.supportingEvidenceIds.length} observations</dd></div></dl></li>)}</ol></section>;
}

export function DimensionScores({ dimensions }: { dimensions: OperationalDimensionScore[] }) {
  return <section className="dimensions-section section"><div className="section-heading"><div><p className="eyebrow">Operational dimensions</p><h2>Where strength and pressure appear</h2><p>Higher development scores indicate stronger apparent operational health. No dimension has been statistically normalised or validated.</p></div><span className="development-status">Development scale / 100</span></div><div className="dimension-list">{dimensions.map(dimension=><article key={dimension.id}><div className="dimension-heading"><h3>{dimension.category}</h3><span>{dimension.evidenceCount ?? "—"} observations</span></div><div className="dimension-score"><strong>{dimension.score}</strong><div><span style={{width:`${dimension.score}%`}}/></div></div><div className="dimension-meta"><span className={`trend trend-${dimension.trend.toLowerCase()}`}>{trendMark(dimension.trend)} {dimension.trend}</span><span>{dimension.confidence ?? "Unknown"} evidence confidence</span></div><p>{dimension.explanation}</p></article>)}</div></section>;
}

export function FinancialRelevance({ linkages }: { linkages: FinancialLinkage[] }) {
  return <section className="financial-section section"><div className="section-heading"><div><p className="eyebrow">Financial relevance</p><h2>Which financial areas may warrant investigation?</h2><p>These are development-only analytical linkages from operational evidence—not audited conclusions and not claims of causation.</p></div><div><SemanticLabel kind="Interpretation"/><span className="development-status">Development linkage mapping</span></div></div><div className="financial-list">{linkages.map((linkage,index)=><article key={linkage.id}><span className="financial-index">0{index+1}</span><div><h3>{linkage.operationalCategory}</h3><p>{linkage.explanation}</p><footer>{linkage.supportingEvidenceIds.length} supporting observations · {linkage.confidence ?? "Unknown"} confidence</footer></div><div className="financial-areas"><span>Potentially linked financial areas</span>{linkage.financialAreas.map(area=><strong key={area}>{area}</strong>)}</div></article>)}</div></section>;
}

export function InterventionPriorities({ priorities }: { priorities: InterventionPriority[] }) {
  return <section className="interventions-section section"><div className="section-heading"><div><p className="eyebrow">Intervention priorities</p><h2>Where should investigation start?</h2><p>PIOTW identifies intervention classes for further investigation. It does not prescribe unsupported company actions.</p></div><span className="development-status">Development prioritisation</span></div><div className="intervention-list">{priorities.map(priority=><article key={priority.id}><header><span>Priority 0{priority.rank}</span><strong>{priority.priority}</strong></header><h3>{priority.title}</h3><div className="intervention-columns"><div><h4>Why PIOTW cares</h4><ul>{priority.rationale.map(item=><li key={item}>{item}</li>)}</ul></div><div><h4>Intervention classes</h4><ul>{priority.interventionClasses.map(item=><li key={item}>{item}</li>)}</ul></div><div><h4>Potential financial areas</h4><ul>{priority.financialAreas.map(item=><li key={item}>{item}</li>)}</ul></div></div><footer><SemanticLabel kind="Interpretation"/><span>{priority.supportingEvidenceIds.length} supporting observations</span></footer></article>)}</div></section>;
}

export function PredictiveIntelligence() {
  return <section className="predictive-section section"><div><SemanticLabel kind="Prediction"/><p className="eyebrow">Predictive intelligence</p><h2>Validated predictive intelligence is not available for this development dataset.</h2><p>No probability has been inferred or invented. When validated model output exists, this area is intended to show:</p></div><ul><li>Predicted operational event</li><li>Forecast horizon</li><li>Calibrated probability</li><li>Model confidence</li><li>Key contributing features</li><li>Supporting evidence</li></ul></section>;
}
