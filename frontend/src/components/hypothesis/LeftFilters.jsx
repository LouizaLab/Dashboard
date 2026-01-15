function LeftFilters({ filters, setFilters }) {
  const updateFilter = (key, value) => {
    setFilters({ ...filters, [key]: value });
  };

  return (
    <div className="w-64 bg-dark-surface border-r border-dark-border p-4 overflow-y-auto">
      <div className="space-y-6">
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            YEAR
          </label>
          <div className="relative">
            <input
              type="range"
              min="2020"
              max="2025"
              value={filters.year}
              onChange={(e) => updateFilter('year', parseInt(e.target.value))}
              className="w-full h-2 bg-dark-hover rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #9ca3af 0%, #9ca3af ${((filters.year - 2020) / 5) * 100}%, #374151 ${((filters.year - 2020) / 5) * 100}%, #374151 100%)`
              }}
            />
            <div className="text-center mt-2 text-xl font-bold text-gray-300">
              {filters.year}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Demographics
          </h3>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Age Bucket
            </label>
            <div className="relative">
              <select
                value={filters.age_bucket}
                onChange={(e) => updateFilter('age_bucket', e.target.value)}
                className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
              >
                <option value="">All Ages</option>
                <option value="18-24">18-24</option>
                <option value="25-34">25-34</option>
                <option value="35-44">35-44</option>
                <option value="45-54">45-54</option>
                <option value="55+">55+</option>
              </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Gender
            </label>
            <div className="relative">
              <select
                value={filters.gender}
                onChange={(e) => updateFilter('gender', e.target.value)}
                className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
              >
                <option value="">All Genders</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Nonbinary">Nonbinary</option>
                <option value="Prefer not to say">Prefer not to say</option>
              </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Region
            </label>
            <div className="relative">
              <select
                value={filters.region}
                onChange={(e) => updateFilter('region', e.target.value)}
                className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
              >
                <option value="">All Regions</option>
                <option value="West">West</option>
                <option value="Midwest">Midwest</option>
                <option value="South">South</option>
                <option value="Northeast">Northeast</option>
              </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Income
            </label>
            <div className="relative">
              <select
                value={filters.income}
                onChange={(e) => updateFilter('income', e.target.value)}
                className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
              >
                <option value="">All Income Levels</option>
                <option value="$0-50k">$0-50k</option>
                <option value="$50-100k">$50-100k</option>
                <option value="$100-150k">$100-150k</option>
                <option value="$150k+">$150k+</option>
              </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Behavioral Archetype
          </h3>
          <div className="relative">
            <select
              value={filters.archetype}
              onChange={(e) => updateFilter('archetype', e.target.value)}
              className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-accent-primary appearance-none"
            >
              <option value="">All Archetypes</option>
              <option value="ingredient_purist">Ingredient Purist</option>
              <option value="clean_beauty_believer">Clean Beauty Believer</option>
              <option value="clinical_results_seeker">Clinical Results Seeker</option>
              <option value="luxury_ritualist">Luxury Ritualist</option>
              <option value="trend_driven_experimenter">Trend-Driven Experimenter</option>
              <option value="problem_solution_buyer">Problem-Solution Buyer</option>
              <option value="sensitive_skin_minimalist">Sensitive-Skin Minimalist</option>
              <option value="makeup_maximalist">Makeup Maximalist</option>
              <option value="skinimalist">Skinimalist</option>
              <option value="ethical_buyer">Ethical Buyer</option>
              <option value="deal_hunter">Deal Hunter</option>
              <option value="pro_guided_buyer">Pro-Guided Buyer</option>
              <option value="age_preventive_optimizer">Age-Preventive Optimizer</option>
              <option value="routine_loyalist">Routine Loyalist</option>
              <option value="fragrance_identity_buyer">Fragrance Identity Buyer</option>
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Agent Count: {filters.agent_count}
          </label>
          <input
            type="range"
            min="10"
            max="150"
            value={filters.agent_count}
            onChange={(e) => updateFilter('agent_count', parseInt(e.target.value))}
            className="w-full h-2 bg-dark-hover rounded-lg appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, #9ca3af 0%, #9ca3af ${((filters.agent_count - 10) / 140) * 100}%, #374151 ${((filters.agent_count - 10) / 140) * 100}%, #374151 100%)`
            }}
          />
        </div>

      </div>
    </div>
  );
}

export default LeftFilters;
