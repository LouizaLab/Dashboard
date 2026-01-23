import { useState, useEffect } from 'react';
import TopNavigation from './components/TopNavigation';
import Sidebar from './components/Sidebar';
import NetworkGraph from './components/NetworkGraph';
import DetailDrawer from './components/DetailDrawer';
import HypothesisPage from './components/HypothesisPage';
import RecipeSimulationPage from './components/RecipeSimulationPage';
import MarketInsightManifoldPage from './pages/MarketInsightManifoldPage';
import { getNetwork, getCompany, getEdge } from './api';

function App() {
  const [activeTab, setActiveTab] = useState('TEST HYPOTHESIS');
  const [viewType, setViewType] = useState('Market Insight');
  const [filters, setFilters] = useState({
    age_bucket: '',
    income: '',
    region: '',
  });
  const [networkData, setNetworkData] = useState({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNetworkData();
  }, [viewType, filters]);

  const loadNetworkData = async () => {
    try {
      setLoading(true);
      const response = await getNetwork(viewType, filters);
      console.log('Network API response:', response.data);
      console.log('Nodes:', response.data.nodes);
      console.log('Edges:', response.data.edges);
      setNetworkData(response.data);
    } catch (error) {
      console.error('Failed to load network data:', error);
      console.error('Error details:', error.response?.data || error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = async (nodeId) => {
    try {
      const response = await getCompany(nodeId);
      setSelectedNode(response.data);
      setSelectedEdge(null);
      setDrawerOpen(true);
    } catch (error) {
      console.error('Failed to load company:', error);
    }
  };

  const handleEdgeClick = async (edgeData) => {
    try {
      // Extract edge ID from cytoscape data
      const edgeId = edgeData.id?.replace('e', '');
      if (edgeId) {
        const response = await getEdge(edgeId);
        setSelectedEdge({ ...response.data, cytoscapeData: edgeData });
        setSelectedNode(null);
        setDrawerOpen(true);
      }
    } catch (error) {
      console.error('Failed to load edge:', error);
    }
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    setSelectedNode(null);
    setSelectedEdge(null);
  };

  return (
    <div className="flex flex-col h-screen bg-dark-bg text-gray-200">
      <TopNavigation activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="flex flex-1 overflow-hidden">
        {activeTab === 'NETWORK GRAPH' && (
          <>
            <Sidebar
              viewType={viewType}
              setViewType={setViewType}
              filters={filters}
              setFilters={setFilters}
            />

            <div className="flex-1 flex flex-col relative">
              <div className="flex-1 relative" style={{ minHeight: 0 }}>
                {loading ? (
                  <div className="absolute inset-0 flex items-center justify-center z-20">
                    <div className="text-gray-300">Loading network...</div>
                  </div>
                ) : (
                  <NetworkGraph
                    nodes={networkData.nodes || []}
                    edges={networkData.edges || []}
                    onNodeClick={handleNodeClick}
                    onEdgeClick={handleEdgeClick}
                    viewType={viewType}
                  />
                )}
              </div>
            </div>

            <DetailDrawer
              isOpen={drawerOpen}
              onClose={handleCloseDrawer}
              node={selectedNode}
              edge={selectedEdge}
              networkData={networkData}
            />
          </>
        )}

        {activeTab === 'TEST HYPOTHESIS' && (
          <HypothesisPage />
        )}

        {activeTab === 'TASTE SNAPSHOT' && (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-4">Taste Snapshot</h2>
              <p className="text-gray-400">Taste analysis dashboard coming soon...</p>
            </div>
          </div>
        )}

        {activeTab === 'BEHAVIORAL DYNAMICS' && (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-4">Behavioral Dynamics</h2>
              <p className="text-gray-400">Behavioral dynamics visualization coming soon...</p>
            </div>
          </div>
        )}

        {activeTab === 'INSIGHTS' && (
          <MarketInsightManifoldPage />
        )}

        {activeTab === 'WHAT-IF SIMULATION' && (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-4">What-If Simulation</h2>
              <p className="text-gray-400">Simulation interface coming soon...</p>
            </div>
          </div>
        )}

        {activeTab === 'RECIPE & LAUNCH SIMULATION' && (
          <RecipeSimulationPage />
        )}
      </div>
    </div>
  );
}

export default App;
