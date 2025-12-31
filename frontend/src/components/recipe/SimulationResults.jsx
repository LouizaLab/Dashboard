import { useState } from 'react';
import ReactECharts from 'echarts-for-react';

function SimulationResults({ results }) {
  const [activeTab, setActiveTab] = useState('overview');

  if (!results || !results.results_json) {
    return (
      <div className="text-center text-gray-400 py-8">
        No results available yet. Please wait for simulation to complete.
      </div>
    );
  }

  const timeSeries = results.results_json?.time_series || [];
  const segmentBreakdown = results.results_json?.segment_breakdown || {};
  const overallAcceptance = results.results_json?.overall_acceptance_rate || 0;
  const meanPreferenceDelta = results.results_json?.mean_preference_delta || 0;
  
  // Get simulator type from metadata or results
  const simulatorType = results.metadata_json?.simulator_type || results.results_json?.simulator_type || 'unknown';
  const simulatorMessage = results.metadata_json?.simulator_message || results.results_json?.simulator_message || '';
  const isPhase34 = simulatorType === 'phase34';

  // Time Series Chart
  const getTimeSeriesChartOption = () => {
    if (timeSeries.length === 0) return null;

    const weeks = timeSeries.map(w => `W${w.week}`);
    const acceptanceRates = timeSeries.map(w => (w.acceptance_rate * 100).toFixed(1));
    const rejectionRates = timeSeries.map(w => (w.rejection_rate * 100).toFixed(1));
    const substitutionRates = timeSeries.map(w => (w.substitution_rate * 100).toFixed(1));
    const meanPreferences = timeSeries.map(w => (w.mean_preference * 100).toFixed(1));

    return {
      backgroundColor: 'transparent',
      textStyle: { color: '#e0e0e0' },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(21, 21, 32, 0.95)',
        borderColor: '#2a2a3a',
        textStyle: { color: '#e0e0e0' },
      },
      legend: {
        data: ['Acceptance', 'Rejection', 'Substitution', 'Mean Preference'],
        textStyle: { color: '#e0e0e0' },
        top: 10,
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '15%',
        top: '20%'
      },
      xAxis: {
        type: 'category',
        data: weeks,
        axisLine: { lineStyle: { color: '#2a2a3a' } },
        axisLabel: { color: '#a0a0a0', fontSize: 10 },
      },
      yAxis: [
        {
          type: 'value',
          name: 'Rate (%)',
          position: 'left',
          axisLine: { lineStyle: { color: '#2a2a3a' } },
          axisLabel: { color: '#a0a0a0', formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#1a1a2a' } },
        },
        {
          type: 'value',
          name: 'Preference',
          position: 'right',
          axisLine: { lineStyle: { color: '#2a2a3a' } },
          axisLabel: { color: '#a0a0a0', formatter: '{value}%' },
          splitLine: { show: false },
        }
      ],
      series: [
        {
          name: 'Acceptance',
          type: 'line',
          data: acceptanceRates,
          smooth: true,
          lineStyle: { color: '#10b981', width: 3 },
          itemStyle: { color: '#10b981' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
                { offset: 1, color: 'rgba(16, 185, 129, 0.05)' },
              ],
            },
          },
        },
        {
          name: 'Rejection',
          type: 'line',
          data: rejectionRates,
          smooth: true,
          lineStyle: { color: '#ef4444', width: 2 },
          itemStyle: { color: '#ef4444' },
        },
        {
          name: 'Substitution',
          type: 'line',
          data: substitutionRates,
          smooth: true,
          lineStyle: { color: '#f59e0b', width: 2 },
          itemStyle: { color: '#f59e0b' },
        },
        {
          name: 'Mean Preference',
          type: 'line',
          yAxisIndex: 1,
          data: meanPreferences,
          smooth: true,
          lineStyle: { color: '#6366f1', width: 2, type: 'dashed' },
          itemStyle: { color: '#6366f1' },
        }
      ]
    };
  };

  // Segment Breakdown Chart
  const getSegmentChartOption = () => {
    const segments = Object.entries(segmentBreakdown);
    if (segments.length === 0) return null;

    const data = segments.map(([key, data]) => ({
      value: data.count,
      name: key.replace('_', ' - ').substring(0, 25),
      acceptanceRate: data.actions?.accept || 0
    }));

    return {
      backgroundColor: 'transparent',
      textStyle: { color: '#e0e0e0' },
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(21, 21, 32, 0.95)',
        borderColor: '#2a2a3a',
        textStyle: { color: '#e0e0e0' },
        formatter: (params) => {
          const segment = data.find(d => d.name === params.name);
          return `${params.name}<br/>Agents: ${params.value}<br/>Acceptance: ${(segment?.acceptanceRate * 100 || 0).toFixed(1)}%`;
        }
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center',
        textStyle: { color: '#a0a0a0', fontSize: 10 },
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#1a1a2e',
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: '{b}\n{c}',
            color: '#e0e0e0',
            fontSize: 10,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 12,
              fontWeight: 'bold',
            },
          },
          data: data,
        }
      ]
    };
  };

  // Action Distribution Chart
  const getActionChartOption = () => {
    const actions = results.results_json?.actions || {};
    const actionCounts = {
      accept: 0,
      reject: 0,
      substitute: 0,
      reduce_frequency: 0,
      increase_frequency: 0
    };

    Object.values(actions).forEach(action => {
      if (actionCounts.hasOwnProperty(action)) {
        actionCounts[action]++;
      }
    });

    const total = Object.values(actionCounts).reduce((a, b) => a + b, 0);
    if (total === 0) return null;

    const data = Object.entries(actionCounts)
      .filter(([_, count]) => count > 0)
      .map(([action, count]) => ({
        value: (count / total * 100).toFixed(1),
        name: action.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
      }));

    return {
      backgroundColor: 'transparent',
      textStyle: { color: '#e0e0e0' },
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(21, 21, 32, 0.95)',
        borderColor: '#2a2a3a',
        textStyle: { color: '#e0e0e0' },
        formatter: '{b}: {c}% ({d}%)'
      },
      legend: {
        orient: 'horizontal',
        bottom: 10,
        textStyle: { color: '#e0e0e0', fontSize: 10 },
      },
      series: [
        {
          type: 'pie',
          radius: '60%',
          center: ['50%', '45%'],
          data: data,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#1a1a2e',
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: '{b}\n{c}%',
            color: '#e0e0e0',
            fontSize: 11,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    };
  };

  return (
    <div className="space-y-6">
      {/* Simulator Type Banner */}
      {simulatorMessage && (
        <div className={`p-3 rounded-lg border ${
          simulatorType === 'phase34' 
            ? 'bg-green-900/20 border-green-700 text-green-300' 
            : 'bg-yellow-900/20 border-yellow-700 text-yellow-300'
        }`}>
          <div className="flex items-center gap-2">
            <span className="font-semibold">
              {simulatorType === 'phase34' ? '✓' : '⚠'}
            </span>
            <span className="text-sm">{simulatorMessage}</span>
          </div>
        </div>
      )}
      
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-dark-surface p-4 rounded-lg border border-dark-border">
          <div className="text-sm text-gray-400 mb-1">Acceptance Rate</div>
          <div className="text-3xl font-bold">
            {(overallAcceptance * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500 mt-1">LPM Population</div>
        </div>
        <div className="bg-dark-surface p-4 rounded-lg border border-dark-border">
          <div className="text-sm text-gray-400 mb-1">Preference Delta</div>
          <div className={`text-3xl font-bold ${meanPreferenceDelta >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {meanPreferenceDelta >= 0 ? '+' : ''}{meanPreferenceDelta.toFixed(3)}
          </div>
          <div className="text-xs text-gray-500 mt-1">Mean Change</div>
        </div>
        <div className="bg-dark-surface p-4 rounded-lg border border-dark-border">
          <div className="text-sm text-gray-400 mb-1">Confidence</div>
          <div className="text-3xl font-bold">
            {((results.confidence_score || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500 mt-1">Decision Clarity</div>
        </div>
        <div className="bg-dark-surface p-4 rounded-lg border border-dark-border">
          <div className="text-sm text-gray-400 mb-1">Entropy Delta</div>
          <div className={`text-3xl font-bold ${(results.entropy_delta || 0) < 0 ? 'text-green-400' : 'text-yellow-400'}`}>
            {(results.entropy_delta || 0).toFixed(3)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {(results.entropy_delta || 0) < 0 ? 'Increased Clarity' : 'More Uncertainty'}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-dark-border">
        {['overview', 'time-series', 'segments', 'actions'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium transition-all ${
              activeTab === tab
                ? 'border-b-2 border-accent-primary text-accent-primary'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {tab.replace('-', ' ').toUpperCase()}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-4">
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <div className="bg-dark-surface p-4 rounded-lg border border-dark-border">
              <h3 className="font-semibold mb-4">Overall Metrics</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Acceptance Rate:</span>
                  <span className="ml-2 font-semibold">{(overallAcceptance * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-gray-400">Rejection Rate:</span>
                  <span className="ml-2 font-semibold">
                    {((results.results_json?.overall_rejection_rate || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Mean Preference Delta:</span>
                  <span className={`ml-2 font-semibold ${meanPreferenceDelta >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {meanPreferenceDelta >= 0 ? '+' : ''}{meanPreferenceDelta.toFixed(3)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Confidence Score:</span>
                  <span className="ml-2 font-semibold">
                    {((results.confidence_score || 0) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {getTimeSeriesChartOption() && (
              <div className="bg-dark-surface p-4 rounded-lg border border-dark-border">
                <h3 className="font-semibold mb-4">Time Series Preview</h3>
                <ReactECharts
                  option={getTimeSeriesChartOption()}
                  style={{ height: '300px', width: '100%' }}
                  opts={{ renderer: 'svg' }}
                />
              </div>
            )}
          </div>
        )}

        {activeTab === 'time-series' && (
          <div className="bg-dark-surface p-4 rounded-lg border border-dark-border">
            <h3 className="font-semibold mb-4">Preference Evolution Over Time (LPM)</h3>
            {getTimeSeriesChartOption() ? (
              <ReactECharts
                option={getTimeSeriesChartOption()}
                style={{ height: '400px', width: '100%' }}
                opts={{ renderer: 'svg' }}
              />
            ) : (
              <div className="text-gray-400 text-sm">No time series data available</div>
            )}
          </div>
        )}

        {activeTab === 'segments' && (
          <div className="space-y-4">
            {getSegmentChartOption() && (
              <div className="bg-dark-surface p-4 rounded-lg border border-dark-border">
                <h3 className="font-semibold mb-4">Segment Distribution</h3>
                <ReactECharts
                  option={getSegmentChartOption()}
                  style={{ height: '350px', width: '100%' }}
                  opts={{ renderer: 'svg' }}
                />
              </div>
            )}
            
            <div className="space-y-3">
              {Object.entries(segmentBreakdown).map(([segmentKey, segmentData]) => (
                <div
                  key={segmentKey}
                  className="bg-dark-surface p-4 rounded-lg border border-dark-border"
                >
                  <div className="font-medium mb-2">{segmentKey.replace('_', ' - ')}</div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Count:</span>
                      <span className="ml-2 font-semibold">{segmentData.count}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Preference Delta:</span>
                      <span className={`ml-2 font-semibold ${segmentData.mean_preference_delta >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {segmentData.mean_preference_delta >= 0 ? '+' : ''}
                        {segmentData.mean_preference_delta.toFixed(3)}
                      </span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-400">Actions:</span>
                      <div className="mt-1 flex flex-wrap gap-3 text-xs">
                        {Object.entries(segmentData.actions || {}).map(([action, rate]) => (
                          <span key={action} className="flex items-center gap-1">
                            <span className="capitalize">{action}:</span>
                            <span className="font-semibold">{(rate * 100).toFixed(1)}%</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'actions' && (
          <div className="space-y-4">
            {getActionChartOption() && (
              <div className="bg-dark-surface p-4 rounded-lg border border-dark-border">
                <h3 className="font-semibold mb-4">Action Distribution</h3>
                <ReactECharts
                  option={getActionChartOption()}
                  style={{ height: '350px', width: '100%' }}
                  opts={{ renderer: 'svg' }}
                />
              </div>
            )}
            
            <div className="bg-dark-surface p-4 rounded-lg border border-dark-border">
              <h3 className="font-semibold mb-4">Agent Decisions (Sample)</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {Object.entries(results.results_json?.actions || {}).slice(0, 100).map(([agentId, action]) => (
                  <div key={agentId} className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">{agentId.substring(0, 12)}...</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      action === 'accept' ? 'bg-green-500/20 text-green-400' :
                      action === 'reject' ? 'bg-red-500/20 text-red-400' :
                      action === 'substitute' ? 'bg-yellow-500/20 text-yellow-400' :
                      action === 'reduce_frequency' ? 'bg-orange-500/20 text-orange-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {action.replace('_', ' ')}
                    </span>
                  </div>
                ))}
                {(Object.keys(results.results_json?.actions || {}).length > 100) && (
                  <div className="text-xs text-gray-400 text-center mt-2">
                    Showing first 100 of {Object.keys(results.results_json?.actions || {}).length} agents
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SimulationResults;
