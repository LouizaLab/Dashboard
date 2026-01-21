import { useState } from 'react';

function SimulationControls({ onRunSimulation, loading, disabled }) {
  const [agentCount, setAgentCount] = useState(1000);
  const [timeHorizon, setTimeHorizon] = useState(12);
  const [segmentFilters, setSegmentFilters] = useState({
    age_bucket: [],
    archetype: [],
    region: [],
  });
  const [showAdvanced, setShowAdvanced] = useState(false);

  const ageBuckets = ['18-24', '25-34', '35-44', '45-54', '55+'];
  const archetypes = [
    'value_seeker',
    'health_optimizer',
    'convenience_loyalist',
    'late_night_craver',
    'trend_chaser',
    'family_bundle_buyer',
    'protein_maximizer',
  ];
  const regions = ['West', 'Midwest', 'South', 'Northeast'];

  const toggleFilter = (category, value) => {
    setSegmentFilters(prev => {
      const current = prev[category] || [];
      const updated = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value];
      return { ...prev, [category]: updated };
    });
  };

  const handleRun = () => {
    const filters = {};
    if (segmentFilters.age_bucket.length > 0) {
      filters.age_bucket = segmentFilters.age_bucket;
    }
    if (segmentFilters.archetype.length > 0) {
      filters.archetype = segmentFilters.archetype;
    }
    if (segmentFilters.region.length > 0) {
      filters.region = segmentFilters.region;
    }

    onRunSimulation({
      agent_count: agentCount,
      time_horizon_weeks: timeHorizon,
      segment_filters: filters,
    });
  };

  return (
    <div className="bg-dark-surface/50 rounded-lg p-4 border border-dark-border">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">LPM Simulation Parameters</h3>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-gray-400 hover:text-gray-200"
        >
          {showAdvanced ? 'Hide' : 'Show'} Advanced
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            Agent Count (LPM Population)
          </label>
          <div className="flex items-center gap-2">
            <input
              type="range"
              min="100"
              max="10000"
              step="100"
              value={agentCount}
              onChange={(e) => setAgentCount(parseInt(e.target.value))}
              className="flex-1"
              disabled={disabled || loading}
            />
            <input
              type="number"
              min="100"
              max="100000"
              step="100"
              value={agentCount}
              onChange={(e) => setAgentCount(parseInt(e.target.value) || 1000)}
              className="w-24 px-2 py-1 bg-dark-surface border border-dark-border rounded text-white text-sm"
              disabled={disabled || loading}
            />
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {agentCount >= 5000 ? 'Large Population (5k+)' :
             agentCount >= 1000 ? 'Medium Population (1k-5k)' :
             'Small Population (<1k)'}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Time Horizon (weeks)
          </label>
          <div className="flex items-center gap-2">
            <input
              type="range"
              min="1"
              max="52"
              value={timeHorizon}
              onChange={(e) => setTimeHorizon(parseInt(e.target.value))}
              className="flex-1"
              disabled={disabled || loading}
            />
            <input
              type="number"
              min="1"
              max="52"
              value={timeHorizon}
              onChange={(e) => setTimeHorizon(parseInt(e.target.value) || 12)}
              className="w-20 px-2 py-1 bg-dark-surface border border-dark-border rounded text-white text-sm"
              disabled={disabled || loading}
            />
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Simulating {timeHorizon} weeks of behavior evolution
          </div>
        </div>
      </div>

      {showAdvanced && (
        <div className="mb-4 p-3 bg-dark-surface rounded border border-dark-border">
          <label className="block text-sm font-medium mb-2">Segment Filters</label>
          <div className="space-y-3">
            <div>
              <div className="text-xs text-gray-400 mb-1">Age Buckets</div>
              <div className="flex flex-wrap gap-2">
                {ageBuckets.map((age) => (
                  <button
                    key={age}
                    onClick={() => toggleFilter('age_bucket', age)}
                    disabled={disabled || loading}
                    className={`px-3 py-1 rounded text-xs transition-all ${
                      segmentFilters.age_bucket.includes(age)
                        ? 'bg-accent-primary text-white'
                        : 'bg-dark-surface border border-dark-border hover:border-gray-600'
                    }`}
                  >
                    {age}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="text-xs text-gray-400 mb-1">Archetypes</div>
              <div className="flex flex-wrap gap-2">
                {archetypes.map((arch) => (
                  <button
                    key={arch}
                    onClick={() => toggleFilter('archetype', arch)}
                    disabled={disabled || loading}
                    className={`px-3 py-1 rounded text-xs transition-all ${
                      segmentFilters.archetype.includes(arch)
                        ? 'bg-accent-primary text-white'
                        : 'bg-dark-surface border border-dark-border hover:border-gray-600'
                    }`}
                  >
                    {arch.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="text-xs text-gray-400 mb-1">Regions</div>
              <div className="flex flex-wrap gap-2">
                {regions.map((region) => (
                  <button
                    key={region}
                    onClick={() => toggleFilter('region', region)}
                    disabled={disabled || loading}
                    className={`px-3 py-1 rounded text-xs transition-all ${
                      segmentFilters.region.includes(region)
                        ? 'bg-accent-primary text-white'
                        : 'bg-dark-surface border border-dark-border hover:border-gray-600'
                    }`}
                  >
                    {region}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <button
        onClick={handleRun}
        disabled={disabled || loading}
        className={`w-full py-4 rounded-lg font-semibold text-lg transition-all ${
          disabled || loading
            ? 'bg-gray-600/40 cursor-not-allowed backdrop-blur-sm'
            : 'bg-gray-600/40 text-white hover:bg-gray-500/50 backdrop-blur-sm'
        }`}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
            Running LPM Simulation...
          </span>
        ) : (
          '🚀 Run LPM Simulation'
        )}
      </button>

      {!disabled && (
        <div className="mt-3 text-xs text-gray-400 text-center">
          Simulating {agentCount.toLocaleString()} agents over {timeHorizon} weeks using Phase 3-4 LPM engine
        </div>
      )}
    </div>
  );
}

export default SimulationControls;
