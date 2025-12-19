import { useState, useEffect } from 'react';
import LeftFilters from './hypothesis/LeftFilters';
import HypothesisInput from './hypothesis/HypothesisInput';
import ResultsPanel from './hypothesis/ResultsPanel';
import AgentDrawer from './hypothesis/AgentDrawer';
import AgentNetworkGraph from './hypothesis/AgentNetworkGraph';

function HypothesisPage() {
  const [filters, setFilters] = useState({
    year: 2025,
    view: 'Hypothesis Test',
    age_bucket: '',
    gender: '',
    region: '',
    income: '',
    archetype: '',
    agent_count: 100,
    use_gpt: false,
  });
  
  const [agentNetworkData, setAgentNetworkData] = useState({ nodes: [], edges: [] });
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedAgentIds, setSelectedAgentIds] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    // Load agent network data
    loadAgentNetwork();
  }, [filters.age_bucket, filters.gender, filters.region, filters.income, filters.archetype]);

  const loadAgentNetwork = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.age_bucket) params.append('age_bucket', filters.age_bucket);
      if (filters.gender) params.append('gender', filters.gender);
      if (filters.region) params.append('region', filters.region);
      if (filters.income) params.append('income', filters.income);
      if (filters.archetype) params.append('archetype', filters.archetype);
      params.append('limit', filters.agent_count.toString());
      
      const response = await fetch(`http://localhost:8000/api/agents/network/?${params}`);
      const data = await response.json();
      setAgentNetworkData(data);
    } catch (error) {
      console.error('Failed to load agent network:', error);
    }
  };

  const handleAgentClick = async (agentId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/agents/${agentId}/`);
      const data = await response.json();
      setSelectedAgent(data);
      setDrawerOpen(true);
      
      // Add to selected agents list
      if (!selectedAgentIds.includes(agentId)) {
        setSelectedAgentIds([...selectedAgentIds, agentId]);
      }
    } catch (error) {
      console.error('Failed to load agent:', error);
    }
  };

  const handleRunHypothesis = async (inputText) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/hypothesis/run/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input_text: inputText,
          filters: {
            age_bucket: filters.age_bucket || null,
            gender: filters.gender || null,
            region: filters.region || null,
            income: filters.income || null,
            archetype: filters.archetype || null,
          },
          agent_ids: selectedAgentIds.length > 0 ? selectedAgentIds : null, // Use selected agents if any
          agent_count: filters.agent_count,
          mode: filters.use_gpt ? 'gpt' : 'mock',
        }),
      });
      
      const data = await response.json();
      setResults(data);
      
      // Update selected agent IDs from results
      if (data.agent_ids) {
        setSelectedAgentIds(data.agent_ids);
      }
    } catch (error) {
      console.error('Failed to run hypothesis:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAgentSelect = (agent) => {
    setSelectedAgent(agent);
    setDrawerOpen(true);
    // Add agent ID to selected list
    if (agent.id && !selectedAgentIds.includes(agent.id)) {
      setSelectedAgentIds([...selectedAgentIds, agent.id]);
    }
  };

  return (
    <div className="flex flex-1 overflow-hidden relative">
      <LeftFilters filters={filters} setFilters={setFilters} />
      
      <div className="flex-1 flex flex-col relative">
        {/* Agent Network Graph */}
        <AgentNetworkGraph
          nodes={agentNetworkData.nodes || []}
          edges={agentNetworkData.edges || []}
          onAgentClick={handleAgentClick}
          selectedAgentIds={selectedAgentIds}
        />
        
        {/* Hypothesis Input and Results Overlay */}
        <div className="flex-1 flex flex-col relative z-10 p-8 pointer-events-none">
          <div className="max-w-4xl mx-auto w-full space-y-6 pointer-events-auto">
            <div className="bg-dark-surface/95 backdrop-blur-sm border border-dark-border rounded-xl p-4 shadow-xl">
              <HypothesisInput
                onRun={handleRunHypothesis}
                loading={loading}
              />
            </div>
            
            {results && (
              <div className="bg-dark-surface/95 backdrop-blur-sm border border-dark-border rounded-xl p-6 shadow-xl">
                <ResultsPanel
                  results={results}
                  onAgentSelect={handleAgentSelect}
                />
              </div>
            )}
          </div>
        </div>
      </div>
      
      <AgentDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        agent={selectedAgent}
        filters={filters}
      />
    </div>
  );
}

export default HypothesisPage;

