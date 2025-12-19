import ReactECharts from 'echarts-for-react';

function ResultsPanel({ results, onAgentSelect }) {
  if (!results) return null;

  const aggregated = results.aggregated_result || {};
  const evidence = results.evidence || [];
  const segments = results.segments || [];
  const gptReport = results.gpt_report || aggregated;

  const getSentimentColor = (sentiment) => {
    if (sentiment > 0.6) return '#10b981'; // green
    if (sentiment < 0.4) return '#ef4444'; // red
    return '#f59e0b'; // yellow
  };

  // Preference breakdown chart (for brand comparisons)
  const getPreferenceChartOption = () => {
    const preferenceBreakdown = gptReport.preference_breakdown || {};
    const brands = Object.keys(preferenceBreakdown);
    
    if (brands.length === 0) return null;

    const data = brands.map(brand => ({
      value: preferenceBreakdown[brand].percentage || 0,
      name: brand.charAt(0).toUpperCase() + brand.slice(1).replace(/_/g, ' '),
    }));

    return {
      backgroundColor: 'transparent',
      textStyle: { color: '#e0e0e0' },
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(21, 21, 32, 0.95)',
        borderColor: '#2a2a3a',
        textStyle: { color: '#e0e0e0' },
        formatter: '{b}: {c}% ({d}%)',
      },
      legend: {
        orient: 'horizontal',
        bottom: 'bottom',
        textStyle: { color: '#e0e0e0' },
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#1a1a2e',
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: '{b}\n{c}%',
            color: '#e0e0e0',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
            },
          },
          data: data,
        },
      ],
    };
  };

  // Segment insights chart
  const getSegmentChartOption = () => {
    const segmentInsights = gptReport.segment_insights || {};
    const archetypeData = segmentInsights.archetype || {};
    
    if (Object.keys(archetypeData).length === 0) return null;

    const categories = Object.keys(archetypeData);
    const percentages = categories.map(key => archetypeData[key].percentage || 0);

    return {
      backgroundColor: 'transparent',
      textStyle: { color: '#e0e0e0' },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(21, 21, 32, 0.95)',
        borderColor: '#2a2a3a',
        textStyle: { color: '#e0e0e0' },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: categories.map(k => k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())),
        axisLabel: { color: '#9ca3af', rotate: 45 },
        axisLine: { lineStyle: { color: '#374151' } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#9ca3af', formatter: '{value}%' },
        axisLine: { lineStyle: { color: '#374151' } },
        splitLine: { lineStyle: { color: '#374151', type: 'dashed' } },
      },
      series: [
        {
          name: 'Preference %',
          type: 'bar',
          data: percentages,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#8b5cf6' },
                { offset: 1, color: '#6366f1' },
              ],
            },
          },
          label: {
            show: true,
            position: 'top',
            color: '#e0e0e0',
            formatter: '{c}%',
          },
        },
      ],
    };
  };

  // Distribution chart (fallback)
  const getDistributionChartOption = () => {
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
      {/* Executive Summary - Larger and more prominent */}
      {gptReport.executive_summary && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4 text-gray-100">Executive Summary</h2>
          <div className="prose prose-invert max-w-none">
            <p className="text-gray-300 leading-relaxed whitespace-pre-line text-base">
              {gptReport.executive_summary}
            </p>
          </div>
        </div>
      )}

      {/* Summary Outcome */}
      <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Summary Outcome</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-gray-400 mb-1">Overall Sentiment</div>
            <div
              className="text-2xl font-bold"
              style={{ color: getSentimentColor(gptReport.overall_sentiment || aggregated.overall_sentiment || 0.5) }}
            >
              {(gptReport.overall_sentiment || aggregated.overall_sentiment || 0.5).toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-400 mb-1">Confidence</div>
            <div className="text-2xl font-bold text-accent-primary">
              {((gptReport.confidence || aggregated.confidence || 0.6) * 100).toFixed(0)}%
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

      {/* Preference Breakdown Chart */}
      {gptReport.preference_breakdown && Object.keys(gptReport.preference_breakdown).length > 0 && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Preference Breakdown</h2>
          <ReactECharts
            option={getPreferenceChartOption()}
            style={{ height: '400px', width: '100%' }}
          />
          <div className="mt-4 space-y-2">
            {Object.entries(gptReport.preference_breakdown).map(([brand, data]) => (
              <div key={brand} className="bg-dark-hover border border-dark-border rounded p-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-gray-200 capitalize">
                    {brand.replace(/_/g, ' ')}
                  </span>
                  <span className="text-lg font-bold text-accent-primary">
                    {data.percentage}%
                  </span>
                </div>
                {data.reasons && data.reasons.length > 0 && (
                  <div className="text-sm text-gray-400">
                    <span className="font-medium">Key Reasons:</span>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                      {data.reasons.map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key Findings */}
      {gptReport.key_findings && gptReport.key_findings.length > 0 && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Key Findings</h2>
          <ul className="space-y-3">
            {gptReport.key_findings.map((finding, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="text-accent-primary font-bold mt-1">•</span>
                <span className="text-gray-300 flex-1">{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Top Drivers */}
      {(gptReport.top_drivers || aggregated.top_themes) && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Top Drivers</h2>
          <div className="flex flex-wrap gap-2">
            {(gptReport.top_drivers || Object.entries(aggregated.top_themes || {})).map((item, idx) => {
              const theme = typeof item === 'string' ? item : item.theme || item[0];
              const count = typeof item === 'string' ? aggregated.top_themes[item] : item.mentions || item[1];
              return (
                <div
                  key={idx}
                  className="bg-dark-hover border border-dark-border rounded px-3 py-1 text-sm"
                >
                  <span className="text-gray-300 capitalize">{theme.replace(/_/g, ' ')}</span>
                  <span className="text-accent-primary ml-2">({count})</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Segment Insights Chart */}
      {gptReport.segment_insights && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Segment Insights</h2>
          {getSegmentChartOption() && (
            <ReactECharts
              option={getSegmentChartOption()}
              style={{ height: '400px', width: '100%' }}
            />
          )}
          <div className="mt-4 space-y-3">
            {gptReport.segment_insights.archetype && Object.entries(gptReport.segment_insights.archetype).map(([archetype, data]) => (
              <div key={archetype} className="bg-dark-hover border border-dark-border rounded p-3">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-medium text-gray-200 capitalize">
                    {archetype.replace(/_/g, ' ')}
                  </span>
                  <span className="text-sm text-accent-primary">
                    {data.preference && `${data.preference.replace(/_/g, ' ')}: ${data.percentage}%`}
                  </span>
                </div>
                {data.insight && (
                  <p className="text-sm text-gray-400 mt-1">{data.insight}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Segment Differences (fallback) */}
      {segments.length > 0 && !gptReport.segment_insights && (
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

      {/* Distribution Chart (fallback) */}
      {aggregated.distribution && !gptReport.preference_breakdown && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Response Distribution</h2>
          <ReactECharts
            option={getDistributionChartOption()}
            style={{ height: '300px', width: '100%' }}
          />
        </div>
      )}

      {/* Recommendations */}
      {gptReport.recommendations && gptReport.recommendations.length > 0 && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Recommendations</h2>
          <ul className="space-y-2 text-gray-300">
            {gptReport.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="text-accent-primary font-bold mt-1">•</span>
                <span className="flex-1">{rec}</span>
              </li>
            ))}
          </ul>
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
    </div>
  );
}

export default ResultsPanel;
