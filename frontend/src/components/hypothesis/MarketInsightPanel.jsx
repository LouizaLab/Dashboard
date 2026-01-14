import { useState, useEffect } from 'react';
import MarketManifold3D from '../market-insight/MarketManifold3D';
import InsightWorkspace from '../market-insight/InsightWorkspace';

function MarketInsightPanel({ filters }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [pinnedNodes, setPinnedNodes] = useState([]);
  const [nodeDetails, setNodeDetails] = useState(null);
  const [vertical, setVertical] = useState('beauty');
  const [region, setRegion] = useState('US');
  const [scenarioResults, setScenarioResults] = useState(null);

  const handleNodeClick = async (node) => {
    setSelectedNode(node);
    
    // Load node details
    try {
      const response = await fetch(
        `http://localhost:8000/api/market-insight-new/node/${node.type}/${node.id}/`
      );
      if (response.ok) {
        const data = await response.json();
        setNodeDetails(data);
      }
    } catch (error) {
      console.error('Failed to load node details:', error);
    }
  };

  const handlePinNode = (node) => {
    if (!pinnedNodes.find(n => n.id === node.id)) {
      setPinnedNodes([...pinnedNodes, node]);
    }
  };

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Left Panel: Market Manifold Map (40%) */}
      <div className="w-[40%] flex flex-col border-r border-dark-border bg-dark-bg">
        <div className="p-4 border-b border-dark-border bg-dark-surface">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xl font-bold text-gray-200">Market Manifold</h2>
            <div className="flex items-center gap-4">
              <select
                className="bg-dark-bg border border-dark-border rounded px-2 py-1 text-sm text-gray-300"
                value={vertical}
                onChange={(e) => setVertical(e.target.value)}
              >
                <option value="beauty">Beauty</option>
                <option value="food">Food</option>
              </select>
              <select
                className="bg-dark-bg border border-dark-border rounded px-2 py-1 text-sm text-gray-300"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
              >
                <option value="US">US</option>
              </select>
            </div>
          </div>
        </div>
        
        <div className="flex-1 overflow-hidden">
          <MarketManifold3D
            vertical={vertical}
            region={region}
            onNodeClick={handleNodeClick}
            selectedNodes={selectedNode ? [selectedNode.id] : []}
            scenarioResults={scenarioResults}
          />
        </div>

        {/* Node Detail Drawer */}
        {nodeDetails && (
          <div className="border-t border-dark-border bg-dark-surface p-4 max-h-[300px] overflow-y-auto">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold text-gray-200">{nodeDetails.name}</h3>
              <button
                onClick={() => {
                  setNodeDetails(null);
                  setSelectedNode(null);
                }}
                className="text-gray-400 hover:text-gray-200"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-2 text-sm text-gray-300">
              {nodeDetails.category && (
                <div>
                  <span className="text-gray-400">Category:</span> {nodeDetails.category}
                  {nodeDetails.sub_category && ` / ${nodeDetails.sub_category}`}
                </div>
              )}
              {nodeDetails.price_tier && (
                <div>
                  <span className="text-gray-400">Price Tier:</span> {nodeDetails.price_tier}
                </div>
              )}
              {nodeDetails.brand_type && (
                <div>
                  <span className="text-gray-400">Brand Type:</span> {nodeDetails.brand_type}
                </div>
              )}
              {nodeDetails.signals && nodeDetails.signals.length > 0 && (
                <div>
                  <span className="text-gray-400">Recent Momentum:</span>{' '}
                  {nodeDetails.signals[0]?.trend_momentum?.toFixed(2) || 'N/A'}
                </div>
              )}
              {nodeDetails.innovation_events && nodeDetails.innovation_events.length > 0 && (
                <div>
                  <span className="text-gray-400">Recent Innovation:</span>{' '}
                  {nodeDetails.innovation_events[0]?.event_type} ({nodeDetails.innovation_events.length} total)
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right Panel: Insight Workspace (60%) */}
      <div className="w-[60%] flex flex-col bg-dark-bg">
        <InsightWorkspace
          pinnedNodes={pinnedNodes}
          onAsk={(results) => {
            console.log('Insight results:', results);
          }}
          onScenarioResults={(scenarioResults) => {
            setScenarioResults(scenarioResults);
          }}
        />
      </div>
    </div>
  );
}

export default MarketInsightPanel;
