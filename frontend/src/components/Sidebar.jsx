function Sidebar({ viewType, setViewType, filters, setFilters }) {
  const viewOptions = [
    'Market Insight',
    'Foot Traffic',
    'Revenue',
    'Intent',
    'Taste Dynamics',
  ];

  const ageBuckets = ['18-24', '25-34', '35-44', '45-54', '55+'];
  const incomeLevels = ['low', 'medium', 'high'];
  const regions = ['northeast', 'south', 'midwest', 'west'];

  const updateFilter = (key, value) => {
    setFilters({ ...filters, [key]: value });
  };

  return (
    <div className="w-64 bg-dark-surface border-r border-dark-border p-4 overflow-y-auto">
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            VIEW
          </label>
          <select
            value={viewType}
            onChange={(e) => setViewType(e.target.value)}
            className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-accent-primary"
          >
            {viewOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-4">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Demographics
          </h3>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Age Bucket
            </label>
            <select
              value={filters.age_bucket}
              onChange={(e) => updateFilter('age_bucket', e.target.value)}
              className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="">All Ages</option>
              {ageBuckets.map((age) => (
                <option key={age} value={age}>
                  {age}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Income
            </label>
            <select
              value={filters.income}
              onChange={(e) => updateFilter('income', e.target.value)}
              className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="">All Income Levels</option>
              {incomeLevels.map((level) => (
                <option key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Region
            </label>
            <select
              value={filters.region}
              onChange={(e) => updateFilter('region', e.target.value)}
              className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="">All Regions</option>
              {regions.map((region) => (
                <option key={region} value={region}>
                  {region.charAt(0).toUpperCase() + region.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Sidebar;

