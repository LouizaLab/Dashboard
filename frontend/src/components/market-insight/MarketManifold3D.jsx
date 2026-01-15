import { useState, useEffect, useMemo } from 'react';
import Plot from 'react-plotly.js';

// Static Beauty Market Clusters with Fixed Positions
const BEAUTY_MARKET_CLUSTERS = [
  // Skincare
  { id: 'clean_skincare', label: 'Clean Skincare', category: 'skincare', baseX: -3.5, baseY: 3.0, color: '#10b981', baseMarketSize: 0.15 },
  { id: 'clinical_skincare', label: 'Clinical Derm-Backed Skincare', category: 'skincare', baseX: -1.5, baseY: 3.5, color: '#3b82f6', baseMarketSize: 0.20 },
  { id: 'barrier_repair', label: 'Barrier Repair Sensitive Skin', category: 'skincare', baseX: -0.8, baseY: 2.2, color: '#06b6d4', baseMarketSize: 0.12 },
  { id: 'acne_solution', label: 'Acne Problem-Solution Skincare', category: 'skincare', baseX: 0.8, baseY: 2.6, color: '#ef4444', baseMarketSize: 0.18 },
  { id: 'anti_aging', label: 'Anti-Aging Preventative Skincare', category: 'skincare', baseX: 2.2, baseY: 3.2, color: '#8b5cf6', baseMarketSize: 0.25 },

  // Makeup
  { id: 'minimal_makeup', label: 'Minimal Skin-First Makeup', category: 'makeup', baseX: -3.0, baseY: -0.8, color: '#84cc16', baseMarketSize: 0.10 },
  { id: 'premium_makeup', label: 'Premium Performance Makeup', category: 'makeup', baseX: -0.8, baseY: -1.5, color: '#f59e0b', baseMarketSize: 0.15 },
  { id: 'trend_makeup', label: 'Trend-Led Social Makeup', category: 'makeup', baseX: 1.5, baseY: -2.2, color: '#ec4899', baseMarketSize: 0.20 },
  { id: 'luxury_makeup', label: 'Luxury Full-Coverage Makeup', category: 'makeup', baseX: 3.5, baseY: -1.2, color: '#a855f7', baseMarketSize: 0.12 },

  // Fragrance
  { id: 'mass_fragrance', label: 'Mass Accessible Fragrance', category: 'fragrance', baseX: -2.2, baseY: -3.8, color: '#64748b', baseMarketSize: 0.08 },
  { id: 'prestige_fragrance', label: 'Prestige Fragrance', category: 'fragrance', baseX: 0.0, baseY: -4.2, color: '#6366f1', baseMarketSize: 0.12 },
  { id: 'ultra_luxury_fragrance', label: 'Ultra-Luxury Niche Fragrance', category: 'fragrance', baseX: 2.5, baseY: -3.5, color: '#d946ef', baseMarketSize: 0.05 },
];

// Cluster-specific motivations (static)
const CLUSTER_MOTIVATIONS = {
  clean_skincare: ['Clean ingredients', 'Non-toxic', 'Natural'],
  clinical_skincare: ['Dermatologist-recommended', 'Proven efficacy', 'Science-backed'],
  barrier_repair: ['Sensitive skin', 'Gentle formulas', 'Repair'],
  acne_solution: ['Problem-solving', 'Targeted treatment', 'Results'],
  anti_aging: ['Prevention', 'Anti-aging', 'Long-term care'],
  minimal_makeup: ['Natural look', 'Skin-first', 'Minimal routine'],
  premium_makeup: ['Performance', 'Long-wear', 'Quality'],
  trend_makeup: ['Social media', 'Trends', 'Experimentation'],
  luxury_makeup: ['Full coverage', 'Luxury', 'Status'],
  mass_fragrance: ['Accessibility', 'Value', 'Everyday'],
  prestige_fragrance: ['Quality', 'Brand', 'Occasion'],
  ultra_luxury_fragrance: ['Exclusivity', 'Niche', 'Luxury'],
};

/**
 * Calculate segment metrics for a cluster based on consumer filters
 * Returns relevance (0-1) and confidence (0-1)
 */
function getSegmentMetrics(clusterId, consumerFilters) {
  const cluster = BEAUTY_MARKET_CLUSTERS.find(c => c.id === clusterId);
  if (!cluster) return { relevance: 0.5, confidence: 0.5 };

  let relevance = cluster.baseMarketSize; // Start with base market size
  let confidence = 0.7; // Base confidence

  // Age Group Rules
  if (consumerFilters.age_group) {
    const ageRules = {
      gen_z: {
        trend_makeup: 0.3, minimal_makeup: 0.2, acne_solution: 0.25, mass_fragrance: 0.15,
        clean_skincare: 0.2, anti_aging: -0.1,
      },
      young_millennials: {
        premium_makeup: 0.25, clinical_skincare: 0.2, anti_aging: 0.2, prestige_fragrance: 0.15,
        barrier_repair: 0.15,
      },
      mid_millennials: {
        anti_aging: 0.3, clinical_skincare: 0.25, premium_makeup: 0.2, prestige_fragrance: 0.2,
      },
      gen_x: {
        anti_aging: 0.25, clinical_skincare: 0.2, luxury_makeup: 0.15, ultra_luxury_fragrance: 0.1,
      },
      '55_plus': {
        anti_aging: 0.3, clinical_skincare: 0.25, barrier_repair: 0.2, luxury_makeup: 0.15,
      },
    };
    const modifier = ageRules[consumerFilters.age_group]?.[clusterId] || 0;
    relevance += modifier;
    confidence += 0.1;
  }

  // Income Tier Rules
  if (consumerFilters.income_tier) {
    const incomeRules = {
      budget_constrained: {
        mass_fragrance: 0.2, minimal_makeup: 0.15, clean_skincare: 0.1, acne_solution: 0.1,
        ultra_luxury_fragrance: -0.2, luxury_makeup: -0.15,
      },
      middle_income: {
        premium_makeup: 0.15, prestige_fragrance: 0.1, clinical_skincare: 0.1,
      },
      upper_middle_income: {
        premium_makeup: 0.2, prestige_fragrance: 0.15, clinical_skincare: 0.15, anti_aging: 0.15,
      },
      high_income: {
        ultra_luxury_fragrance: 0.25, luxury_makeup: 0.2, clinical_skincare: 0.15, anti_aging: 0.2,
        prestige_fragrance: 0.15,
      },
    };
    const modifier = incomeRules[consumerFilters.income_tier]?.[clusterId] || 0;
    relevance += modifier;
    confidence += 0.1;
  }

  // Beauty Archetype Rules
  if (consumerFilters.beauty_archetype) {
    const archetypeRules = {
      minimalist: {
        minimal_makeup: 0.3, barrier_repair: 0.2, clean_skincare: 0.15, mass_fragrance: 0.1,
        trend_makeup: -0.2, luxury_makeup: -0.15,
      },
      beauty_enthusiast: {
        premium_makeup: 0.25, trend_makeup: 0.2, prestige_fragrance: 0.15, clinical_skincare: 0.15,
      },
      ingredient_obsessed: {
        clean_skincare: 0.3, clinical_skincare: 0.25, barrier_repair: 0.2, anti_aging: 0.15,
      },
      trend_follower: {
        trend_makeup: 0.35, minimal_makeup: 0.15, mass_fragrance: 0.1, clean_skincare: 0.1,
        anti_aging: -0.15,
      },
      prestige_luxury: {
        ultra_luxury_fragrance: 0.3, luxury_makeup: 0.25, prestige_fragrance: 0.2, clinical_skincare: 0.15,
        anti_aging: 0.15,
      },
      value_driven: {
        mass_fragrance: 0.2, minimal_makeup: 0.15, clean_skincare: 0.1, acne_solution: 0.1,
        ultra_luxury_fragrance: -0.25,
      },
      problem_solution: {
        acne_solution: 0.3, barrier_repair: 0.25, clinical_skincare: 0.2, anti_aging: 0.15,
      },
    };
    const modifier = archetypeRules[consumerFilters.beauty_archetype]?.[clusterId] || 0;
    relevance += modifier;
    confidence += 0.15;
  }

  // Primary Motivation Rules
  if (consumerFilters.primary_motivation) {
    const motivationRules = {
      appearance: {
        premium_makeup: 0.2, luxury_makeup: 0.15, trend_makeup: 0.15, prestige_fragrance: 0.1,
      },
      skin_health: {
        clinical_skincare: 0.25, barrier_repair: 0.2, clean_skincare: 0.15, acne_solution: 0.2,
      },
      anti_aging: {
        anti_aging: 0.35, clinical_skincare: 0.2, premium_makeup: 0.1,
      },
      confidence: {
        premium_makeup: 0.2, luxury_makeup: 0.15, prestige_fragrance: 0.15, ultra_luxury_fragrance: 0.1,
      },
      experimentation: {
        trend_makeup: 0.25, minimal_makeup: 0.15, mass_fragrance: 0.1,
      },
      value: {
        mass_fragrance: 0.2, minimal_makeup: 0.15, clean_skincare: 0.1, acne_solution: 0.1,
      },
    };
    const modifier = motivationRules[consumerFilters.primary_motivation]?.[clusterId] || 0;
    relevance += modifier;
    confidence += 0.1;
  }

  // Gender Rules
  if (consumerFilters.gender) {
    // Generally, makeup and fragrance are more gender-neutral in modern markets
    // Skincare tends to be slightly more female-leaning
    if (consumerFilters.gender === 'female') {
      if (cluster.category === 'skincare') relevance += 0.05;
      if (cluster.category === 'makeup') relevance += 0.03;
    }
    confidence += 0.05;
  }

  // Area Type Rules
  if (consumerFilters.area_type) {
    const areaRules = {
      urban: {
        trend_makeup: 0.1, premium_makeup: 0.1, prestige_fragrance: 0.1, ultra_luxury_fragrance: 0.05,
      },
      coastal_metro: {
        ultra_luxury_fragrance: 0.15, luxury_makeup: 0.1, prestige_fragrance: 0.1, clinical_skincare: 0.1,
      },
      suburban: {
        premium_makeup: 0.1, prestige_fragrance: 0.1, clinical_skincare: 0.1, anti_aging: 0.1,
      },
      rural: {
        mass_fragrance: 0.1, minimal_makeup: 0.1, clean_skincare: 0.1,
      },
    };
    const modifier = areaRules[consumerFilters.area_type]?.[clusterId] || 0;
    relevance += modifier;
    confidence += 0.05;
  }

  // Clamp values
  relevance = Math.max(0.05, Math.min(1.0, relevance)); // Never completely invisible
  confidence = Math.max(0.3, Math.min(1.0, confidence));

  return { relevance, confidence };
}

function MarketManifold3D({ vertical = 'beauty', region = 'US', onVerticalChange, onRegionChange, onNodeClick, selectedNodes = [], scenarioResults = null }) {
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    age_group: '',
    gender: '',
    income_tier: '',
    area_type: '',
    beauty_archetype: '',
    primary_motivation: '',
  });
  const [hoveredCluster, setHoveredCluster] = useState(null);
  const [pinnedClusters, setPinnedClusters] = useState([]);

  // Calculate metrics for each cluster based on current filters
  const clusterMetrics = useMemo(() => {
    return BEAUTY_MARKET_CLUSTERS.map(cluster => {
      const metrics = getSegmentMetrics(cluster.id, filters);
      return {
        ...cluster,
        ...metrics,
      };
    });
  }, [filters]);

  // Check if any filters are active
  const hasActiveFilters = Object.values(filters).some(v => v !== '');

  // Prepare data for Plotly
  const plotData = useMemo(() => {
    const traces = clusterMetrics.map(cluster => {
      const isSelected = selectedNodes.includes(cluster.id);
      const isPinned = pinnedClusters.includes(cluster.id);
      const isHovered = hoveredCluster === cluster.id;

      // Size based on relevance (0.05 to 1.0 maps to 10px to 50px) - scaled up for larger panel
      const baseSize = 10;
      const maxSize = 50;
      const size = baseSize + (cluster.relevance * (maxSize - baseSize));

      // Opacity based on confidence (0.3 to 1.0 maps to 0.3 to 1.0)
      let opacity = cluster.confidence;
      if (isSelected) opacity = 1.0;
      if (isPinned) opacity = Math.max(opacity, 0.9);
      if (isHovered) opacity = Math.min(opacity + 0.2, 1.0);

      // Color
      let color = cluster.color;
      if (isSelected) color = '#a855f7'; // Purple for selected
      if (isPinned) color = '#f59e0b'; // Orange for pinned

      // Calculate percentage of segment
      const segmentPercent = (cluster.relevance * 100).toFixed(1);

      // Hover text
      const hoverText = `
        <b>${cluster.label}</b><br>
        Segment Relevance: ${segmentPercent}%<br>
        Confidence: ${(cluster.confidence * 100).toFixed(0)}%<br>
        Category: ${cluster.category}<br>
        Top Motivations: ${CLUSTER_MOTIVATIONS[cluster.id]?.join(', ') || 'N/A'}
      `;

    return {
        x: [cluster.baseX],
        y: [cluster.baseY],
        z: [0], // 2D projection
        mode: 'markers+text',
      type: 'scatter3d',
        name: cluster.label,
      marker: {
          size: size,
          color: color,
          opacity: opacity,
        line: {
            color: isSelected ? '#fff' : color,
            width: isSelected ? 3 : isPinned ? 2 : 1.5,
          },
          sizemode: 'diameter',
        },
        text: [cluster.label],
        textposition: 'top center',
        textfont: {
          size: 14,
          color: '#ffffff',
          family: 'Inter, sans-serif',
        },
        hovertext: [hoverText],
      hoverinfo: 'text',
        customdata: [cluster.id],
      showlegend: false,
    };
  });

    return traces;
  }, [clusterMetrics, selectedNodes, pinnedClusters, hoveredCluster]);

  const layout = {
    scene: {
      xaxis: {
        visible: false,
        showgrid: false,
        showticklabels: false,
        showbackground: false,
        zeroline: false,
        range: [-5, 5],
      },
      yaxis: {
        visible: false,
        showgrid: false,
        showticklabels: false,
        showbackground: false,
        zeroline: false,
        range: [-5, 5],
      },
      zaxis: {
        visible: false,
        showgrid: false,
        showticklabels: false,
        showbackground: false,
        zeroline: false,
        range: [-1, 1],
      },
      bgcolor: '#0a0e1a',
      camera: {
        eye: { x: 0, y: 0, z: 1.5 },
        center: { x: 0, y: 0, z: 0 },
        up: { x: 0, y: 1, z: 0 },
      },
      aspectmode: 'manual',
      aspectratio: { x: 1, y: 1, z: 0.1 },
    },
    paper_bgcolor: '#0f172a',
    plot_bgcolor: '#0f172a',
    font: { color: '#9ca3af', family: 'Inter, sans-serif' },
    margin: { l: 0, r: 0, t: 0, b: 0 },
    showlegend: false,
  };

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: 'market-clusters',
    },
  };

  const handlePlotClick = (data) => {
    if (data.points && data.points.length > 0) {
      const clusterId = data.points[0].customdata;
      if (clusterId) {
        // Toggle pinning
        if (pinnedClusters.includes(clusterId)) {
          setPinnedClusters(pinnedClusters.filter(id => id !== clusterId));
        } else {
          setPinnedClusters([...pinnedClusters, clusterId]);
        }

        // Also call onNodeClick for parent component
        if (onNodeClick) {
          const cluster = BEAUTY_MARKET_CLUSTERS.find(c => c.id === clusterId);
          if (cluster) {
            onNodeClick({
              id: clusterId,
              label: cluster.label,
              type: 'cluster',
              category: cluster.category,
            });
          }
        }
      }
    }
  };

  const handlePlotHover = (data) => {
    if (data.points && data.points.length > 0) {
      const clusterId = data.points[0].customdata;
      setHoveredCluster(clusterId);
    } else {
      setHoveredCluster(null);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Filters */}
      <div className="p-4 border-b border-dark-border bg-dark-surface">
        {/* Row 1 */}
        <div className="flex flex-wrap gap-4 mb-4 justify-center">
          <div className="w-[200px]">
            <label className="text-xs text-gray-400 mb-1 block">Age Group</label>
            <div className="relative">
            <select
                className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
                value={filters.age_group}
                onChange={(e) => setFilters({ ...filters, age_group: e.target.value })}
              >
                <option value="">All</option>
                <option value="gen_z">Gen Z (16–24)</option>
                <option value="young_millennials">Young Millennials (25–34)</option>
                <option value="mid_millennials">Mid Millennials (35–44)</option>
                <option value="gen_x">Gen X (45–54)</option>
                <option value="55_plus">55+</option>
            </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
          <div className="w-[200px]">
            <label className="text-xs text-gray-400 mb-1 block">Gender</label>
            <div className="relative">
            <select
                className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
                value={filters.gender}
                onChange={(e) => setFilters({ ...filters, gender: e.target.value })}
            >
              <option value="">All</option>
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="non_binary">Non-binary / Gender-fluid</option>
            </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
          <div className="w-[200px]">
            <label className="text-xs text-gray-400 mb-1 block">Income Tier</label>
            <div className="relative">
            <select
                className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
                value={filters.income_tier}
                onChange={(e) => setFilters({ ...filters, income_tier: e.target.value })}
            >
              <option value="">All</option>
                <option value="budget_constrained">Budget-constrained</option>
                <option value="middle_income">Middle income</option>
                <option value="upper_middle_income">Upper-middle income</option>
                <option value="high_income">High income / Affluent</option>
            </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
        </div>
        {/* Row 2 */}
        <div className="flex flex-wrap gap-4 justify-center">
          <div className="w-[200px]">
            <label className="text-xs text-gray-400 mb-1 block">Area Type</label>
            <div className="relative">
            <select
                className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
                value={filters.area_type}
                onChange={(e) => setFilters({ ...filters, area_type: e.target.value })}
            >
              <option value="">All</option>
                <option value="urban">Urban</option>
                <option value="suburban">Suburban</option>
                <option value="rural">Rural</option>
                <option value="coastal_metro">Coastal Metro</option>
                <option value="secondary_cities">Secondary Cities</option>
            </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
          <div className="w-[200px]">
            <label className="text-xs text-gray-400 mb-1 block">Beauty Consumer Archetype</label>
            <div className="relative">
              <select
                className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
                value={filters.beauty_archetype}
                onChange={(e) => setFilters({ ...filters, beauty_archetype: e.target.value })}
              >
                <option value="">All</option>
                <option value="minimalist">Minimalist / Low-Routine</option>
                <option value="beauty_enthusiast">Beauty Enthusiast</option>
                <option value="ingredient_obsessed">Ingredient-Obsessed</option>
                <option value="trend_follower">Trend-Follower (TikTok-led)</option>
                <option value="prestige_luxury">Prestige / Luxury Buyer</option>
                <option value="value_driven">Value-Driven Shopper</option>
                <option value="problem_solution">Problem-Solution Seeker</option>
              </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
          <div className="w-[200px]">
            <label className="text-xs text-gray-400 mb-1 block">Primary Motivation</label>
            <div className="relative">
          <select
                className="w-full bg-dark-hover border border-dark-border rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 appearance-none"
                value={filters.primary_motivation}
                onChange={(e) => setFilters({ ...filters, primary_motivation: e.target.value })}
              >
                <option value="">All</option>
                <option value="appearance">Appearance / Aesthetics</option>
                <option value="skin_health">Skin Health / Repair</option>
                <option value="anti_aging">Anti-aging / Prevention</option>
                <option value="confidence">Confidence / Identity</option>
                <option value="experimentation">Experimentation / Fun</option>
                <option value="value">Value / Price</option>
          </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3D Plot */}
      <div className="flex-1 p-4 overflow-hidden">
        {Plot ? (
          <Plot
            data={plotData}
            layout={layout}
            config={config}
            style={{ width: '100%', height: '100%' }}
            onClick={handlePlotClick}
            onHover={handlePlotHover}
            onUnhover={() => setHoveredCluster(null)}
            useResizeHandler={true}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            Loading visualization...
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-dark-border bg-dark-surface">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500"></div>
            <span>Selected</span>
          </div>
          <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span>Pinned</span>
          </div>
            <div className="text-gray-500">
              {hasActiveFilters ? 'Dot size = Segment Relevance | Opacity = Confidence' : 'All clusters shown at base size'}
            </div>
          </div>
          <div className="text-gray-500">
            {BEAUTY_MARKET_CLUSTERS.length} clusters | {pinnedClusters.length} pinned
          </div>
        </div>
      </div>
    </div>
  );
}

export default MarketManifold3D;
