import ReactECharts from 'echarts-for-react';
import { useMemo } from 'react';

function ApprovalPanel({ simulationResults }) {
  // Extract data early for use in render
  const timeSeries = simulationResults?.results_json?.time_series || [];
  const segmentBreakdown = simulationResults?.results_json?.segment_breakdown || {};
  const actions = simulationResults?.results_json?.actions || {};
  const approvalAssessments = simulationResults?.approval_assessment_json || {};
  
  const chartOptions = useMemo(() => {
    if (!simulationResults) return null;

    const overallAcceptance = simulationResults.results_json?.overall_acceptance_rate || 0;
    const confidence = simulationResults.confidence_score || 0;
    const rejectionRate = simulationResults.results_json?.overall_rejection_rate || 0;

    const getOverallApproval = () => {
      const assessments = Object.values(approvalAssessments);
      if (assessments.length === 0) {
        return { status: 'unknown', color: 'gray' };
      }
      const approvedCount = assessments.filter(a => a.approved).length;
      const approvalRate = approvedCount / assessments.length;
      if (approvalRate >= 0.7) {
        return { status: 'approved', color: 'green' };
      } else if (approvalRate >= 0.4) {
        return { status: 'risky', color: 'yellow' };
      } else {
        return { status: 'rejected', color: 'red' };
      }
    };

    const overallApproval = getOverallApproval();

    // Risk Gauge
    const getRiskGaugeChart = () => ({
      backgroundColor: 'transparent',
      textStyle: { color: '#e0e0e0' },
      series: [{
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: 100,
        splitNumber: 4,
        axisLine: {
          lineStyle: {
            width: 10,
            color: [[0.3, '#10b981'], [0.6, '#f59e0b'], [1, '#ef4444']]
          }
        },
        pointer: { itemStyle: { color: 'auto' } },
        axisTick: { distance: -25, splitNumber: 5, lineStyle: { width: 1, color: '#999' } },
        splitLine: { distance: -25, lineStyle: { width: 2, color: '#999' } },
        axisLabel: { distance: -15, color: '#a0a0a0', fontSize: 9 },
        detail: {
          valueAnimation: true,
          formatter: '{value}%',
          color: '#e0e0e0',
          fontSize: 14,
          fontWeight: 'bold',
          offsetCenter: [0, '-30%']
        },
        data: [{ value: rejectionRate * 100, name: 'Risk' }]
      }]
    });

    // Time Series Chart
    const getTimeSeriesChart = () => {
      if (timeSeries.length === 0) {
        return {
          backgroundColor: 'transparent',
          textStyle: { color: '#e0e0e0' },
          title: { text: 'No Data', left: 'center', top: 'center', textStyle: { color: '#a0a0a0', fontSize: 11 } }
        };
      }
      const weeks = timeSeries.map(w => `W${w.week || w.week_number || 0}`);
      const acceptanceRates = timeSeries.map(w => parseFloat(((w.acceptance_rate || 0) * 100).toFixed(1)));
      const rejectionRates = timeSeries.map(w => parseFloat(((w.rejection_rate || 0) * 100).toFixed(1)));
      return {
        backgroundColor: 'transparent',
        textStyle: { color: '#e0e0e0' },
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(21, 21, 32, 0.95)', borderColor: '#2a2a3a', textStyle: { color: '#e0e0e0' } },
        legend: { data: ['Acceptance', 'Rejection'], textStyle: { color: '#e0e0e0', fontSize: 9 }, top: 2 },
        grid: { left: '18%', right: '8%', bottom: '18%', top: '20%' },
        xAxis: { type: 'category', data: weeks, axisLine: { lineStyle: { color: '#2a2a3a' } }, axisLabel: { color: '#a0a0a0', fontSize: 9 } },
        yAxis: { type: 'value', axisLine: { lineStyle: { color: '#2a2a3a' } }, axisLabel: { color: '#a0a0a0', formatter: '{value}%', fontSize: 9 }, splitLine: { lineStyle: { color: '#1a1a2a' } } },
        series: [
          { name: 'Acceptance', type: 'line', data: acceptanceRates, smooth: true, lineStyle: { color: '#10b981', width: 2 }, itemStyle: { color: '#10b981' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(16, 185, 129, 0.3)' }, { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }] } } },
          { name: 'Rejection', type: 'line', data: rejectionRates, smooth: true, lineStyle: { color: '#ef4444', width: 2 }, itemStyle: { color: '#ef4444' } }
        ]
      };
    };

    // Persona Approval
    const getPersonaApprovalChart = () => {
      const personas = Object.entries(approvalAssessments);
      if (personas.length === 0) {
        return {
          backgroundColor: 'transparent',
          textStyle: { color: '#e0e0e0' },
          title: { text: 'No Data', left: 'center', top: 'center', textStyle: { color: '#a0a0a0', fontSize: 11 } }
        };
      }
      const data = personas.map(([id, assessment]) => ({
        value: assessment.approved ? 100 : 0,
        name: id.substring(0, 8) + '...',
        approved: assessment.approved
      }));
      return {
        backgroundColor: 'transparent',
        textStyle: { color: '#e0e0e0' },
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(21, 21, 32, 0.95)', borderColor: '#2a2a3a', textStyle: { color: '#e0e0e0' } },
        grid: { left: '25%', right: '8%', bottom: '20%', top: '8%' },
        xAxis: { type: 'category', data: data.map(d => d.name), axisLine: { lineStyle: { color: '#2a2a3a' } }, axisLabel: { color: '#a0a0a0', rotate: 45, fontSize: 8 } },
        yAxis: { type: 'value', max: 100, axisLine: { lineStyle: { color: '#2a2a3a' } }, axisLabel: { color: '#a0a0a0', formatter: '{value}%', fontSize: 9 }, splitLine: { lineStyle: { color: '#1a1a2a' } } },
        series: [{
          type: 'bar',
          data: data.map(d => ({ value: d.value, itemStyle: { color: d.approved ? '#10b981' : '#ef4444' } })),
          barWidth: '50%',
          label: { show: true, position: 'top', color: '#e0e0e0', formatter: '{c}%', fontSize: 9 }
        }]
      };
    };

    // Segment Breakdown
    const getSegmentChart = () => {
      const segments = Object.entries(segmentBreakdown);
      if (segments.length === 0) {
        return {
          backgroundColor: 'transparent',
          textStyle: { color: '#e0e0e0' },
          title: { text: 'No Data', left: 'center', top: 'center', textStyle: { color: '#a0a0a0', fontSize: 11 } }
        };
      }
      const data = segments.map(([key, data]) => ({
        value: data.count || 0,
        name: key.replace('_', ' - ').substring(0, 15),
        acceptanceRate: data.actions?.accept || 0
      }));
      return {
        backgroundColor: 'transparent',
        textStyle: { color: '#e0e0e0' },
        tooltip: { trigger: 'item', backgroundColor: 'rgba(21, 21, 32, 0.95)', borderColor: '#2a2a3a', textStyle: { color: '#e0e0e0' } },
        legend: { orient: 'vertical', right: 3, top: 'middle', textStyle: { color: '#a0a0a0', fontSize: 8 } },
        series: [{
          type: 'pie',
          radius: ['35%', '65%'],
          center: ['35%', '50%'],
          itemStyle: { borderRadius: 5, borderColor: '#1a1a2e', borderWidth: 2 },
          label: { show: true, formatter: '{b}\n{c}', color: '#e0e0e0', fontSize: 8 },
          data: data
        }]
      };
    };

    // Action Distribution
    const getActionChart = () => {
      const actionCounts = { accept: 0, reject: 0, substitute: 0, reduce_frequency: 0, increase_frequency: 0 };
      Object.values(actions).forEach(action => {
        if (actionCounts.hasOwnProperty(action)) actionCounts[action]++;
      });
      const total = Object.values(actionCounts).reduce((a, b) => a + b, 0);
      if (total === 0) {
        return {
          backgroundColor: 'transparent',
          textStyle: { color: '#e0e0e0' },
          title: { text: 'No Data', left: 'center', top: 'center', textStyle: { color: '#a0a0a0', fontSize: 11 } }
        };
      }
      const data = Object.entries(actionCounts)
        .filter(([_, count]) => count > 0)
        .map(([action, count]) => ({
          value: parseFloat((count / total * 100).toFixed(1)),
          name: action.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
        }));
      return {
        backgroundColor: 'transparent',
        textStyle: { color: '#e0e0e0' },
        tooltip: { trigger: 'item', backgroundColor: 'rgba(21, 21, 32, 0.95)', borderColor: '#2a2a3a', textStyle: { color: '#e0e0e0' } },
        legend: { orient: 'horizontal', bottom: 2, textStyle: { color: '#e0e0e0', fontSize: 9 } },
        series: [{
          type: 'pie',
          radius: '60%',
          center: ['50%', '40%'],
          data: data,
          itemStyle: { borderRadius: 5, borderColor: '#1a1a2e', borderWidth: 2 },
          label: { show: true, formatter: '{b}\n{c}%', color: '#e0e0e0', fontSize: 9 }
        }]
      };
    };

    // Demographic Heatmap
    const getDemographicHeatmap = () => {
      const segments = Object.entries(segmentBreakdown);
      if (segments.length === 0) {
        return {
          backgroundColor: 'transparent',
          textStyle: { color: '#e0e0e0' },
          title: { text: 'No Data', left: 'center', top: 'center', textStyle: { color: '#a0a0a0', fontSize: 11 } }
        };
      }
      const ageData = {};
      segments.forEach(([key, data]) => {
        const ageMatch = key.match(/(\d+-\d+|\d+\+)/);
        if (ageMatch) {
          const age = ageMatch[1];
          if (!ageData[age]) ageData[age] = [];
          ageData[age].push(data.actions?.accept || 0);
        }
      });
      const ages = Object.keys(ageData).sort();
      const avgAcceptance = ages.map(age => {
        const rates = ageData[age];
        return rates.length > 0 ? rates.reduce((a, b) => a + b, 0) / rates.length : 0;
      });
      return {
        backgroundColor: 'transparent',
        textStyle: { color: '#e0e0e0' },
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(21, 21, 32, 0.95)', borderColor: '#2a2a3a', textStyle: { color: '#e0e0e0' } },
        grid: { left: '18%', right: '8%', bottom: '18%', top: '10%' },
        xAxis: { type: 'category', data: ages, axisLine: { lineStyle: { color: '#2a2a3a' } }, axisLabel: { color: '#a0a0a0', fontSize: 9 } },
        yAxis: { type: 'value', max: 1, axisLine: { lineStyle: { color: '#2a2a3a' } }, axisLabel: { color: '#a0a0a0', formatter: '{value}', fontSize: 9 }, splitLine: { lineStyle: { color: '#1a1a2a' } } },
        series: [{
          type: 'bar',
          data: avgAcceptance.map(rate => ({
            value: (rate * 100).toFixed(1),
            itemStyle: { color: rate >= 0.7 ? '#10b981' : rate >= 0.4 ? '#f59e0b' : '#ef4444' }
          })),
          barWidth: '60%',
          label: { show: true, position: 'top', formatter: '{c}%', color: '#e0e0e0', fontSize: 9 }
        }]
      };
    };

    return {
      overallApproval,
      overallAcceptance,
      confidence,
      rejectionRate,
      entropyDelta: simulationResults.entropy_delta || 0,
      riskGaugeChart: getRiskGaugeChart(),
      timeSeriesChart: getTimeSeriesChart(),
      personaChart: getPersonaApprovalChart(),
      segmentChart: getSegmentChart(),
      actionChart: getActionChart(),
      demographicHeatmap: getDemographicHeatmap(),
    };
  }, [simulationResults, timeSeries, segmentBreakdown, actions, approvalAssessments]);

  if (!simulationResults || !chartOptions) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        {!simulationResults ? 'Complete a simulation to see approval assessment' : 'Loading...'}
      </div>
    );
  }

  const { overallApproval, overallAcceptance, confidence, rejectionRate, entropyDelta, 
          riskGaugeChart, timeSeriesChart, personaChart, segmentChart, actionChart,
          demographicHeatmap } = chartOptions;

  return (
    <div className="h-full flex flex-col overflow-hidden p-3">
      {/* Header - Fixed */}
      <div className="flex-shrink-0 space-y-1.5 mb-1.5">
        {/* Overall Approval Status */}
        <div className={`p-2 rounded-lg border-2 ${
          overallApproval.color === 'green' ? 'border-green-500 bg-green-500/10' :
          overallApproval.color === 'yellow' ? 'border-yellow-500 bg-yellow-500/10' :
          overallApproval.color === 'red' ? 'border-red-500 bg-red-500/10' :
          'border-gray-500 bg-gray-500/10'
        }`}>
          <div className="text-xs font-bold mb-0.5">
            Overall: {overallApproval.status.toUpperCase()}
          </div>
          <div className="text-xs text-gray-300">
            {overallApproval.status === 'approved' && 'Ready for launch'}
            {overallApproval.status === 'risky' && 'Needs review'}
            {overallApproval.status === 'rejected' && 'Does not meet criteria'}
            {overallApproval.status === 'unknown' && 'Insufficient data'}
          </div>
        </div>

        {/* Key Metrics - Compact Grid */}
        <div className="grid grid-cols-3 gap-1.5">
          <div className="bg-dark-surface p-1.5 rounded border border-dark-border text-center">
            <div className="text-xs text-gray-400 mb-0.5">Accept</div>
            <div className={`text-sm font-bold ${overallAcceptance >= 0.6 ? 'text-green-400' : 'text-red-400'}`}>
              {(overallAcceptance * 100).toFixed(0)}%
            </div>
          </div>
          <div className="bg-dark-surface p-1.5 rounded border border-dark-border text-center">
            <div className="text-xs text-gray-400 mb-0.5">Conf</div>
            <div className={`text-sm font-bold ${confidence >= 0.7 ? 'text-green-400' : 'text-yellow-400'}`}>
              {(confidence * 100).toFixed(0)}%
            </div>
          </div>
          <div className="bg-dark-surface p-1.5 rounded border border-dark-border text-center">
            <div className="text-xs text-gray-400 mb-0.5">Entropy</div>
            <div className={`text-sm font-bold ${entropyDelta < 0 ? 'text-green-400' : 'text-yellow-400'}`}>
              {entropyDelta.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Charts Container - Scrollable */}
      <div className="flex-1 overflow-y-auto space-y-1.5 pr-1" style={{ minHeight: 0 }}>
        {/* Risk Gauge */}
        <div className="bg-dark-surface p-2 rounded border border-dark-border">
          <h3 className="font-semibold mb-1 text-xs">Risk Gauge</h3>
          <div style={{ height: '200px', width: '100%' }}>
            <ReactECharts option={riskGaugeChart} style={{ height: '100%', width: '100%' }} opts={{ renderer: 'canvas' }} notMerge={true} />
          </div>
        </div>

        {/* Acceptance Over Time */}
        <div className="bg-dark-surface p-2 rounded border border-dark-border">
          <h3 className="font-semibold mb-1 text-xs">Acceptance Over Time</h3>
          <div style={{ height: '240px', width: '100%' }}>
            <ReactECharts option={timeSeriesChart} style={{ height: '100%', width: '100%' }} opts={{ renderer: 'canvas' }} notMerge={true} />
          </div>
        </div>

        {/* Persona Approval */}
        <div className="bg-dark-surface p-2 rounded border border-dark-border">
          <h3 className="font-semibold mb-1 text-xs">Persona Approval</h3>
          <div style={{ height: '200px', width: '100%' }}>
            <ReactECharts option={personaChart} style={{ height: '100%', width: '100%' }} opts={{ renderer: 'canvas' }} notMerge={true} />
          </div>
        </div>

        {/* Segments */}
        <div className="bg-dark-surface p-2 rounded border border-dark-border">
          <h3 className="font-semibold mb-1 text-xs">Segments</h3>
          <div style={{ height: '240px', width: '100%' }}>
            <ReactECharts option={segmentChart} style={{ height: '100%', width: '100%' }} opts={{ renderer: 'canvas' }} notMerge={true} />
          </div>
        </div>

        {/* Action Distribution */}
        <div className="bg-dark-surface p-2 rounded border border-dark-border">
          <h3 className="font-semibold mb-1 text-xs">Actions</h3>
          <div style={{ height: '200px', width: '100%' }}>
            <ReactECharts option={actionChart} style={{ height: '100%', width: '100%' }} opts={{ renderer: 'canvas' }} notMerge={true} />
          </div>
        </div>

        {/* Age Group Acceptance */}
        <div className="bg-dark-surface p-2 rounded border border-dark-border">
          <h3 className="font-semibold mb-1 text-xs">Age Groups</h3>
          <div style={{ height: '200px', width: '100%' }}>
            <ReactECharts option={demographicHeatmap} style={{ height: '100%', width: '100%' }} opts={{ renderer: 'canvas' }} notMerge={true} />
          </div>
        </div>

        {/* Persona Assessments - Compact */}
        {Object.keys(approvalAssessments).length > 0 && (
          <div className="bg-dark-surface p-1.5 rounded border border-dark-border">
            <h3 className="font-semibold mb-1 text-xs">Personas</h3>
            <div className="space-y-0.5 max-h-32 overflow-y-auto">
              {Object.entries(approvalAssessments).slice(0, 4).map(([personaId, assessment]) => (
                <div key={personaId} className={`p-1 rounded border text-xs ${
                  assessment.approved ? 'border-green-500/50 bg-green-500/5' : 'border-red-500/50 bg-red-500/5'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{personaId.substring(0, 12)}...</span>
                    <span className={`px-1 py-0.5 rounded text-xs ${
                      assessment.approved ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {assessment.approved ? '✓' : '✗'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ApprovalPanel;
