import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

function NetworkGraph({ nodes, edges, onNodeClick, onEdgeClick, viewType }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Debug logging
    console.log('NetworkGraph - nodes:', nodes);
    console.log('NetworkGraph - edges:', edges);
    console.log('NetworkGraph - nodes length:', nodes.length);
    console.log('NetworkGraph - edges length:', edges.length);

    if (nodes.length === 0) {
      console.warn('No nodes to render');
      return;
    }

    // Ensure nodes and edges are in correct format for Cytoscape
    // Nodes should be: [{data: {id, label, ...}}]
    // Edges should be: [{data: {id, source, target, ...}}]
    const elements = [...nodes, ...edges];
    console.log('NetworkGraph - elements to render:', elements);

    // Destroy existing instance if any
    if (cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
    }

    // Initialize Cytoscape
    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#6366f1',
            'label': 'data(label)',
            'width': 50,
            'height': 50,
            'font-size': '11px',
            'font-weight': 'bold',
            'color': '#ffffff',
            'text-outline-width': 2,
            'text-outline-color': '#000000',
            'text-outline-opacity': 0.8,
            'text-wrap': 'none',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': -8,
            'border-width': 2,
            'border-color': '#818cf8',
            'border-opacity': 0.8,
            'shadow-blur': 8,
            'shadow-color': '#6366f1',
            'shadow-opacity': 0.5,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 'mapData(weight, 0, 1, 1.5, 3)',
            'line-color': '#818cf8',
            'opacity': 'mapData(weight, 0, 1, 0.5, 0.8)',
            'curve-style': 'bezier',
            'target-arrow-color': '#818cf8',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1.0,
            'source-endpoint': 'outside-to-node',
            'target-endpoint': 'outside-to-node',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'background-color': '#8b5cf6',
            'border-width': 3,
            'border-color': '#a78bfa',
          },
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#a78bfa',
            'opacity': 1,
            'width': 6,
          },
        },
      ],
      layout: {
        name: 'cose',
        idealEdgeLength: 300,
        nodeOverlap: 10,
        refresh: 20,
        fit: true,
        padding: 150,
        randomize: true,
        componentSpacing: 250,
        nodeRepulsion: 12000,
        edgeElasticity: 0.4,
        nestingFactor: 0.05,
        gravity: 0.05,
        numIter: 3500,
        initialTemp: 400,
        coolingFactor: 0.97,
        minTemp: 0.5,
      },
    });

    // Verify elements were added
    const nodeCount = cy.nodes().length;
    const edgeCount = cy.edges().length;
    console.log('Cytoscape initialized. Nodes:', nodeCount, 'Edges:', edgeCount);
    
    if (nodeCount === 0) {
      console.error('No nodes found in Cytoscape instance!');
      console.error('Elements passed:', elements);
    }
    
    // Wait for layout to complete, then fit and resize
    cy.ready(() => {
      setTimeout(() => {
        cy.resize();
        // Fit with generous padding to ensure all nodes are visible
        cy.fit(undefined, 100);
        // Set zoom to show full graph - zoom out more for better overview
        const currentZoom = cy.zoom();
        if (currentZoom > 0.8) {
          cy.zoom(0.75);
        }
        cy.center();
        console.log('Cytoscape resized and fitted at zoom:', cy.zoom());
      }, 1000);
    });

    cyRef.current = cy;

    // Event handlers
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      onNodeClick(node.data('id'));
    });

    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      onEdgeClick(edge.data());
    });

    let tooltip = null;
    
    cy.on('mouseover', 'edge', (evt) => {
      const edge = evt.target;
      const weight = edge.data('weight') || edge.data('edge_weight') || 0;
      const topFactors = edge.data('top_factors') || {};
      
      if (tooltip) {
        document.body.removeChild(tooltip);
      }
      
      tooltip = document.createElement('div');
      tooltip.className = 'cytoscape-tooltip';
      tooltip.style.cssText = `
        position: fixed;
        background: rgba(21, 21, 32, 0.95);
        border: 1px solid #2a2a3a;
        border-radius: 8px;
        padding: 8px 12px;
        color: #e0e0e0;
        font-size: 12px;
        pointer-events: none;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        max-width: 200px;
      `;
      
      const factorsText = Object.entries(topFactors)
        .slice(0, 2)
        .map(([key, val]) => {
          const displayKey = key.replace(/_/g, ' ');
          const displayVal = typeof val === 'number' ? val.toFixed(2) : val;
          return `${displayKey}: ${displayVal}`;
        })
        .join('<br/>');
      
      tooltip.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 4px;">Weight: ${weight.toFixed(2)}</div>
        <div style="font-size: 11px; color: #a0a0a0;">${factorsText || 'No factors'}</div>
      `;
      
      document.body.appendChild(tooltip);
      
      const updateTooltip = (e) => {
        if (tooltip) {
          tooltip.style.left = `${e.originalEvent.clientX + 10}px`;
          tooltip.style.top = `${e.originalEvent.clientY + 10}px`;
        }
      };
      
      cy.on('mousemove', 'edge', updateTooltip);
      updateTooltip(evt);
    });
    
    cy.on('mouseout', 'edge', () => {
      if (tooltip) {
        document.body.removeChild(tooltip);
        tooltip = null;
      }
    });

    // Cleanup
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [nodes, edges, onNodeClick, onEdgeClick, viewType]);

  // Refit when viewType changes
  useEffect(() => {
    if (cyRef.current && nodes.length > 0) {
      setTimeout(() => {
        cyRef.current.resize();
        cyRef.current.fit(undefined, 100);
        // Reset zoom to show full graph - zoom out for better spacing
        const currentZoom = cyRef.current.zoom();
        if (currentZoom > 0.8) {
          cyRef.current.zoom(0.75);
        }
        cyRef.current.center();
      }, 500);
    }
  }, [viewType, nodes.length]);

  return (
    <div className="w-full h-full bg-dark-bg relative" style={{ minHeight: '500px' }}>
      <div
        ref={containerRef}
        id="cytoscape-container"
        className="w-full h-full"
        style={{ 
          minHeight: '500px', 
          width: '100%', 
          height: '100%',
          position: 'absolute',
          top: 0,
          left: 0,
        }}
      />
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <div className="text-gray-400">No network data available. Check console for details.</div>
        </div>
      )}
      {nodes.length > 0 && (
        <div className="absolute top-4 right-4 z-20">
          <button
            onClick={() => {
              if (cyRef.current) {
                cyRef.current.fit(undefined, 100);
                cyRef.current.zoom(0.75);
                cyRef.current.center();
              }
            }}
            className="bg-dark-surface border border-dark-border rounded-lg px-3 py-2 text-sm text-gray-300 hover:bg-dark-hover hover:border-accent-primary transition-colors"
            title="Fit all nodes"
          >
            🔍 Fit View
          </button>
        </div>
      )}
    </div>
  );
}

export default NetworkGraph;

