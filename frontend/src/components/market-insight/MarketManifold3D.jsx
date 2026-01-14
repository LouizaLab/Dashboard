import { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';

function MarketManifold3D({ vertical = 'beauty', region = 'US', onNodeClick, selectedNodes = [], scenarioResults = null }) {
  const [points, setPoints] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [hulls, setHulls] = useState({});
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    category: '',
    price_tier: '',
    brand_type: '',
    momentum_range: [0, 1],
    view: 'markets', // markets, brands, products
    cluster: '', // Filter by cluster
  });
  const [hoveredNode, setHoveredNode] = useState(null);
  const [pinnedNodes, setPinnedNodes] = useState([]);

  useEffect(() => {
    loadManifoldData();
  }, [vertical, region]);

  useEffect(() => {
    // Update reactivity scores from scenario results
    if (scenarioResults && scenarioResults.impacted_points) {
      const reactivityMap = {};
      scenarioResults.impacted_points.forEach(p => {
        reactivityMap[p.node_id] = p.reactivity_score;
      });
      
      setPoints(prevPoints => 
        prevPoints.map(p => ({
          ...p,
          reactivity_score: reactivityMap[p.id] || p.reactivity_score || null,
        }))
      );
    }
  }, [scenarioResults]);

  const loadManifoldData = async () => {
    setLoading(true);
    try {
      const url = `http://localhost:8000/api/market-insight-new/manifold/?vertical=${vertical}&region=${region}&organic=true`;
      console.log('Loading manifold from:', url);
      const response = await fetch(url);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API error:', response.status, errorText);
        throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 200)}`);
      }
      const data = await response.json();
      console.log('Manifold data loaded:', {
        points: data.points?.length || 0,
        clusters: data.clusters?.length || 0,
        hulls: Object.keys(data.hulls || {}).length
      });
      setPoints(data.points || []);
      setClusters(data.clusters || []);
      setHulls(data.hulls || {});
      
      if (!data.points || data.points.length === 0) {
        console.warn('No points returned from API. Manifold may need to be rebuilt.');
      }
    } catch (error) {
      console.error('Failed to load manifold data:', error);
      setPoints([]);
      setClusters([]);
      setHulls({});
    } finally {
      setLoading(false);
    }
  };

  // Filter points
  let filteredPoints = points;
  if (filters.view === 'markets') {
    filteredPoints = filteredPoints.filter(p => p.type === 'market');
  } else if (filters.view === 'brands') {
    filteredPoints = filteredPoints.filter(p => p.type === 'brand');
  } else if (filters.view === 'products') {
    filteredPoints = filteredPoints.filter(p => p.type === 'product');
  }

  if (filters.category) {
    filteredPoints = filteredPoints.filter(p => p.category === filters.category);
  }
  if (filters.price_tier) {
    filteredPoints = filteredPoints.filter(p => p.tier === filters.price_tier);
  }
  if (filters.brand_type && filteredPoints.some(p => p.brand_type)) {
    filteredPoints = filteredPoints.filter(p => p.brand_type === filters.brand_type);
  }
  if (filters.momentum_range) {
    filteredPoints = filteredPoints.filter(
      p => (p.momentum || 0) >= filters.momentum_range[0] && (p.momentum || 0) <= filters.momentum_range[1]
    );
  }
  if (filters.cluster) {
    filteredPoints = filteredPoints.filter(
      p => p.cluster_id !== null && p.cluster_id.toString() === filters.cluster
    );
  }

  // Prepare data for Plotly with enhanced color scheme
  const getColorForPoint = (point) => {
    const isSelected = Array.isArray(selectedNodes) ? selectedNodes.includes(point.id) : selectedNodes === point.id;
    const isPinned = Array.isArray(pinnedNodes) ? pinnedNodes.includes(point.id) : pinnedNodes === point.id;
    
    if (isSelected) return '#a855f7'; // Purple for selected
    if (isPinned) return '#f59e0b'; // Orange for pinned
    
    // Color by reactivity if available
    if (point.reactivity_score !== null && point.reactivity_score !== undefined) {
      // Red gradient based on reactivity
      const intensity = Math.floor(point.reactivity_score * 255);
      return `rgb(${intensity}, ${Math.floor(intensity * 0.3)}, ${Math.floor(intensity * 0.1)})`;
    }
    
    // Color by cluster with a more vibrant palette
    if (point.cluster_id !== null && point.cluster_id !== undefined) {
      const colors = [
        '#3b82f6', // Blue
        '#10b981', // Emerald
        '#f59e0b', // Amber
        '#ef4444', // Red
        '#8b5cf6', // Violet
        '#ec4899', // Pink
        '#06b6d4', // Cyan
        '#84cc16', // Lime
        '#f97316', // Orange
        '#6366f1', // Indigo
        '#14b8a6', // Teal
        '#a855f7', // Purple
        '#f43f5e', // Rose
        '#0ea5e9', // Sky
        '#22c55e', // Green
        '#eab308', // Yellow
        '#d946ef', // Fuchsia
        '#64748b', // Slate
      ];
      return colors[Math.abs(point.cluster_id) % colors.length];
    }
    
    return '#64748b'; // Slate gray default
  };

  const getSizeForPoint = (point) => {
    const isSelected = Array.isArray(selectedNodes) ? selectedNodes.includes(point.id) : selectedNodes === point.id;
    const isPinned = Array.isArray(pinnedNodes) ? pinnedNodes.includes(point.id) : pinnedNodes === point.id;
    
    // Base bubble size - make them larger and more bubble-like
    let baseSize = 12; // Larger base size for bubbles
    
    if (isSelected) return baseSize * 1.8; // 21.6
    if (isPinned) return baseSize * 1.5; // 18
    
    // Vary size based on cluster (makes bubbles more interesting)
    if (point.cluster_id !== null && point.cluster_id !== undefined) {
      // Add some variation based on cluster ID for visual interest
      const clusterVariation = 1 + (point.cluster_id % 3) * 0.2; // 1.0, 1.2, or 1.4
      baseSize = baseSize * clusterVariation;
    }
    
    if (point.reactivity_score !== null && point.reactivity_score !== undefined) {
      return baseSize + (point.reactivity_score * baseSize * 0.5); // Scale with reactivity
    }
    
    return baseSize;
  };

  // Early return if no points
  if (filteredPoints.length === 0 && !loading) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-dark-border bg-dark-surface">
          <h2 className="text-xl font-bold text-gray-200">Market Manifold</h2>
        </div>
        <div className="flex-1 flex items-center justify-center text-gray-400 p-8">
          <div className="text-center">
            <div className="text-lg mb-2">No manifold data available</div>
            <div className="text-sm mb-4">
              {points.length === 0 
                ? "The manifold needs to be built. Run this command in the backend:"
                : "No points match the current filters. Try adjusting filters."}
            </div>
            {points.length === 0 && (
              <code className="block bg-dark-surface p-3 rounded text-xs text-left max-w-md">
                python3 manage.py rebuild_market_manifold --vertical beauty --region US --organic
              </code>
            )}
          </div>
        </div>
      </div>
    );
  }

  const x = filteredPoints.map(p => p.x);
  const y = filteredPoints.map(p => p.y);
  const z = filteredPoints.map(p => p.z || 0);
  const colors = filteredPoints.map(p => getColorForPoint(p));
  const sizes = filteredPoints.map(p => getSizeForPoint(p));
  const labels = filteredPoints.map(p => 
    `${p.label || 'Point'}\n${p.cluster_label || 'No cluster'}\n${p.type || 'market'} | ${p.tier || p.brand_type || ''}`
  );
    const hoverText = filteredPoints.map(p => {
    let text = `<b>${p.label || `Point ${p.id?.substring(0, 8) || 'unknown'}`}</b><br>`;
    text += `Type: ${p.type || 'market'}<br>`;
    if (p.category) text += `Category: ${p.category}<br>`;
    if (p.tier) text += `Tier: ${p.tier}<br>`;
    if (p.cluster_label) {
      text += `Cluster: ${p.cluster_label}<br>`;
      // Add cluster drivers if available
      const cluster = clusters.find(c => c.cluster_id === p.cluster_id);
      if (cluster && cluster.drivers) {
        if (cluster.drivers.claims && cluster.drivers.claims.length > 0) {
          text += `Claims: ${cluster.drivers.claims.join(', ')}<br>`;
        }
        if (cluster.drivers.channel) {
          text += `Channel: ${cluster.drivers.channel}<br>`;
        }
      }
    }
    if (p.momentum !== null && p.momentum !== undefined) text += `Momentum: ${p.momentum.toFixed(2)}<br>`;
    if (p.reactivity_score !== null && p.reactivity_score !== undefined) {
      text += `Reactivity: ${(p.reactivity_score * 100).toFixed(1)}%<br>`;
    }
    return text;
  });

  // Add cluster hull boundaries (2D projection on x-y plane)
  const hullTraces = [];
  Object.entries(hulls).forEach(([clusterId, hullPoints]) => {
    if (hullPoints && hullPoints.length > 0 && Array.isArray(hullPoints)) {
      // Close the hull by adding first point at the end
      const closedHull = [...hullPoints, hullPoints[0]];
      const hullX = closedHull.map(p => Array.isArray(p) ? p[0] : p.x || 0);
      const hullY = closedHull.map(p => Array.isArray(p) ? p[1] : p.y || 0);
      // Use average z for the hull
      const clusterPoints = filteredPoints.filter(p => p.cluster_id !== null && p.cluster_id.toString() === clusterId);
      const avgZ = clusterPoints.length > 0 
        ? clusterPoints.reduce((sum, p) => sum + (p.z || 0), 0) / clusterPoints.length 
        : 0;
      const hullZ = closedHull.map(() => avgZ);
      
      const clusterColor = getColorForPoint({ cluster_id: parseInt(clusterId) });
      
      hullTraces.push({
        x: hullX,
        y: hullY,
        z: hullZ,
        mode: 'lines',
        type: 'scatter3d',
        line: {
          color: clusterColor,
          width: 2,
          dash: 'dash',
        },
        opacity: 0.3,
        showlegend: false,
        hoverinfo: 'skip',
      });
    }
  });

  // Group points by cluster for distinct colors
  const clusterGroups = {};
  filteredPoints.forEach((p, idx) => {
    const cid = p.cluster_id !== null && p.cluster_id !== undefined ? p.cluster_id : -1;
    if (!clusterGroups[cid]) {
      clusterGroups[cid] = {
        points: [],
        indices: [],
        label: p.cluster_label || `Cluster ${cid}`,
      };
    }
    clusterGroups[cid].points.push(p);
    clusterGroups[cid].indices.push(idx);
  });

  // Create a trace for each cluster with distinct colors
  const clusterTraces = Object.entries(clusterGroups).map(([cid, group]) => {
    const clusterX = group.indices.map(i => x[i]);
    const clusterY = group.indices.map(i => y[i]);
    const clusterZ = group.indices.map(i => z[i]);
    const clusterColors = group.indices.map(i => colors[i]);
    const clusterSizes = group.indices.map(i => sizes[i]);
    const clusterHoverText = group.indices.map(i => hoverText[i]);
    
    // Use distinct color per cluster (not from individual points)
    const distinctColors = [
      '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
      '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1',
      '#14b8a6', '#a855f7', '#f43f5e', '#0ea5e9', '#22c55e',
      '#eab308', '#d946ef', '#64748b'
    ];
    const clusterColor = distinctColors[Math.abs(parseInt(cid)) % distinctColors.length];
    
    return {
      x: clusterX,
      y: clusterY,
      z: clusterZ,
      mode: 'markers',
      type: 'scatter3d',
      name: group.label,
      marker: {
        size: clusterSizes,
        color: clusterColor,
        opacity: 0.75, // Slightly more transparent for bubble effect
        line: {
          color: group.points.map(p => {
            const isSelected = Array.isArray(selectedNodes) ? selectedNodes.includes(p.id) : selectedNodes === p.id;
            return isSelected ? '#fff' : clusterColor; // Use cluster color for bubble border
          }),
          width: group.points.map(p => {
            const isSelected = Array.isArray(selectedNodes) ? selectedNodes.includes(p.id) : selectedNodes === p.id;
            return isSelected ? 3 : 1.5; // Thicker borders for bubble effect
          }),
        },
        sizemode: 'diameter', // Use diameter instead of area for more bubble-like appearance
      },
      hovertext: clusterHoverText,
      hoverinfo: 'text',
      customdata: group.points.map(p => p.id),
      showlegend: false,
    };
  });

  // Create cluster label annotations (centroid labels)
  const distinctColors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1',
    '#14b8a6', '#a855f7', '#f43f5e', '#0ea5e9', '#22c55e',
    '#eab308', '#d946ef', '#64748b'
  ];
  
  const labelAnnotations = Object.entries(clusterGroups).map(([cid, group]) => {
    const clusterX = group.indices.map(i => x[i]);
    const clusterY = group.indices.map(i => y[i]);
    const clusterZ = group.indices.map(i => z[i]);
    
    const centroidX = clusterX.reduce((a, b) => a + b, 0) / clusterX.length;
    const centroidY = clusterY.reduce((a, b) => a + b, 0) / clusterY.length;
    const centroidZ = clusterZ.reduce((a, b) => a + b, 0) / clusterZ.length;
    
    const clusterColor = distinctColors[Math.abs(parseInt(cid)) % distinctColors.length];
    
    return {
      x: centroidX,
      y: centroidY,
      z: centroidZ,
      text: group.label,
      showarrow: false,
      font: {
        size: 14,
        color: '#ffffff',
        family: 'Inter, sans-serif',
      },
      bgcolor: clusterColor,
      bordercolor: '#ffffff',
      borderwidth: 1,
      borderpad: 4,
      opacity: 0.9,
    };
  });

  // Create label trace (separate trace for labels)
  const labelTrace = {
    x: labelAnnotations.map(a => a.x),
    y: labelAnnotations.map(a => a.y),
    z: labelAnnotations.map(a => a.z),
    mode: 'text',
    type: 'scatter3d',
    text: labelAnnotations.map(a => a.text),
    textfont: {
      size: 14,
      color: '#ffffff',
      family: 'Inter, sans-serif',
    },
    textposition: 'middle center',
    hoverinfo: 'skip',
    showlegend: false,
  };

  const plotData = [
    ...hullTraces, // Draw hulls first (behind points)
    ...clusterTraces, // Draw clusters with distinct colors
    labelTrace, // Draw cluster labels
  ];

  const layout = {
    title: {
      text: 'Market Manifold',
      font: { color: '#e5e7eb', size: 20, family: 'Inter, sans-serif' },
      x: 0.5,
      xanchor: 'center',
    },
    annotations: labelAnnotations,
    scene: {
      xaxis: { 
        visible: false,
        showgrid: false,
        showticklabels: false,
        showbackground: false,
        zeroline: false,
      },
      yaxis: { 
        visible: false,
        showgrid: false,
        showticklabels: false,
        showbackground: false,
        zeroline: false,
      },
      zaxis: { 
        visible: false,
        showgrid: false,
        showticklabels: false,
        showbackground: false,
        zeroline: false,
      },
      bgcolor: '#0a0e1a',
      camera: {
        eye: { x: 1.8, y: 1.8, z: 1.8 },
        center: { x: 0, y: 0, z: 0 },
        up: { x: 0, y: 0, z: 1 },
      },
      aspectmode: 'data',
    },
    paper_bgcolor: '#0f172a',
    plot_bgcolor: '#0f172a',
    font: { color: '#9ca3af', family: 'Inter, sans-serif' },
    margin: { l: 0, r: 0, t: 60, b: 0 },
    showlegend: false,
  };

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: 'market-manifold-3d',
    },
  };

  const handlePlotClick = (data) => {
    if (data.points && data.points.length > 0) {
      const point = data.points[0];
      const nodeId = point.customdata;
      const node = filteredPoints.find(p => p.id === nodeId);
      
      if (node && onNodeClick) {
        // Check for shift+click (would need to track mouse events)
        onNodeClick(node);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Loading 3D manifold...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Filters */}
      <div className="p-4 border-b border-dark-border bg-dark-surface">
        <div className="grid grid-cols-6 gap-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">View</label>
            <select
              className="w-full bg-dark-bg border border-dark-border rounded px-2 py-1 text-sm text-gray-300"
              value={filters.view}
              onChange={(e) => setFilters({ ...filters, view: e.target.value })}
            >
              <option value="markets">Markets</option>
              <option value="brands">Brands</option>
              <option value="products">Products</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Category</label>
            <select
              className="w-full bg-dark-bg border border-dark-border rounded px-2 py-1 text-sm text-gray-300"
              value={filters.category}
              onChange={(e) => setFilters({ ...filters, category: e.target.value })}
            >
              <option value="">All</option>
              <option value="Skincare">Skincare</option>
              <option value="Makeup">Makeup</option>
              <option value="Fragrance">Fragrance</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Price Tier</label>
            <select
              className="w-full bg-dark-bg border border-dark-border rounded px-2 py-1 text-sm text-gray-300"
              value={filters.price_tier}
              onChange={(e) => setFilters({ ...filters, price_tier: e.target.value })}
            >
              <option value="">All</option>
              <option value="premium">Premium</option>
              <option value="super_premium">Super-Premium</option>
              <option value="ultra_luxury">Ultra-Luxury</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Brand Type</label>
            <select
              className="w-full bg-dark-bg border border-dark-border rounded px-2 py-1 text-sm text-gray-300"
              value={filters.brand_type}
              onChange={(e) => setFilters({ ...filters, brand_type: e.target.value })}
            >
              <option value="">All</option>
              <option value="heritage">Heritage</option>
              <option value="indie">Indie</option>
              <option value="luxury">Luxury</option>
            </select>
          </div>
          <div className="col-span-2">
            <label className="text-xs text-gray-400 mb-1 block">
              Momentum: {filters.momentum_range[0].toFixed(2)} - {filters.momentum_range[1].toFixed(2)}
            </label>
            <input
              type="range"
              min="-0.5"
              max="1"
              step="0.1"
              value={filters.momentum_range[1]}
              onChange={(e) => setFilters({
                ...filters,
                momentum_range: [filters.momentum_range[0], parseFloat(e.target.value)]
              })}
              className="w-full"
            />
          </div>
        </div>
        <div className="mt-4">
          <label className="text-xs text-gray-400 mb-1 block">Cluster</label>
          <select
            className="w-full bg-dark-bg border border-dark-border rounded px-2 py-1 text-sm text-gray-300"
            value={filters.cluster}
            onChange={(e) => setFilters({ ...filters, cluster: e.target.value })}
          >
            <option value="">All Clusters</option>
            {clusters.map(cluster => (
              <option key={cluster.cluster_id} value={cluster.cluster_id.toString()}>
                {cluster.label} ({cluster.count} points)
              </option>
            ))}
          </select>
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
            onHover={(data) => {
              if (data.points && data.points.length > 0) {
                const nodeId = data.points[0].customdata;
                const node = filteredPoints.find(p => p.id === nodeId);
                setHoveredNode(node);
              }
            }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-lg mb-2">Plotly.js not loaded</div>
              <div className="text-sm">Install with: npm install plotly.js react-plotly.js</div>
              <div className="text-xs mt-4 text-gray-600">
                Points loaded: {filteredPoints.length}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-dark-border bg-dark-surface">
        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500"></div>
            <span>Selected</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span>Pinned</span>
          </div>
          {scenarioResults && (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span>Impacted (red gradient = reactivity)</span>
            </div>
          )}
          <div className="text-gray-500">
            {filteredPoints.length} points | {pinnedNodes.length} pinned
          </div>
        </div>
      </div>
    </div>
  );
}

export default MarketManifold3D;
