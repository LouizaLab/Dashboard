import { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { getCompanyTimeseries, compareCompanies, getNetwork } from '../api';

function DetailDrawer({ isOpen, onClose, node, edge, networkData }) {
  const [timeseriesData, setTimeseriesData] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  const [connectedEdges, setConnectedEdges] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState('foot_traffic');
  const [loading, setLoading] = useState(false);
  const [comparingWith, setComparingWith] = useState(null);

  useEffect(() => {
    if (node && isOpen) {
      loadTimeseries();
      loadConnectedEdges();
    }
    if (edge && isOpen) {
      loadEdgeComparison();
    }
  }, [node, edge, selectedMetric, isOpen]);

  const loadConnectedEdges = () => {
    if (!node || !networkData) return;
    const edges = networkData.edges || [];
    // Find edges connected to this node
    const connected = edges.filter(e =>
      e.data.source === String(node.id) || e.data.target === String(node.id)
    );
    setConnectedEdges(connected);
  };

  const loadEdgeComparison = async () => {
    if (!edge) return;
    try {
      setLoading(true);
      const response = await compareCompanies(
        edge.source_company,
        edge.target_company,
        selectedMetric
      );
      setComparisonData(response.data);
    } catch (error) {
      console.error('Failed to load comparison:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCompareWith = async (targetCompanyId, targetCompanyName) => {
    if (!node) return;
    try {
      setLoading(true);
      setComparingWith(targetCompanyName);
      const response = await compareCompanies(node.id, targetCompanyId, selectedMetric);
      setComparisonData(response.data);
    } catch (error) {
      console.error('Failed to load comparison:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTimeseries = async () => {
    if (!node) return;
    try {
      setLoading(true);
      const response = await getCompanyTimeseries(node.id, selectedMetric);
      setTimeseriesData(response.data);
    } catch (error) {
      console.error('Failed to load timeseries:', error);
    } finally {
      setLoading(false);
    }
  };

  const getChartOption = () => {
    if (!timeseriesData || timeseriesData.length === 0) {
      return {
        title: { text: 'No data available', left: 'center', textStyle: { color: '#e0e0e0' } },
      };
    }

    const dates = timeseriesData.map((d) => d.date);
    const quantValues = timeseriesData.map((d) => d.value);

    // Generate behavioral index (synthetic overlay)
    const behavioralValues = quantValues.map((val, idx) => {
      const trend = Math.sin(idx / 10) * 0.1;
      return val * (1 + trend);
    });

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
        data: ['Quant Data', 'Behavioral Index'],
        textStyle: { color: '#e0e0e0' },
        top: 10,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLine: { lineStyle: { color: '#2a2a3a' } },
        axisLabel: { color: '#a0a0a0' },
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: '#2a2a3a' } },
        axisLabel: { color: '#a0a0a0' },
        splitLine: { lineStyle: { color: '#1a1a2a' } },
      },
      series: [
        {
          name: 'Quant Data',
          type: 'line',
          data: quantValues,
          smooth: true,
          lineStyle: { color: '#6366f1', width: 2 },
          itemStyle: { color: '#6366f1' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
                { offset: 1, color: 'rgba(99, 102, 241, 0.05)' },
              ],
            },
          },
        },
        {
          name: 'Behavioral Index',
          type: 'line',
          data: behavioralValues,
          smooth: true,
          lineStyle: { color: '#8b5cf6', width: 2, type: 'dashed' },
          itemStyle: { color: '#8b5cf6' },
        },
      ],
    };
  };

  const getMetricLabel = (metric) => {
    const labels = {
      'foot_traffic': 'Foot Traffic',
      'revenue': 'Revenue ($)',
      'intent_index': 'Intent Index',
      'taste_index': 'Taste Index',
    };
    return labels[metric] || metric;
  };

  const getComparisonChartOption = () => {
    if (!comparisonData || !comparisonData.data || comparisonData.data.length === 0) {
      return {
        title: { text: 'No comparison data', left: 'center', textStyle: { color: '#e0e0e0' } },
      };
    }

    const dates = comparisonData.data.map((d) => d.date);
    const companyAValues = comparisonData.data.map((d) => d.company_a);
    const companyBValues = comparisonData.data.map((d) => d.company_b);

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
        data: [
          comparisonData.company_a?.name || 'Company A',
          comparisonData.company_b?.name || 'Company B',
          ...(comparisonData.edge_metric !== null && comparisonData.edge_metric !== undefined
            ? ['Edge Metric']
            : [])
        ],
        textStyle: { color: '#e0e0e0' },
        top: 10,
      },
      grid: {
        left: '12%',
        right: '6%',
        bottom: '18%',
        top: '18%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLine: { lineStyle: { color: '#2a2a3a' } },
        axisLabel: {
          color: '#a0a0a0',
          rotate: 45,
          interval: 'auto',
        },
      },
      yAxis: {
        type: 'value',
        name: getMetricLabel(selectedMetric),
        nameLocation: 'middle',
        nameGap: 50,
        nameTextStyle: {
          color: '#e0e0e0',
          fontSize: 14,
          fontWeight: 'bold',
        },
        axisLine: { lineStyle: { color: '#2a2a3a' } },
        axisLabel: { color: '#a0a0a0' },
        splitLine: { lineStyle: { color: '#1a1a2a' } },
      },
      series: [
        {
          name: comparisonData.company_a?.name || 'Company A',
          type: 'line',
          data: companyAValues,
          smooth: true,
          lineStyle: { color: '#6366f1', width: 2 },
          itemStyle: { color: '#6366f1' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
                { offset: 1, color: 'rgba(99, 102, 241, 0.05)' },
              ],
            },
          },
        },
        {
          name: comparisonData.company_b?.name || 'Company B',
          type: 'line',
          data: companyBValues,
          smooth: true,
          lineStyle: { color: '#8b5cf6', width: 2 },
          itemStyle: { color: '#8b5cf6' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(139, 92, 246, 0.3)' },
                { offset: 1, color: 'rgba(139, 92, 246, 0.05)' },
              ],
            },
          },
        },
        ...(comparisonData.edge_metric !== null && comparisonData.edge_metric !== undefined ? [{
          name: 'Edge Metric',
          type: 'line',
          data: companyAValues.map((val, idx) => {
            // Show edge metric as a derived line (scaled to fit the chart)
            const avg = (val + companyBValues[idx]) / 2;
            return avg * (comparisonData.edge_metric || 1);
          }),
          smooth: true,
          lineStyle: { color: '#10b981', width: 2, type: 'dashed' },
          itemStyle: { color: '#10b981' },
        }] : []),
      ],
    };
  };

  const renderMatrix = (matrix) => {
    if (!matrix || !Array.isArray(matrix)) return null;

    // Calculate average value for color coding
    const allValues = matrix.flat().filter(v => typeof v === 'number');
    const avgValue = allValues.length > 0 ? allValues.reduce((a, b) => a + b, 0) / allValues.length : 0.5;

    return (
      <div className="mt-4">
        <h4 className="text-sm font-semibold text-gray-400 mb-1">Edge Weight Matrix</h4>
        <p className="text-xs text-gray-500 mb-3">
          Multi-dimensional relationship factors across different contexts (0-1 scale)
        </p>
        <div className="bg-dark-hover rounded-lg p-3 border border-dark-border">
          <div className="grid grid-cols-3 gap-2">
            {matrix.map((row, rowIdx) =>
              row.map((val, colIdx) => {
                const numVal = typeof val === 'number' ? val : 0;
                const intensity = Math.min(255, Math.max(0, Math.round(numVal * 255)));
                const bgOpacity = 0.2 + (numVal * 0.3); // 0.2 to 0.5 opacity based on value

                return (
                  <div
                    key={`${rowIdx}-${colIdx}`}
                    className="bg-gray-700/40 border border-gray-600/50 rounded p-3 text-center relative"
                    style={{
                      backgroundColor: `rgba(156, 163, 175, ${bgOpacity})`,
                    }}
                  >
                    <div className="text-sm font-semibold text-white">
                      {typeof val === 'number' ? val.toFixed(2) : val}
                    </div>
                    {numVal > avgValue && (
                      <div className="absolute top-1 right-1 w-1.5 h-1.5 bg-green-400 rounded-full"></div>
                    )}
                  </div>
                );
              })
            )}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
            <span>Higher values = stronger relationship</span>
            <span>Average: {avgValue.toFixed(2)}</span>
          </div>
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-[800px] bg-dark-surface border-l border-dark-border shadow-2xl z-50 flex flex-col">
      <div className="p-4 border-b border-dark-border flex items-center justify-between">
        <h2 className="text-lg font-bold">
          {node ? node.name : edge ? 'Edge Details' : 'Details'}
        </h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white text-xl"
        >
          ×
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {node && (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-2">Company Info</h3>
              <p className="text-sm text-gray-300">{node.description || 'No description'}</p>
            </div>

            {node.kpis && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">KPIs</h3>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(node.kpis).map(([key, kpi]) => (
                    <div key={key} className="bg-dark-hover rounded p-2">
                      <div className="text-xs text-gray-400">{key.replace('_', ' ')}</div>
                      <div className="text-lg font-bold">{kpi.current?.toFixed(1) || 0}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-2">Time Series</h3>
              <select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value)}
                className="w-full bg-dark-hover border border-dark-border rounded px-3 py-2 text-sm mb-3"
              >
                <option value="foot_traffic">Foot Traffic</option>
                <option value="revenue">Revenue</option>
                <option value="intent_index">Intent Index</option>
                <option value="taste_index">Taste Index</option>
              </select>

              {loading ? (
                <div className="text-center py-8 text-gray-400">Loading...</div>
              ) : (
                <ReactECharts
                  option={getChartOption()}
                  style={{ height: '500px', width: '100%' }}
                />
              )}
            </div>

            {connectedEdges.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">
                  Compare with Connected Companies
                </h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {connectedEdges.map((e, idx) => {
                    const connectedCompanyId = e.data.source === String(node.id)
                      ? e.data.target
                      : e.data.source;
                    // Find the connected company name from nodes
                    const connectedNode = networkData?.nodes?.find(
                      n => String(n.data.id) === String(connectedCompanyId)
                    );
                    const connectedCompanyName = connectedNode?.data?.name || connectedNode?.data?.label || `Company ${connectedCompanyId}`;
                    const edgeWeight = e.data.weight || e.data.edge_weight || 0;

                    return (
                      <button
                        key={idx}
                        onClick={() => handleCompareWith(connectedCompanyId, connectedCompanyName)}
                        className="w-full text-left bg-dark-hover border border-dark-border rounded p-2 hover:border-accent-primary transition-colors"
                      >
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">{connectedCompanyName}</span>
                          <span className="text-xs text-gray-400">
                            Edge: {edgeWeight.toFixed(2)}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {comparisonData && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-gray-400 mb-2">
                  Comparison: {node.name} vs {comparingWith || comparisonData.company_b?.name}
                </h3>
                <div className="overflow-x-auto">
                  <ReactECharts
                    option={getComparisonChartOption()}
                    style={{ height: '550px', minWidth: '1200px', width: '100%' }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {edge && (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-2">Edge Information</h3>
              <div className="bg-dark-hover rounded p-3">
                <div className="text-sm">
                  <span className="text-gray-400">From:</span>{' '}
                  <span className="font-semibold">{edge.source_name}</span>
                </div>
                <div className="text-sm mt-1">
                  <span className="text-gray-400">To:</span>{' '}
                  <span className="font-semibold">{edge.target_name}</span>
                </div>
                <div className="text-sm mt-2">
                  <div className="flex items-baseline gap-2">
                    <span className="text-gray-400">Weight:</span>
                    <span className="font-bold text-accent-primary">{edge.weight?.toFixed(3)}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 ml-0">
                    Overall relationship strength (0-1 scale)
                  </div>
                </div>
              </div>
            </div>

            {edge.top_factors && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-1">Top Factors</h3>
                <p className="text-xs text-gray-500 mb-2">Key metrics driving the relationship</p>
                <div className="space-y-1">
                  {Object.entries(edge.top_factors).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-sm bg-dark-hover rounded px-2 py-1">
                      <span className="text-gray-300">{key.replace('_', ' ')}</span>
                      <span className="font-semibold">
                        {typeof value === 'number' ? value.toFixed(3) : value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {edge && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-gray-400 mb-2">
                  Comparison Chart: {edge.source_name} vs {edge.target_name}
                </h3>
                <div className="relative mb-3">
                  <select
                    value={selectedMetric}
                    onChange={(e) => setSelectedMetric(e.target.value)}
                    className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
                  >
                    <option value="foot_traffic">Foot Traffic</option>
                    <option value="revenue">Revenue</option>
                    <option value="intent_index">Intent Index</option>
                    <option value="taste_index">Taste Index</option>
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
                {loading ? (
                  <div className="text-center py-8 text-gray-400">Loading...</div>
                ) : comparisonData ? (
                  <div className="overflow-x-auto">
                    <ReactECharts
                      option={getComparisonChartOption()}
                      style={{ height: '550px', minWidth: '1200px', width: '100%' }}
                    />
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-400">Loading comparison...</div>
                )}
              </div>
            )}

            {edge.factors_json && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">All Factors</h3>
                <div className="bg-dark-hover rounded p-3 text-xs font-mono max-h-40 overflow-y-auto">
                  <pre className="text-gray-300">
                    {JSON.stringify(edge.factors_json, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default DetailDrawer;
