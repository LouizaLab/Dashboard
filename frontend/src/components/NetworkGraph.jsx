import cytoscape from 'cytoscape';
import { useEffect, useRef } from 'react';

function NetworkGraph({ nodes, edges, onNodeClick, onEdgeClick, viewType }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const onNodeClickRef = useRef(onNodeClick);
  const onEdgeClickRef = useRef(onEdgeClick);
  const hasInitialFitRef = useRef(false);

  // Keep callbacks refs up to date
  useEffect(() => {
    onNodeClickRef.current = onNodeClick;
    onEdgeClickRef.current = onEdgeClick;
  }, [onNodeClick, onEdgeClick]);

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

    // Remove any existing tooltips before destroying
    const existingTooltips = document.querySelectorAll('.cytoscape-tooltip');
    existingTooltips.forEach(tooltip => {
      if (tooltip.parentNode) {
        tooltip.parentNode.removeChild(tooltip);
      }
    });

    // Destroy existing instance if any
    if (cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
      hasInitialFitRef.current = false; // Reset flag when destroying
    }

    // Initialize Cytoscape WITHOUT layout - we'll run it manually
    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#1f1f2e',
            'label': 'data(label)',
            'width': 120,
            'height': 120,
            'font-size': 20,
            'font-weight': 600,
            'font-family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
            'color': '#ffffff',
            'text-outline-width': 3,
            'text-outline-color': '#0a0a0a',
            'text-outline-opacity': 0.9,
            'text-wrap': 'none',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 22,
            'text-transform': 'none',
            'letter-spacing': '0',
            'border-width': 4,
            'border-color': '#9ca3af',
            'border-opacity': 0.8,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 'mapData(weight, 0, 1, 1.5, 3)',
            'line-color': '#9ca3af',
            'opacity': 'mapData(weight, 0, 1, 0.5, 0.8)',
            'curve-style': 'bezier',
            'target-arrow-color': '#9ca3af',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1.0,
            'source-endpoint': 'outside-to-node',
            'target-endpoint': 'outside-to-node',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'background-color': '#6b7280',
            'border-width': 3,
            'border-color': '#9ca3af',
            'color': '#ffffff',
            'text-outline-color': '#0a0a0a',
            'font-weight': 600,
          },
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#9ca3af',
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
      fit: false, // Don't let layout auto-fit
      padding: 250, // Good padding to show all nodes
      spacingFactor: 3.0, // Even spacing between nodes
      animate: false, // Disable layout animation to prevent glitches
    });

    // After grid layout completes, fit the view and ensure no overlap
    // Use 'one' to ensure this only fires once
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

      // Only fit/zoom on initial load, not on subsequent layouts
      if (!hasInitialFitRef.current) {
        // Use requestAnimationFrame to ensure layout is fully complete before fitting
        requestAnimationFrame(() => {
          cy.resize();
          // Calculate and set viewport in one go to avoid double animation
          const padding = 200;
          const boundingBox = cy.elements().boundingBox();
          const width = cy.width();
          const height = cy.height();

          // Calculate zoom to fit with padding, capped at 0.75 for more zoomed in view
          const scaleX = (width - padding * 2) / boundingBox.w;
          const scaleY = (height - padding * 2) / boundingBox.h;
          const targetZoom = Math.min(scaleX, scaleY, 0.75);

          // Set zoom and pan in one operation without animation
          cy.stop(); // Stop any ongoing animations
          cy.zoom(targetZoom);
          const centerX = boundingBox.x1 + boundingBox.w / 2;
          const centerY = boundingBox.y1 + boundingBox.h / 2;
          cy.pan({
            x: width / 2 - centerX * targetZoom,
            y: height / 2 - centerY * targetZoom
          });

          hasInitialFitRef.current = true;
          console.log('Initial fit/zoom complete at zoom:', cy.zoom());
        });
      } else {
        // Preserve user's zoom/pan on subsequent layouts - just resize
        cy.resize();
        console.log('Layout complete, preserving zoom:', cy.zoom());
      }
    });

    // Ensure container is ready before running layout
    cy.ready(() => {
      cy.resize();
      // Only run layout if we haven't done initial fit yet
      if (!hasInitialFitRef.current) {
        gridLayout.run();
      }
    });

    cyRef.current = cy;

    // Event handlers - use refs to avoid re-initialization
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      // Remove any visible tooltip when node is clicked
      const existingTooltip = document.querySelector('.cytoscape-tooltip');
      if (existingTooltip) {
        document.body.removeChild(existingTooltip);
      }
      if (onNodeClickRef.current) {
        onNodeClickRef.current(node.data('id'));
      }
    });

    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      // Remove any visible tooltip when edge is clicked
      const existingTooltip = document.querySelector('.cytoscape-tooltip');
      if (existingTooltip) {
        document.body.removeChild(existingTooltip);
      }
      if (onEdgeClickRef.current) {
        onEdgeClickRef.current(edge.data());
      }
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
      // Remove any visible tooltips
      const existingTooltips = document.querySelectorAll('.cytoscape-tooltip');
      existingTooltips.forEach(tooltip => {
        if (tooltip.parentNode) {
          tooltip.parentNode.removeChild(tooltip);
        }
      });

      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [nodes, edges, viewType]); // Removed onNodeClick and onEdgeClick from deps to prevent re-initialization on click

  // Only resize when container size changes, don't refit/zoom
  // The gridLayout callback handles initial fit/zoom, so we don't duplicate it here
  useEffect(() => {
    if (cyRef.current) {
      // Just resize to handle container changes, preserve user's zoom/pan
      cyRef.current.resize();
    }
  }, [nodes.length]); // Only resize when nodes change, don't refit/zoom

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
                cyRef.current.zoom(0.75); // Show all nodes clearly, more zoomed in
                cyRef.current.center();
              }
            }}
            className="bg-dark-surface/80 border border-dark-border rounded-lg px-3 py-2 text-sm text-gray-300 hover:bg-dark-hover/80 backdrop-blur-sm transition-colors"
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
