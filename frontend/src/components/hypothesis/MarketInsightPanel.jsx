import { useState, useEffect } from 'react';
import { Line, Pie, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

function MarketInsightPanel({ filters }) {
  const [insights, setInsights] = useState(null);
  const [graphs, setGraphs] = useState([]);
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMarketInsights();
  }, [filters]);

  const loadMarketInsights = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/market-insight/generate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          days_back: 30,
          limit: 20,
          filters: {
            region: filters.region || null,
            archetype: filters.archetype || null,
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setInsights(data.insights || []);
      setGraphs(data.graphs || []);
      setSummary(data.summary || 'No insights available');
    } catch (error) {
      console.error('Failed to load market insights:', error);
      setSummary('Failed to load market insights. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderGraph = (graph) => {
    if (!graph || !graph.data) return null;

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#e5e7eb'
          }
        },
        title: {
          display: true,
          text: graph.title,
          color: '#e5e7eb',
          font: {
            size: 16,
            weight: 'bold'
          }
        }
      },
      scales: graph.type !== 'pie' ? {
        x: {
          ticks: { color: '#9ca3af' },
          grid: { color: '#374151' }
        },
        y: {
          ticks: { color: '#9ca3af' },
          grid: { color: '#374151' }
        }
      } : {}
    };

    switch (graph.type) {
      case 'line':
        return (
          <div key={graph.title} className="bg-dark-surface rounded-lg p-6 mb-6">
            <div style={{ height: '300px' }}>
              <Line data={graph.data} options={chartOptions} />
            </div>
          </div>
        );
      case 'pie':
        return (
          <div key={graph.title} className="bg-dark-surface rounded-lg p-6 mb-6">
            <div style={{ height: '300px' }}>
              <Pie data={graph.data} options={chartOptions} />
            </div>
          </div>
        );
      case 'bar':
        return (
          <div key={graph.title} className="bg-dark-surface rounded-lg p-6 mb-6">
            <div style={{ height: '300px' }}>
              <Bar data={graph.data} options={chartOptions} />
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <div className="text-accent-primary text-xl mb-4">Loading Market Insights...</div>
          <div className="text-gray-400">Analyzing consultant questions...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-7xl mx-auto">
        {/* Summary Section */}
        <div className="bg-dark-surface rounded-lg p-6 mb-6 border border-dark-border">
          <h2 className="text-2xl font-bold text-gray-200 mb-4">Market Insight Summary</h2>
          <div className="text-gray-300 whitespace-pre-line">{summary}</div>
        </div>

        {/* Insights Cards */}
        {insights && insights.length > 0 && (
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-200 mb-4">Key Insights</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {insights.map((insight, index) => (
                <div key={index} className="bg-dark-surface rounded-lg p-4 border border-dark-border">
                  <div className="text-sm font-semibold text-accent-primary mb-2 uppercase">
                    {insight.category || 'General'}
                  </div>
                  <div className="text-gray-300 mb-2">
                    {insight.question_count} questions analyzed
                  </div>
                  {insight.average_sentiment !== undefined && (
                    <div className="text-sm text-gray-400 mb-2">
                      Avg Sentiment: {insight.average_sentiment}
                    </div>
                  )}
                  {insight.top_themes && insight.top_themes.length > 0 && (
                    <div className="mt-2">
                      <div className="text-xs text-gray-400 mb-1">Top Themes:</div>
                      {insight.top_themes.slice(0, 3).map((theme, i) => (
                        <div key={i} className="text-sm text-gray-300">
                          • {theme.theme} ({theme.mentions} mentions)
                        </div>
                      ))}
                    </div>
                  )}
                  {insight.key_findings && insight.key_findings.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-dark-border">
                      <div className="text-xs text-gray-400 mb-1">Key Findings:</div>
                      {insight.key_findings.map((finding, i) => (
                        <div key={i} className="text-sm text-gray-300">
                          • {finding}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Graphs Section */}
        {graphs && graphs.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold text-gray-200 mb-4">Visualizations</h2>
            <div className="space-y-6">
              {graphs.map((graph, index) => (
                <div key={index}>
                  {renderGraph(graph)}
                </div>
              ))}
            </div>
          </div>
        )}

        {(!insights || insights.length === 0) && (!graphs || graphs.length === 0) && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-lg mb-2">No insights available</div>
            <div className="text-gray-500 text-sm">
              Run some hypothesis tests to generate market insights
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MarketInsightPanel;

