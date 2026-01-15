import React, { useState, useEffect } from 'react';

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ResultsDisplay error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-full text-red-500 p-8">
          <div className="text-center">
            <div className="text-lg mb-2">Error rendering results</div>
            <div className="text-sm text-gray-400">{this.state.error?.message}</div>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const CASE_TEMPLATES = {
  case1: {
    name: 'Case 1: Food Growth & Whitespace',
    question: 'What are the emerging functional jobs in better-for-you snacks, and where are the whitespace opportunities?',
    subQuestions: [
      'What functional jobs are consumers hiring food for? (mood, focus, sleep, gut health, social moments)',
      'What ingredient/format/ritual recommendations align with these jobs?',
      'How do cohort preferences differ? (Gen Z vs Millennials, fitness-oriented vs time-starved)',
      'Where are the whitespace opportunities in the "jobs × formats" matrix?',
    ],
  },
  case2: {
    name: 'Case 2: Prestige Beauty Portfolio Strategy',
    question: 'What should our prestige beauty portfolio strategy be for the next 3-5 years?',
    subQuestions: [
      'Which categories/subcategories are gaining strategic importance?',
      'How is demand evolving across price tiers? (trade up/down patterns)',
      'How are competitors positioning across category × tier?',
      'What innovation plays are working? (indie vs luxury patterns)',
      'What should we launch, at what tier, and why?',
    ],
  },
  custom: {
    name: 'Custom Question',
    question: '',
    subQuestions: [],
  },
};

function InsightWorkspace({ pinnedNodes = [], onAsk, onScenarioResults, consumerFilters = {} }) {
  const [question, setQuestion] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [vertical, setVertical] = useState('beauty');
  const [scenarioOpen, setScenarioOpen] = useState(false);
  const [scenarioResults, setScenarioResults] = useState(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [scenarioParams, setScenarioParams] = useState({
    price_tier_shift: '',
    channel_shift: '',
    claim_emphasis: '',
    bundle_vs_single: '',
  });

  const handleAsk = async () => {
    if (!question.trim()) return;

    setLoading(true);
    setResults(null); // Clear previous results
    setScenarioResults(null); // Clear scenario results

    try {
      // Call the new /ask endpoint which runs simulation → GPT insight
      const response = await fetch('http://localhost:8000/api/market-insight-new/ask/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          vertical: vertical,
          region: 'US',
          question: question,
          pinned_nodes: pinnedNodes.map(n => n.id),
          filters: consumerFilters || {}, // Use consumer segment filters
          scenario_params: scenarioParams,
          force_gpt: true, // Force GPT API usage instead of cached/mock
        }),
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        try {
          const errorText = await response.text();
          try {
            const errorJson = JSON.parse(errorText);
            errorMessage = errorJson.error || errorJson.detail || errorMessage;
          } catch (e) {
            errorMessage = errorText || errorMessage;
          }
        } catch (e) {
          // If we can't parse the error, use the status
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('Ask response:', data);
      console.log('Consumer filters sent:', consumerFilters);

      // Extract insight (GPT-generated answer)
      // Handle both formats: {insight: {...}} or direct insight object
      let insightData;
      if (data.insight) {
        // New format: {simulation: {...}, insight: {...}}
        insightData = data.insight;
        if (data.simulation) {
          setScenarioResults(data.simulation);
          if (onScenarioResults) {
            onScenarioResults(data.simulation);
          }
        }
      } else {
        // Old format or direct insight
        insightData = data;
      }

      console.log('Setting results with insightData:', insightData);
      setResults(insightData);

      if (onAsk) {
        onAsk(insightData);
      }
    } catch (error) {
      console.error('Failed to ask question:', error);
      setResults({
        title: 'Error',
        executive_summary: [`Failed to generate insight: ${error.message}`],
        direct_answers: {},
        recommended_actions: { now: [], next: [], long_term: [] },
        confidence: { score: 1, entropy: 1.0, rationale: 'Error occurred' },
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRunScenario = async () => {
    if (!question.trim()) {
      alert('Please ask a question first before running scenarios');
      return;
    }

    setScenarioLoading(true);
    try {
      // Run simulation with scenario params
      const response = await fetch('http://localhost:8000/api/market-insight-new/simulate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          vertical: vertical,
          region: 'US',
          question: question,
          pinned_nodes: pinnedNodes.map(n => n.id),
          filters: {},
          scenario_params: scenarioParams,
          force_gpt: true, // Force GPT API usage instead of cached/mock
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setScenarioResults(data);

      if (onScenarioResults) {
        onScenarioResults(data);
      }
    } catch (error) {
      console.error('Failed to run scenario:', error);
    } finally {
      setScenarioLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-dark-bg">
      {/* Header */}
      <div className="p-4 border-b border-dark-border bg-dark-surface">
        <h2 className="text-xl font-bold text-gray-200 mb-4">Insight Workspace</h2>

        {/* Vertical Selector */}
        <div className="mb-4">
          <label className="text-sm text-gray-400 mb-2 block">Vertical</label>
          <div className="relative">
            <select
              className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
              value={vertical}
              onChange={(e) => {
                setVertical(e.target.value);
                setResults(null);
                setScenarioResults(null);
              }}
            >
              <option value="beauty">Beauty</option>
              <option value="food">Food</option>
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Question Input */}
      <div className="p-3 border-b border-dark-border bg-dark-surface">
        <div className="flex items-start gap-2">
          <label className="text-xs text-gray-400 flex-shrink-0 pt-2">Ask:</label>
          <div className="flex-1 flex flex-col gap-2">
            <textarea
              className="w-full bg-dark-bg border border-dark-border rounded px-3 py-2 text-sm text-gray-300 min-h-[50px] max-h-[80px] resize-none"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                  handleAsk();
                }
              }}
              placeholder="What categories should we prioritize?"
            />
            {pinnedNodes.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {pinnedNodes.map((node, index) => (
                  <span
                    key={index}
                    className="px-1.5 py-0.5 bg-purple-900/30 text-purple-300 rounded text-xs"
                  >
                    {node.label}
                  </span>
                ))}
              </div>
            )}
          </div>
          <div className="flex-shrink-0 flex items-start gap-1">
            <button
              onClick={handleAsk}
              disabled={loading || !question.trim()}
              className="bg-gray-600/40 text-white px-3 py-2 rounded-lg hover:bg-gray-500/50 backdrop-blur-sm disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors border border-dark-border"
            >
              {loading ? '...' : 'Ask'}
            </button>
            {question.trim() && (
              <button
                onClick={() => {
                  setQuestion('');
                  setResults(null);
                  setScenarioResults(null);
                }}
                className="px-2 py-2 text-gray-400 hover:text-gray-200 text-sm transition-colors"
                title="Clear"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Scenario Controls */}
      {results && (
        <div className="p-4 border-b border-dark-border bg-dark-surface">
          <button
            onClick={() => setScenarioOpen(!scenarioOpen)}
            className="w-full flex items-center justify-between text-left text-sm font-semibold text-gray-200 hover:text-gray-300 bg-gray-600/40 hover:bg-gray-500/50 backdrop-blur-sm px-3 py-2 rounded-lg border border-dark-border transition-colors"
          >
            <span>Scenario Analysis</span>
            <span>{scenarioOpen ? '▼' : '▶'}</span>
          </button>

          {scenarioOpen && (
            <div className="mt-4 space-y-4">
              {/* Price Tier Shift */}
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Price Tier Shift</label>
                <div className="relative">
                  <select
                    className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
                    value={scenarioParams.price_tier_shift}
                    onChange={(e) => setScenarioParams({ ...scenarioParams, price_tier_shift: e.target.value })}
                  >
                    <option value="">No change</option>
                    <option value="premium">Shift to Premium</option>
                    <option value="super_premium">Shift to Super-Premium</option>
                    <option value="ultra_luxury">Shift to Ultra-Luxury</option>
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Channel Shift */}
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Channel Mix Shift</label>
                <div className="relative">
                  <select
                    className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
                    value={scenarioParams.channel_shift}
                    onChange={(e) => setScenarioParams({ ...scenarioParams, channel_shift: e.target.value })}
                  >
                    <option value="">No change</option>
                    <option value="sephora_heavy">Sephora-Heavy (60%+)</option>
                    <option value="ulta_heavy">Ulta-Heavy (40%+)</option>
                    <option value="dtc_heavy">DTC-Heavy (50%+)</option>
                    <option value="amazon_heavy">Amazon-Heavy (40%+)</option>
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Claim Emphasis */}
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Claim Emphasis</label>
                <div className="relative">
                  <select
                    className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
                    value={scenarioParams.claim_emphasis}
                    onChange={(e) => setScenarioParams({ ...scenarioParams, claim_emphasis: e.target.value })}
                  >
                    <option value="">No change</option>
                    <option value="clean">Clean Beauty</option>
                    <option value="clinical">Clinical/Performance</option>
                    <option value="luxury_heritage">Luxury Heritage</option>
                    <option value="indie_trendy">Indie/Trendy</option>
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Bundle vs Single */}
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Product Strategy</label>
                <div className="relative">
                  <select
                    className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
                    value={scenarioParams.bundle_vs_single}
                    onChange={(e) => setScenarioParams({ ...scenarioParams, bundle_vs_single: e.target.value })}
                  >
                    <option value="">No change</option>
                    <option value="bundle">Focus on Bundles/Kits</option>
                    <option value="single">Focus on Single Hero Products</option>
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              <button
                onClick={handleRunScenario}
                disabled={scenarioLoading}
                className="w-full bg-gray-600/40 text-white px-4 py-2 rounded-lg hover:bg-gray-500/50 backdrop-blur-sm text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors border border-dark-border"
              >
                {scenarioLoading ? 'Running Scenario...' : 'Run Scenario'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="flex-1 overflow-y-auto p-4">
          <ErrorBoundary>
            <ResultsDisplay
              results={results}
              scenarioResults={scenarioResults}
            />
          </ErrorBoundary>
        </div>
      )}

    </div>
  );
}

function ResultsDisplay({ results, scenarioResults }) {
  if (!results) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div>No results to display</div>
      </div>
    );
  }

  // Handle both old format (direct results) and new format (results.insight)
  const insightData = results.insight || results;

  // Safety check - ensure insightData is an object
  if (!insightData || typeof insightData !== 'object') {
    console.error('Invalid insight data:', insightData, 'Full results:', results);
    return (
      <div className="flex items-center justify-center h-full text-red-500 p-8">
        <div className="text-center">
          <div className="text-lg mb-2">Invalid response format</div>
          <div className="text-sm text-gray-400">Received: {typeof insightData}</div>
          <pre className="text-xs mt-4 bg-dark-surface p-2 rounded overflow-auto max-h-40">
            {JSON.stringify(results, null, 2)}
          </pre>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Scenario Results */}
      {scenarioResults && scenarioResults.impacted_clusters && (
        <div className="bg-blue-900/20 rounded-lg p-4 border border-blue-500/30">
          <h3 className="text-lg font-semibold text-blue-300 mb-3">Scenario Impact</h3>

          {/* Impact Summary */}
          {scenarioResults.expected_outcomes && (
            <div className="mb-4 space-y-2">
              <div className="text-sm text-gray-300">
                <span className="text-gray-400">Market Share Change:</span>{' '}
                <span className={scenarioResults.expected_outcomes.market_share_change >= 0 ? 'text-green-400' : 'text-red-400'}>
                  {scenarioResults.expected_outcomes.market_share_change >= 0 ? '+' : ''}
                  {(scenarioResults.expected_outcomes.market_share_change * 100).toFixed(1)}%
                </span>
              </div>
              <div className="text-sm text-gray-300">
                <span className="text-gray-400">Price Sensitivity Impact:</span>{' '}
                <span className={scenarioResults.expected_outcomes.price_sensitivity_impact >= 0 ? 'text-green-400' : 'text-red-400'}>
                  {scenarioResults.expected_outcomes.price_sensitivity_impact >= 0 ? '+' : ''}
                  {(scenarioResults.expected_outcomes.price_sensitivity_impact * 100).toFixed(1)}%
                </span>
              </div>
              <div className="text-sm text-gray-300">
                <span className="text-gray-400">Channel Mix Shift:</span>{' '}
                <span className="text-blue-400">
                  +{(scenarioResults.expected_outcomes.channel_mix_shift * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          )}

          {/* Impacted Clusters */}
          {scenarioResults.impacted_clusters && scenarioResults.impacted_clusters.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-blue-300 mb-2">Impacted Clusters:</h4>
              <div className="flex flex-wrap gap-2">
                {scenarioResults.impacted_clusters.map((cluster, index) => {
                  // Handle both string and object formats
                  const clusterLabel = typeof cluster === 'string'
                    ? cluster
                    : (cluster.cluster_label || cluster.label || `Cluster ${cluster.cluster_id || index}`);
                  const impactScore = typeof cluster === 'object' && cluster.impact_score
                    ? ` (${(cluster.impact_score * 100).toFixed(0)}%)`
                    : '';

                  return (
                    <span
                      key={index}
                      className="px-2 py-1 bg-blue-900/40 text-blue-200 rounded text-xs"
                      title={typeof cluster === 'object' ? JSON.stringify(cluster, null, 2) : ''}
                    >
                      {clusterLabel}{impactScore}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* Scenario Recommendations */}
          {scenarioResults.recommendations && scenarioResults.recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-blue-300 mb-2">Scenario-Specific Recommendations:</h4>
              <ul className="space-y-1">
                {scenarioResults.recommendations.map((rec, index) => (
                  <li key={index} className="text-gray-300 text-sm flex items-start gap-2">
                    <span className="text-blue-400 mt-1">→</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Diffs from Baseline */}
          {scenarioResults.diffs && (
            <div className="mt-4 pt-4 border-t border-blue-500/30">
              <h4 className="text-sm font-semibold text-blue-300 mb-2">Changes from Baseline:</h4>
              {scenarioResults.diffs.recommended_actions && (
                <div className="text-sm text-gray-300">
                  <div className="mb-2">
                    <span className="text-gray-400">Actions Changed:</span>{' '}
                    {scenarioResults.diffs.recommended_actions.changed || 0}
                  </div>
                  {scenarioResults.diffs.recommended_actions.new && scenarioResults.diffs.recommended_actions.new.length > 0 && (
                    <div className="mt-2">
                      <span className="text-green-400">New Actions:</span>
                      <ul className="ml-4 mt-1">
                        {scenarioResults.diffs.recommended_actions.new.map((action, idx) => (
                          <li key={idx} className="text-xs">+ {action}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
      {/* Title */}
      {insightData.title && (
        <div className="text-2xl font-bold text-gray-200">{insightData.title}</div>
      )}

      {/* Executive Summary */}
      {insightData.executive_summary && Array.isArray(insightData.executive_summary) && insightData.executive_summary.length > 0 && (
        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Executive Summary</h3>
          <ul className="space-y-2">
            {insightData.executive_summary.map((item, index) => (
              <li key={index} className="text-gray-300 flex items-start gap-2">
                <span className="text-accent-primary mt-1">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Fallback if no executive summary but we have results */}
      {(!insightData.executive_summary || !Array.isArray(insightData.executive_summary)) && (
        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Analysis Results</h3>
          <pre className="text-sm text-gray-300 overflow-auto max-h-96">
            {JSON.stringify(insightData, null, 2)}
          </pre>
        </div>
      )}

      {/* Direct Answers */}
      {insightData.direct_answers && (
        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Direct Answers</h3>
          <div className="space-y-3">
            {Object.entries(insightData.direct_answers).map(([key, value]) => (
              <div key={key}>
                <h4 className="text-sm font-semibold text-accent-primary mb-1 capitalize">
                  {key.replace(/_/g, ' ')}
                </h4>
                <p className="text-gray-300 text-sm">{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Market Map Takeaways */}
      {insightData.market_map_takeaways && (
        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Market Map Takeaways</h3>

          {insightData.market_map_takeaways.clusters_impacted && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-400 mb-2">Impacted Clusters:</h4>
              <ul className="space-y-1">
                {insightData.market_map_takeaways.clusters_impacted.map((cluster, index) => {
                  // Handle both string and object formats
                  const clusterLabel = typeof cluster === 'string'
                    ? cluster
                    : (cluster.cluster_label || cluster.label || `Cluster ${cluster.cluster_id || index}`);
                  return (
                    <li key={index} className="text-gray-300 text-sm">• {clusterLabel}</li>
                  );
                })}
              </ul>
            </div>
          )}

          {insightData.market_map_takeaways.cluster_relationships && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-400 mb-2">Cluster Relationships:</h4>
              <p className="text-gray-300 text-sm">{insightData.market_map_takeaways.cluster_relationships}</p>
            </div>
          )}

          {insightData.market_map_takeaways.cluster_characteristics && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-400 mb-2">Key Cluster Characteristics:</h4>
              <p className="text-gray-300 text-sm">{insightData.market_map_takeaways.cluster_characteristics}</p>
            </div>
          )}

          {insightData.market_map_takeaways.rationale && (
            <div className="mb-2">
              <h4 className="text-sm font-semibold text-gray-400 mb-2">Strategic Rationale:</h4>
              <p className="text-gray-300 text-sm">{insightData.market_map_takeaways.rationale}</p>
            </div>
          )}
        </div>
      )}

      {/* Recommended Actions */}
      {insightData.recommended_actions && (
        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Recommended Actions</h3>
          <div className="space-y-4">
            {insightData.recommended_actions.now && insightData.recommended_actions.now.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-accent-primary mb-2">Now</h4>
                <ul className="space-y-1">
                  {insightData.recommended_actions.now.map((action, index) => (
                    <li key={index} className="text-gray-300 text-sm">• {action}</li>
                  ))}
                </ul>
              </div>
            )}
            {insightData.recommended_actions.next && insightData.recommended_actions.next.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-yellow-500 mb-2">Next</h4>
                <ul className="space-y-1">
                  {insightData.recommended_actions.next.map((action, index) => (
                    <li key={index} className="text-gray-300 text-sm">• {action}</li>
                  ))}
                </ul>
              </div>
            )}
            {insightData.recommended_actions.long_term && insightData.recommended_actions.long_term.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-blue-500 mb-2">3-5 Years</h4>
                <ul className="space-y-1">
                  {insightData.recommended_actions.long_term.map((action, index) => (
                    <li key={index} className="text-gray-300 text-sm">• {action}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Confidence & Entropy */}
      {insightData.confidence && (
        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Confidence & Entropy</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-400">Confidence:</span>
              <div className="flex-1 bg-dark-bg rounded-full h-2">
                <div
                  className="bg-accent-primary h-2 rounded-full"
                  style={{ width: `${((insightData.confidence.score || 0) / 5) * 100}%` }}
                ></div>
              </div>
              <span className="text-sm text-gray-300">{insightData.confidence.score || 0}/5</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-400">Entropy:</span>
              <div className="flex-1 bg-dark-bg rounded-full h-2">
                <div
                  className="bg-yellow-500 h-2 rounded-full"
                  style={{ width: `${((insightData.confidence.entropy || 0) * 100)}%` }}
                ></div>
              </div>
              <span className="text-sm text-gray-300">{(insightData.confidence.entropy || 0).toFixed(2)}</span>
            </div>
            {insightData.confidence.rationale && (
              <div className="text-sm text-gray-400 mt-3">
                {insightData.confidence.rationale}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Evidence */}
      {insightData.evidence && insightData.evidence.length > 0 && (
        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Evidence</h3>
          <div className="space-y-2">
            {insightData.evidence.slice(0, 10).map((ev, index) => (
              <div
                key={index}
                className="text-sm text-gray-300 p-2 bg-dark-bg rounded cursor-pointer hover:bg-dark-border"
              >
                <span className="text-accent-primary">{ev.type || 'node'}</span>: {ev.label || ev.id}
                {ev.evidence_type === 'synthetic_demo' && (
                  <span className="text-yellow-500 ml-2">(synthetic demo)</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Whitespace Opportunities */}
      {insightData.whitespace_opportunities && Object.keys(insightData.whitespace_opportunities).length > 0 && (
        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Whitespace Opportunities</h3>
          <div className="space-y-3">
            {Object.entries(insightData.whitespace_opportunities).map(([key, opp]) => (
              <div key={key} className="p-3 bg-dark-bg rounded">
                <h4 className="text-sm font-semibold text-accent-primary mb-1">{key.replace(/_/g, ' ')}</h4>
                {typeof opp === 'object' && opp !== null ? (
                  <>
                    {opp.description && (
                      <p className="text-gray-300 text-sm">{opp.description}</p>
                    )}
                    {opp.sizing && (
                      <span className="text-xs text-gray-400">Sizing: {opp.sizing}</span>
                    )}
                    {!opp.description && !opp.sizing && (
                      <pre className="text-xs text-gray-400 overflow-auto">{JSON.stringify(opp, null, 2)}</pre>
                    )}
                  </>
                ) : (
                  <p className="text-gray-300 text-sm">{String(opp)}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Assumptions */}
      {insightData.assumptions && insightData.assumptions.length > 0 && (
        <div className="bg-dark-surface rounded-lg p-4 border border-yellow-500/30">
          <h3 className="text-lg font-semibold text-yellow-400 mb-3">Assumptions</h3>
          <ul className="space-y-2">
            {insightData.assumptions.map((assumption, index) => (
              <li key={index} className="text-gray-300 text-sm flex items-start gap-2">
                <span className="text-yellow-400 mt-1">ℹ</span>
                <span>{assumption}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Risks & Watchouts */}
      {insightData.risks_and_watchouts && insightData.risks_and_watchouts.length > 0 && (
        <div className="bg-dark-surface rounded-lg p-4 border border-red-500/30">
          <h3 className="text-lg font-semibold text-red-400 mb-3">Risks & Watchouts</h3>
          <ul className="space-y-2">
            {insightData.risks_and_watchouts.map((risk, index) => (
              <li key={index} className="text-gray-300 text-sm flex items-start gap-2">
                <span className="text-red-400 mt-1">⚠</span>
                <span>{risk}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Next Questions */}
      {insightData.next_questions && insightData.next_questions.length > 0 && (
        <div className="bg-dark-surface rounded-lg p-4 border border-dark-border">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Next Questions</h3>
          <ul className="space-y-2">
            {insightData.next_questions.map((q, index) => (
              <li key={index} className="text-gray-300 text-sm">• {q}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default InsightWorkspace;
