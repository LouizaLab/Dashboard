import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

function NetworkBackground({ nodes, edges }) {
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
            'background-color': '#2a2a3a',
            'width': 30,
            'height': 30,
            'opacity': 0.2,
            'border-width': 0,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 1,
            'line-color': '#2a2a3a',
            'opacity': 0.1,
            'curve-style': 'bezier',
          },
        },
      ],
      layout: {
        name: 'cose',
        idealEdgeLength: 200,
        nodeOverlap: 20,
        fit: true,
        padding: 50,
        randomize: true,
        componentSpacing: 150,
        nodeRepulsion: 5000,
        edgeElasticity: 0.5,
        gravity: 0.2,
        numIter: 2000,
      },
    });

    cyRef.current = cy;

    cy.ready(() => {
      setTimeout(() => {
        cy.fit(undefined, 50);
        cy.zoom(0.6);
        cy.center();
      }, 300);
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [nodes, edges]);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 opacity-30"
      style={{ pointerEvents: 'none' }}
    />
  );
}

export default NetworkBackground;

