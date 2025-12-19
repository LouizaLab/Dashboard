import ReactECharts from 'echarts-for-react';

function ResultsPanel({ results, onAgentSelect }) {
  if (!results) return null;

  const aggregated = results.aggregated_result || {};
  const evidence = results.evidence || [];
  const segments = results.segments || [];

  const getSentimentColor = (sentiment) => {
    if (sentiment > 0.6) return '#10b981'; // green
    if (sentiment < 0.4) return '#ef4444'; // red
    return '#f59e0b'; // yellow
  };

  const getChartOption = () => {
    const distribution = aggregated.distribution || {};
    return {
      backgroundColor: 'transparent',
      textStyle: { color: '#e0e0e0' },
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(21, 21, 32, 0.95)',
        borderColor: '#2a2a3a',
        textStyle: { color: '#e0e0e0' },
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: { color: '#e0e0e0' },
      },
      series: [
        {
          type: 'pie',
          radius: '60%',
          data: [
            { value: distribution.positive || 0, name: 'Positive' },
            { value: distribution.neutral || 0, name: 'Neutral' },
            { value: distribution.negative || 0, name: 'Negative' },
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    };
  };

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Summary Outcome</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-gray-400 mb-1">Overall Sentiment</div>
            <div
              className="text-2xl font-bold"
              style={{ color: getSentimentColor(aggregated.overall_sentiment || 0.5) }}
            >
              {(aggregated.overall_sentiment || 0.5).toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-400 mb-1">Confidence</div>
            <div className="text-2xl font-bold text-accent-primary">
              {((aggregated.confidence || 0.6) * 100).toFixed(0)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-400 mb-1">Agents Tested</div>
            <div className="text-2xl font-bold text-gray-200">
              {results.agent_count || 0}
            </div>
          </div>
        </div>
      </div>

      {/* Top Drivers */}
      {aggregated.top_themes && Object.keys(aggregated.top_themes).length > 0 && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Top Drivers</h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(aggregated.top_themes).map(([theme, count]) => (
              <div
                key={theme}
                className="bg-dark-hover border border-dark-border rounded px-3 py-1 text-sm"
              >
                <span className="text-gray-300">{theme}</span>
                <span className="text-accent-primary ml-2">({count})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Segment Differences */}
      {segments.length > 0 && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Segment Differences</h2>
          <div className="space-y-3">
            {segments.map((segment, idx) => (
              <div
                key={idx}
                className="bg-dark-hover border border-dark-border rounded p-3"
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-gray-200">{segment.name}</span>
                  <span className="text-sm text-gray-400">{segment.count} agents</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-dark-bg rounded-full h-2">
                    <div
                      className="h-2 rounded-full"
                      style={{
                        width: `${(segment.sentiment || 0.5) * 100}%`,
                        backgroundColor: getSentimentColor(segment.sentiment || 0.5),
                      }}
                    />
                  </div>
                  <span
                    className="text-sm font-semibold"
                    style={{ color: getSentimentColor(segment.sentiment || 0.5) }}
                  >
                    {(segment.sentiment || 0.5).toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Distribution Chart */}
      {aggregated.distribution && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Response Distribution</h2>
          <ReactECharts
            option={getChartOption()}
            style={{ height: '300px', width: '100%' }}
          />
        </div>
      )}

      {/* Evidence Section */}
      {evidence.length > 0 && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Evidence from Real Surveys</h2>
          <div className="space-y-4">
            {evidence.map((item, idx) => (
              <div
                key={idx}
                className="bg-dark-hover border border-dark-border rounded p-4"
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <div className="text-sm font-medium text-gray-300">{item.dataset_name}</div>
                    <div className="text-xs text-gray-500">{item.region} • {item.date}</div>
                  </div>
                  <div className="text-xs text-gray-500">
                    n={item.metadata?.sample_size || 'N/A'}
                  </div>
                </div>
                <div className="text-sm text-gray-400 mb-2">{item.question}</div>
                <div className="text-sm text-gray-300 italic border-l-2 border-accent-primary pl-3">
                  "{item.snippet}"
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Follow-up */}
      <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Recommended Follow-up Questions</h2>
        <ul className="space-y-2 text-gray-300">
          <li>• How would this change your ordering frequency?</li>
          <li>• What price point would make this most attractive?</li>
          <li>• Which demographic segments show strongest interest?</li>
          <li>• What concerns do you have about this hypothesis?</li>
        </ul>
      </div>

    </div>
  );
}

export default ResultsPanel;

