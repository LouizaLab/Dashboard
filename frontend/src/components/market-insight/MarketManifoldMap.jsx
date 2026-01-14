import { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';

function MarketManifoldMap({ vertical = 'beauty', region = 'US', onNodeClick, selectedNodes = [], scenarioResults = null }) {
  const svgRef = useRef(null);
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    category: '',
    price_tier: '',
    channel: '',
    momentum_range: [0, 1],
    brand_type: '',
  });
  const [hoveredNode, setHoveredNode] = useState(null);
  const [pinnedNodes, setPinnedNodes] = useState([]);

  useEffect(() => {
    loadManifoldData();
  }, [vertical, region]);

  const loadManifoldData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/market-insight-new/manifold/?vertical=${vertical}&region=${region}`
      );
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setPoints(data.points || []);
    } catch (error) {
      console.error('Failed to load manifold data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (points.length === 0 || loading) return;

    // Clear previous render
    d3.select(svgRef.current).selectAll('*').remove();

    const width = 800;
    const height = 600;
    const margin = { top: 20, right: 20, bottom: 40, left: 40 };

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Filter points
    let filteredPoints = points;
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
        p => p.momentum >= filters.momentum_range[0] && p.momentum <= filters.momentum_range[1]
      );
    }

    // Set up scales
    const xExtent = d3.extent(filteredPoints, d => d.x);
    const yExtent = d3.extent(filteredPoints, d => d.y);

    const xScale = d3.scaleLinear()
      .domain(xExtent)
      .range([margin.left, width - margin.right]);

    const yScale = d3.scaleLinear()
      .domain(yExtent)
      .range([height - margin.bottom, margin.top]);

    // Color scale by cluster
    const clusters = [...new Set(filteredPoints.map(d => d.cluster_id).filter(Boolean))];
    const colorScale = d3.scaleOrdinal()
      .domain(clusters)
      .range(d3.schemeCategory10);
    
    // Get impacted clusters from scenario
    const impactedClusters = scenarioResults?.impacted_clusters || [];
    const impactedClusterLabels = new Set(impactedClusters);

    // Draw points
    const pointsGroup = svg.append('g');

    pointsGroup.selectAll('circle')
      .data(filteredPoints)
      .enter()
      .append('circle')
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y))
      .attr('r', d => {
        const isSelected = Array.isArray(selectedNodes) ? selectedNodes.includes(d.id) : selectedNodes === d.id;
        const isPinned = Array.isArray(pinnedNodes) ? pinnedNodes.includes(d.id) : pinnedNodes === d.id;
        if (isSelected) return 8;
        if (isPinned) return 7;
        return 5;
      })
      .attr('fill', d => {
        const isSelected = Array.isArray(selectedNodes) ? selectedNodes.includes(d.id) : selectedNodes === d.id;
        const isPinned = Array.isArray(pinnedNodes) ? pinnedNodes.includes(d.id) : pinnedNodes === d.id;
        if (isSelected) return '#a855f7';
        if (isPinned) return '#f59e0b';
        
        // Highlight impacted clusters from scenario
        if (scenarioResults && d.cluster_label && impactedClusterLabels.has(d.cluster_label)) {
          return '#ef4444'; // Red for impacted clusters
        }
        
        return d.cluster_id ? colorScale(d.cluster_id) : '#6b7280';
      })
      .attr('stroke', d => {
        const isSelected = Array.isArray(selectedNodes) ? selectedNodes.includes(d.id) : selectedNodes === d.id;
        if (isSelected) return '#fff';
        
        // Add red stroke for impacted clusters
        if (scenarioResults && d.cluster_label && impactedClusterLabels.has(d.cluster_label)) {
          return '#ef4444';
        }
        
        return 'none';
      })
      .attr('stroke-width', d => {
        const isSelected = Array.isArray(selectedNodes) ? selectedNodes.includes(d.id) : selectedNodes === d.id;
        if (isSelected) return 2;
        
        // Add stroke for impacted clusters
        if (scenarioResults && d.cluster_label && impactedClusterLabels.has(d.cluster_label)) {
          return 2;
        }
        
        return 0;
      })
      .attr('stroke', d => {
        const isSelected = Array.isArray(selectedNodes) ? selectedNodes.includes(d.id) : selectedNodes === d.id;
        return isSelected ? '#fff' : 'none';
      })
      .attr('stroke-width', d => selectedNodes.includes(d.id) ? 2 : 0)
      .attr('opacity', 0.7)
      .on('mouseover', function(event, d) {
        setHoveredNode(d);
        d3.select(this).attr('opacity', 1).attr('r', 7);
      })
      .on('mouseout', function() {
        setHoveredNode(null);
        d3.select(this).attr('opacity', 0.7).attr('r', 5);
      })
      .on('click', function(event, d) {
        if (event.shiftKey) {
          // Pin/unpin node
          if (pinnedNodes.includes(d.id)) {
            setPinnedNodes(pinnedNodes.filter(id => id !== d.id));
          } else {
            setPinnedNodes([...pinnedNodes, d.id]);
          }
        } else {
          // Select node
          if (onNodeClick) {
            onNodeClick(d);
          }
        }
      });

    // Tooltip
    if (hoveredNode) {
      const tooltip = svg.append('g')
        .attr('class', 'tooltip')
        .attr('transform', `translate(${xScale(hoveredNode.x) + 10}, ${yScale(hoveredNode.y) - 10})`);

      tooltip.append('rect')
        .attr('width', 200)
        .attr('height', 60)
        .attr('fill', 'rgba(0, 0, 0, 0.8)')
        .attr('rx', 4);

      tooltip.append('text')
        .attr('x', 10)
        .attr('y', 20)
        .attr('fill', 'white')
        .attr('font-size', '12px')
        .text(hoveredNode.label);

      tooltip.append('text')
        .attr('x', 10)
        .attr('y', 35)
        .attr('fill', '#9ca3af')
        .attr('font-size', '10px')
        .text(`${hoveredNode.type} | ${hoveredNode.tier || hoveredNode.brand_type || ''}`);

      tooltip.append('text')
        .attr('x', 10)
        .attr('y', 50)
        .attr('fill', '#9ca3af')
        .attr('font-size', '10px')
        .text(`Cluster: ${hoveredNode.cluster_label || 'N/A'}`);
    }

    // Axes
    svg.append('g')
      .attr('transform', `translate(0, ${height - margin.bottom})`)
      .call(d3.axisBottom(xScale))
      .attr('color', '#9ca3af');

    svg.append('g')
      .attr('transform', `translate(${margin.left}, 0)`)
      .call(d3.axisLeft(yScale))
      .attr('color', '#9ca3af');

  }, [points, loading, filters, selectedNodes, pinnedNodes, hoveredNode, scenarioResults, onNodeClick]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Loading manifold...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Filters */}
      <div className="p-4 border-b border-dark-border bg-dark-surface">
        <div className="grid grid-cols-5 gap-4">
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
      </div>

      {/* Map */}
      <div className="flex-1 p-4 overflow-auto">
        <svg ref={svgRef} className="w-full h-full" />
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
            <span>Pinned (Shift+Click)</span>
          </div>
          {scenarioResults && (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500 border-2 border-red-500"></div>
              <span>Impacted by Scenario</span>
            </div>
          )}
          <div className="text-gray-500">
            {points.length} points | {pinnedNodes.length} pinned
          </div>
        </div>
      </div>
    </div>
  );
}

export default MarketManifoldMap;
