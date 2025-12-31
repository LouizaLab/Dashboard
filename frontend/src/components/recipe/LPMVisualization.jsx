import ReactECharts from 'echarts-for-react';
import { useState, useEffect, useMemo } from 'react';

function LPMVisualization({ simulationResults, recipeVariant }) {
  const [selectedCondition, setSelectedCondition] = useState('baseline');
  const [animationSpeed, setAnimationSpeed] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentWeek, setCurrentWeek] = useState(0);

  // Extract Phase 3-4 LPM data
  const timeSeries = simulationResults?.results_json?.time_series || [];
  const segmentBreakdown = simulationResults?.results_json?.segment_breakdown || {};
  const actions = simulationResults?.results_json?.actions || {};
  const baselinePreferences = simulationResults?.results_json?.baseline_preferences || {};
  const preferenceDeltas = simulationResults?.results_json?.preference_deltas || {};
  const finalPreferences = simulationResults?.results_json?.final_preferences || {};
  
  // Check if using Phase 3-4 models
  const simulatorType = simulationResults?.metadata_json?.simulator_type || simulationResults?.results_json?.simulator_type || 'unknown';
  const isPhase34 = simulatorType === 'phase34';

  // Animation effect
  useEffect(() => {
    if (isPlaying && timeSeries.length > 0) {
      const interval = setInterval(() => {
        setCurrentWeek((prev) => {
          if (prev >= timeSeries.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1000 / animationSpeed);
      return () => clearInterval(interval);
    }
  }, [isPlaying, animationSpeed, timeSeries.length]);

  // Population Network Graph
  const getNetworkGraph = () => {
    const segments = Object.keys(segmentBreakdown);
    if (segments.length === 0) {
      return {
        backgroundColor: 'transparent',
        textStyle: { color: '#e0e0e0' },
        title: {
          text: 'No Segment Data',
          left: 'center',
          top: 'center',
          textStyle: { color: '#a0a0a0', fontSize: 12 }
        }
      };
    }

    // Create nodes for each segment
    const nodes = segments.map((segment, idx) => {
      const data = segmentBreakdown[segment];
      const acceptanceRate = data.actions?.accept || 0;
      const angle = (idx * 2 * Math.PI) / segments.length;
      const radius = 0.4;
      
      return {
        id: segment,
        name: segment.substring(0, 15),
        value: data.count || 0,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        symbolSize: Math.max(20, Math.min(60, (data.count || 0) / 10)),
        itemStyle: {
          color: acceptanceRate >= 0.7 ? '#10b981' : acceptanceRate >= 0.4 ? '#f59e0b' : '#ef4444'
        },
        label: {
          show: true,
          fontSize: 9,
          color: '#e0e0e0'
        }
      };
    });

    // Create edges (connections between segments)
    const edges = [];
    for (let i = 0; i < segments.length; i++) {
      for (let j = i + 1; j < segments.length; j++) {
        const seg1 = segmentBreakdown[segments[i]];
        const seg2 = segmentBreakdown[segments[j]];
        // Connect segments with similar acceptance rates
        const similarity = 1 - Math.abs((seg1.actions?.accept || 0) - (seg2.actions?.accept || 0));
        if (similarity > 0.3) {
          edges.push({
            source: segments[i],
            target: segments[j],
            value: similarity,
            lineStyle: {
              width: similarity * 3,
              color: '#6366f1',
              opacity: 0.3
            }
          });
        }
      }
    }

    return {
      backgroundColor: 'transparent',
      textStyle: { color: '#e0e0e0' },
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(21, 21, 32, 0.95)',
        borderColor: '#2a2a3a',
        textStyle: { color: '#e0e0e0' },
        formatter: (params) => {
          if (params.dataType === 'node') {
            const data = segmentBreakdown[params.data.id];
            return `${params.data.name}<br/>Agents: ${params.data.value}<br/>Acceptance: ${((data.actions?.accept || 0) * 100).toFixed(1)}%`;
          }
          return `${params.data.source} ↔ ${params.data.target}`;
        }
      },
      series: [{
        type: 'graph',
        layout: 'force',
        roam: true,
        label: {
          show: true,
          position: 'right',
          fontSize: 9,
          color: '#e0e0e0'
        },
        edgeLabel: {
          show: false
        },
        force: {
          repulsion: 300,
          gravity: 0.1,
          edgeLength: 100,
          layoutAnimation: true
        },
        data: nodes,
        links: edges,
        lineStyle: {
          color: '#6366f1',
          opacity: 0.3,
          curveness: 0.3
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 4
          }
        }
      }]
    };
  };

  // Population Heatmap
  const getPopulationHeatmap = () => {
    const segments = Object.entries(segmentBreakdown);
    if (segments.length === 0) {
      return {
        backgroundColor: 'transparent',
        textStyle: { color: '#e0e0e0' },
        title: {
          text: 'No Data',
          left: 'center',
          top: 'center',
          textStyle: { color: '#a0a0a0', fontSize: 12 }
        }
      };
    }

    const segmentNames = segments.map(([key]) => key.substring(0, 12));
    const weeks = timeSeries.length > 0 
      ? timeSeries.map(w => `W${w.week || w.week_number || 0}`)
      : ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12'];

    // Create heatmap data
    const data = [];
    segments.forEach(([segmentKey, segmentData], segIdx) => {
      weeks.forEach((week, weekIdx) => {
        const weekData = timeSeries[weekIdx];
        if (weekData) {
          const acceptanceRate = weekData.acceptance_rate || 0;
          data.push([weekIdx, segIdx, (acceptanceRate * 100).toFixed(1)]);
        } else {
          data.push([weekIdx, segIdx, 0]);
        }
      });
    });

    return {
      backgroundColor: 'transparent',
      textStyle: { color: '#e0e0e0' },
      tooltip: {
        position: 'top',
        backgroundColor: 'rgba(21, 21, 32, 0.95)',
        borderColor: '#2a2a3a',
        textStyle: { color: '#e0e0e0' },
        formatter: (params) => {
          return `${segmentNames[params.data[1]]}<br/>${weeks[params.data[0]]}: ${params.data[2]}%`;
        }
      },
      grid: {
        height: '60%',
        top: '15%',
        left: '15%'
      },
      xAxis: {
        type: 'category',
        data: weeks,
        splitArea: { show: true },
        axisLine: { lineStyle: { color: '#2a2a3a' } },
        axisLabel: { color: '#a0a0a0', fontSize: 8, rotate: 45 }
      },
      yAxis: {
        type: 'category',
        data: segmentNames,
        splitArea: { show: true },
        axisLine: { lineStyle: { color: '#2a2a3a' } },
        axisLabel: { color: '#a0a0a0', fontSize: 8 }
      },
      visualMap: {
        min: 0,
        max: 100,
        calculable: true,
        orient: 'vertical',
        left: 'right',
        top: 'center',
        inRange: {
          color: ['#ef4444', '#f59e0b', '#10b981']
        },
        textStyle: { color: '#e0e0e0', fontSize: 9 }
      },
      series: [{
        name: 'Acceptance Rate',
        type: 'heatmap',
        data: data,
        label: {
          show: false
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    };
  };

  // Agent State Distribution
  const getAgentStateChart = () => {
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
    if (total === 0) {
      return {
        backgroundColor: 'transparent',
        textStyle: { color: '#e0e0e0' },
        title: {
          text: 'No Data',
          left: 'center',
          top: 'center',
          textStyle: { color: '#a0a0a0', fontSize: 12 }
        }
      };
    }

    const data = Object.entries(actionCounts)
      .filter(([_, count]) => count > 0)
      .map(([action, count]) => ({
        value: count,
        name: action.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        itemStyle: {
          color: action === 'accept' ? '#10b981' :
                 action === 'reject' ? '#ef4444' :
                 action === 'substitute' ? '#f59e0b' :
                 action === 'reduce_frequency' ? '#f97316' : '#6366f1'
        }
      }));

    return {
      backgroundColor: 'transparent',
      textStyle: { color: '#e0e0e0' },
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(21, 21, 32, 0.95)',
        borderColor: '#2a2a3a',
        textStyle: { color: '#e0e0e0' },
        formatter: '{b}: {c} agents ({d}%)'
      },
      legend: {
        orient: 'horizontal',
        bottom: 2,
        textStyle: { color: '#e0e0e0', fontSize: 9 }
      },
      series: [{
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['50%', '40%'],
        data: data,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#1a1a2e',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{c}',
          color: '#e0e0e0',
          fontSize: 9
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    };
  };

  // Preference Evolution Animation
  const getPreferenceEvolution = () => {
    if (timeSeries.length === 0) {
      return {
        backgroundColor: 'transparent',
        textStyle: { color: '#e0e0e0' },
        title: {
          text: 'No Data',
          left: 'center',
          top: 'center',
          textStyle: { color: '#a0a0a0', fontSize: 12 }
        }
      };
    }

    const weeks = timeSeries.map(w => `W${w.week || w.week_number || 0}`);
    const meanPreferences = timeSeries.map(w => (w.mean_preference || 0.5) * 100);
    const acceptanceRates = timeSeries.map(w => (w.acceptance_rate || 0) * 100);

    // Highlight current week
    const dataPoints = meanPreferences.map((val, idx) => ({
      value: [weeks[idx], val],
      itemStyle: {
        color: idx === currentWeek ? '#6366f1' : '#10b981',
        borderColor: idx === currentWeek ? '#fff' : 'transparent',
        borderWidth: idx === currentWeek ? 2 : 0
      }
    }));

    return {
      backgroundColor: 'transparent',
      textStyle: { color: '#e0e0e0' },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(21, 21, 32, 0.95)',
        borderColor: '#2a2a3a',
        textStyle: { color: '#e0e0e0' }
      },
      legend: {
        data: ['Mean Preference', 'Acceptance Rate'],
        textStyle: { color: '#e0e0e0', fontSize: 9 },
        top: 2
      },
      grid: {
        left: '15%',
        right: '8%',
        bottom: '15%',
        top: '18%'
      },
      xAxis: {
        type: 'category',
        data: weeks,
        axisLine: { lineStyle: { color: '#2a2a3a' } },
        axisLabel: { color: '#a0a0a0', fontSize: 8 }
      },
      yAxis: {
        type: 'value',
        max: 100,
        axisLine: { lineStyle: { color: '#2a2a3a' } },
        axisLabel: { color: '#a0a0a0', formatter: '{value}%', fontSize: 8 },
        splitLine: { lineStyle: { color: '#1a1a2a' } }
      },
      series: [
        {
          name: 'Mean Preference',
          type: 'line',
          data: meanPreferences,
          smooth: true,
          lineStyle: { color: '#10b981', width: 2 },
          itemStyle: { color: '#10b981' },
          markPoint: {
            data: [{ xAxis: currentWeek, yAxis: meanPreferences[currentWeek] || 0 }],
            itemStyle: { color: '#6366f1' },
            label: { show: true, formatter: 'Current', color: '#fff', fontSize: 8 }
          }
        },
        {
          name: 'Acceptance Rate',
          type: 'line',
          data: acceptanceRates,
          smooth: true,
          lineStyle: { color: '#6366f1', width: 2, type: 'dashed' },
          itemStyle: { color: '#6366f1' }
        }
      ]
    };
  };

  const networkGraph = useMemo(() => getNetworkGraph(), [segmentBreakdown]);
  const populationHeatmap = useMemo(() => getPopulationHeatmap(), [segmentBreakdown, timeSeries]);
  const agentStateChart = useMemo(() => getAgentStateChart(), [actions]);
  const preferenceEvolution = useMemo(() => getPreferenceEvolution(), [timeSeries, currentWeek]);

  if (!simulationResults) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm p-4">
        <div className="text-center">
          <div className="mb-2">🎯</div>
          <div>Run a simulation to see LPM visualization</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden p-3">
      {/* Header */}
      <div className="flex-shrink-0 mb-2">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-bold">LPM Population Visualization</h2>
          {isPhase34 && (
            <span className="text-xs px-2 py-1 bg-green-900/30 border border-green-700/50 text-green-400 rounded">
              ✓ Phase 3-4 Active
            </span>
          )}
        </div>
        
        {/* Controls */}
        <div className="flex items-center gap-2 mb-2">
          <select
            value={selectedCondition}
            onChange={(e) => setSelectedCondition(e.target.value)}
            className="bg-dark-surface border border-dark-border rounded px-2 py-1 text-xs text-gray-200"
          >
            <option value="baseline">Baseline</option>
            <option value="recipe_change">Recipe Change</option>
            <option value="price_change">Price Change</option>
            <option value="positioning">Positioning</option>
          </select>
          
          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-2 py-1 bg-accent-primary rounded text-xs hover:bg-accent-primary/80"
            >
              {isPlaying ? '⏸' : '▶'}
            </button>
            <button
              onClick={() => setCurrentWeek(0)}
              className="px-2 py-1 bg-dark-surface border border-dark-border rounded text-xs hover:bg-dark-hover"
            >
              ↺
            </button>
          </div>
          
          <input
            type="range"
            min="0.5"
            max="3"
            step="0.5"
            value={animationSpeed}
            onChange={(e) => setAnimationSpeed(parseFloat(e.target.value))}
            className="flex-1"
          />
          <span className="text-xs text-gray-400">{animationSpeed}x</span>
        </div>

        {/* Week Indicator */}
        {timeSeries.length > 0 && (
          <div className="text-xs text-gray-400 mb-1">
            Week: {currentWeek + 1} / {timeSeries.length}
          </div>
        )}
      </div>

      {/* Visualizations - Scrollable */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1" style={{ minHeight: 0 }}>
        {/* Population Network */}
        <div className="bg-dark-surface p-2 rounded border border-dark-border">
          <h3 className="font-semibold mb-1 text-xs">Segment Network</h3>
          <div style={{ height: '280px', width: '100%' }}>
            <ReactECharts
              option={networkGraph}
              style={{ height: '100%', width: '100%' }}
              opts={{ renderer: 'canvas' }}
              notMerge={true}
            />
          </div>
        </div>

        {/* Preference Evolution */}
        <div className="bg-dark-surface p-2 rounded border border-dark-border">
          <h3 className="font-semibold mb-1 text-xs">Preference Evolution</h3>
          <div style={{ height: '250px', width: '100%' }}>
            <ReactECharts
              option={preferenceEvolution}
              style={{ height: '100%', width: '100%' }}
              opts={{ renderer: 'canvas' }}
              notMerge={true}
            />
          </div>
        </div>

        {/* Population Heatmap */}
        <div className="bg-dark-surface p-2 rounded border border-dark-border">
          <h3 className="font-semibold mb-1 text-xs">Population Heatmap</h3>
          <div style={{ height: '280px', width: '100%' }}>
            <ReactECharts
              option={populationHeatmap}
              style={{ height: '100%', width: '100%' }}
              opts={{ renderer: 'canvas' }}
              notMerge={true}
            />
          </div>
        </div>

        {/* Agent States */}
        <div className="bg-dark-surface p-2 rounded border border-dark-border">
          <h3 className="font-semibold mb-1 text-xs">Agent States</h3>
          <div style={{ height: '220px', width: '100%' }}>
            <ReactECharts
              option={agentStateChart}
              style={{ height: '100%', width: '100%' }}
              opts={{ renderer: 'canvas' }}
              notMerge={true}
            />
          </div>
        </div>

        {/* Info Panel */}
        <div className="bg-dark-surface p-2 rounded border border-dark-border">
          <h3 className="font-semibold mb-1 text-xs">Population Stats</h3>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-400">Total Agents:</span>
              <span className="text-gray-200 font-semibold">
                {Object.values(segmentBreakdown).reduce((sum, seg) => sum + (seg.count || 0), 0)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Segments:</span>
              <span className="text-gray-200 font-semibold">{Object.keys(segmentBreakdown).length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Avg Acceptance:</span>
              <span className="text-green-400 font-semibold">
                {simulationResults.results_json?.overall_acceptance_rate 
                  ? (simulationResults.results_json.overall_acceptance_rate * 100).toFixed(1) + '%'
                  : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LPMVisualization;

