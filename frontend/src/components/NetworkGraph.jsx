import cytoscape from 'cytoscape';
import { useEffect, useRef } from 'react';

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

    // Initialize Cytoscape WITHOUT layout - we'll run it manually
    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#6366f1',
            'label': 'data(label)',
            'width': 80, // Increased from 50 for better visibility
            'height': 80, // Increased from 50 for better visibility
            'font-size': '16px', // Increased from 11px for readability
            'font-weight': 'bold',
            'color': '#ffffff',
            'text-outline-width': 3, // Increased outline for better text visibility
            'text-outline-color': '#000000',
            'text-outline-opacity': 0.9,
            'text-wrap': 'wrap', // Allow text wrapping
            'text-max-width': '100px', // Max width before wrapping
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': -10, // Adjusted for larger nodes
            'border-width': 3, // Thicker border for visibility
            'border-color': '#818cf8',
            'border-opacity': 0.9,
            'shadow-blur': 10,
            'shadow-color': '#6366f1',
            'shadow-opacity': 0.6,
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
      // No initial layout - we'll run it manually
    });

    // Verify elements were added
    const nodeCount = cy.nodes().length;
    const edgeCount = cy.edges().length;
    console.log('Cytoscape initialized. Nodes:', nodeCount, 'Edges:', edgeCount);

    if (nodeCount === 0) {
      console.error('No nodes found in Cytoscape instance!');
      console.error('Elements passed:', elements);
      cyRef.current = cy;
      return;
    }

    // Use grid layout with good spacing to prevent overlap
    // Calculate optimal grid size for even distribution
    const cols = Math.ceil(Math.sqrt(nodeCount));
    const rows = Math.ceil(nodeCount / cols);

    const gridLayout = cy.layout({
      name: 'grid',
      rows: rows,
      cols: cols,
      fit: false,
      padding: 250, // Good padding to show all nodes
      spacingFactor: 3.0, // Even spacing between nodes
    });

    // After grid layout completes, fit the view and ensure no overlap
    gridLayout.one('layoutstop', () => {
      console.log('Grid layout complete, verifying spacing...');

      // Verify nodes are spaced properly
      const nodes = cy.nodes();
      let minDistance = Infinity;
      nodes.forEach((node1, i) => {
        nodes.slice(i + 1).forEach((node2) => {
          const pos1 = node1.position();
          const pos2 = node2.position();
          const distance = Math.sqrt(
            Math.pow(pos1.x - pos2.x, 2) + Math.pow(pos1.y - pos2.y, 2)
          );
          minDistance = Math.min(minDistance, distance);
        });
      });
      console.log('Minimum distance between nodes:', minDistance);

      setTimeout(() => {
        cy.resize();
        // Fit with generous padding to ensure all nodes are visible
        cy.fit(undefined, 200); // Increased padding to show all nodes
        const currentZoom = cy.zoom();
        // Ensure we're zoomed out enough to see everything
        // If still too zoomed in, zoom out further
        if (currentZoom > 0.6) {
          cy.zoom(0.45); // Zoom out more to show all nodes
        } else if (currentZoom < 0.3) {
          cy.zoom(0.45); // Don't zoom out too much
        }
        cy.center();
        console.log('Final fit complete at zoom:', cy.zoom());

        // Double-check: verify all nodes are within bounds
        const extent = cy.extent();
        const nodes = cy.nodes();
        let allVisible = true;
        nodes.forEach(node => {
          const pos = node.position();
          if (pos.x < extent.x1 || pos.x > extent.x2 ||
              pos.y < extent.y1 || pos.y > extent.y2) {
            allVisible = false;
          }
        });
        if (!allVisible) {
          // If nodes are outside bounds, fit again with even more padding
          cy.fit(undefined, 250);
          cy.zoom(0.4);
          cy.center();
          console.log('Adjusted fit to show all nodes');
        }
      }, 300);
    });

    // Ensure container is ready before running layout
    cy.ready(() => {
      cy.resize();
      gridLayout.run();
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
        cyRef.current.fit(undefined, 200); // Generous padding
        // Set zoom to show all nodes clearly
        const currentZoom = cyRef.current.zoom();
        if (currentZoom > 0.6) {
          cyRef.current.zoom(0.45); // Show all nodes
        } else if (currentZoom < 0.3) {
          cyRef.current.zoom(0.45);
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
                cyRef.current.fit(undefined, 200); // Generous padding
                cyRef.current.zoom(0.45); // Show all nodes clearly
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
