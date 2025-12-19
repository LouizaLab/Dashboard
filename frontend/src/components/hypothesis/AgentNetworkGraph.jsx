import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

function AgentNetworkGraph({ nodes, edges, onAgentClick, selectedAgentIds = [] }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...nodes, ...edges],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'width': 40,
            'height': 40,
            'label': 'data(label)',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 8,
            'text-outline-width': 2,
            'text-outline-color': '#0a0a0f',
            'font-size': 10,
            'font-weight': 'bold',
            'color': '#e0e0e0',
            'border-width': 2,
            'border-color': '#ffffff',
            'border-opacity': 0,
            'opacity': 0.8,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-opacity': 1,
            'border-width': 3,
            'opacity': 1,
            'width': 50,
            'height': 50,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#4b5563',
            'opacity': 0.4,
            'curve-style': 'bezier',
            'target-arrow-color': '#4b5563',
            'target-arrow-shape': 'triangle',
            'target-arrow-size': 5,
          },
        },
        {
          selector: 'edge:selected',
          style: {
            'opacity': 0.8,
            'line-color': '#a855f7',
            'width': 3,
          },
        },
      ],
      layout: {
        name: 'cose',
        idealEdgeLength: 150,
        nodeOverlap: 20,
        fit: true,
        padding: 50,
        randomize: true,
        componentSpacing: 100,
        nodeRepulsion: 4000,
        edgeElasticity: 0.5,
        gravity: 0.25,
        numIter: 2000,
      },
    });

    // Handle node clicks
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const agentId = node.id();
      if (onAgentClick) {
        onAgentClick(agentId);
      }
    });

    // Highlight selected nodes
    if (selectedAgentIds.length > 0) {
      selectedAgentIds.forEach(agentId => {
        const node = cy.getElementById(agentId);
        if (node.length > 0) {
          node.select();
        }
      });
    }

    cyRef.current = cy;

    cy.ready(() => {
      setTimeout(() => {
        cy.fit(undefined, 50);
        cy.zoom(0.8);
        cy.center();
      }, 300);
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [nodes, edges, selectedAgentIds, onAgentClick]);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0"
      style={{ zIndex: 1 }}
    />
  );
}

export default AgentNetworkGraph;

