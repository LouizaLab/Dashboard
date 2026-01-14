import { useState, useEffect } from 'react';
import LeftFilters from './hypothesis/LeftFilters';
import HypothesisInput from './hypothesis/HypothesisInput';
import ResultsPanel from './hypothesis/ResultsPanel';
import AgentDrawer from './hypothesis/AgentDrawer';
import AgentGrid from './hypothesis/AgentGrid';

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
  });

  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedAgentIds, setSelectedAgentIds] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    // Load agents
    loadAgents();
  }, [filters.age_bucket, filters.gender, filters.region, filters.income, filters.archetype, filters.agent_count]);

  const loadAgents = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.age_bucket) params.append('age_bucket', filters.age_bucket);
      if (filters.gender) params.append('gender', filters.gender);
      if (filters.region) params.append('region', filters.region);
      if (filters.income) params.append('income', filters.income);
      if (filters.archetype) params.append('archetype', filters.archetype);
      params.append('limit', filters.agent_count.toString());

      const response = await fetch(`http://localhost:8000/api/agents/?${params}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      const agentsList = Array.isArray(data) ? data : (data.results || []);
      console.log('Loaded agents:', agentsList.length, 'agents');
      // Ensure all agents have id field
      agentsList.forEach(agent => {
        if (!agent.id) {
          console.warn('Agent missing id:', agent);
        }
      });
      setAgents(agentsList);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const handleAgentClick = async (agentId) => {
    try {
      console.log('Loading agent with ID:', agentId);
      const response = await fetch(`http://localhost:8000/api/agents/${agentId}/`);

      if (!response.ok) {
        if (response.status === 404) {
          console.error(`Agent ${agentId} not found (404)`);
          // Try to find agent in local list
          const localAgent = agents.find(a => a.id === agentId);
          if (localAgent) {
            console.log('Using local agent data:', localAgent);
            setSelectedAgent(localAgent);
            setDrawerOpen(true);
            return;
          }
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Loaded agent data:', data);

      if (!data.id) {
        console.warn('Agent data missing id field:', data);
        data.id = agentId; // Set id from the URL parameter
      }

      setSelectedAgent(data);
      setDrawerOpen(true);

      // Toggle selection (add if not selected, remove if selected)
      if (selectedAgentIds.includes(agentId)) {
        setSelectedAgentIds(selectedAgentIds.filter(id => id !== agentId));
      } else {
        setSelectedAgentIds([...selectedAgentIds, agentId]);
      }
    } catch (error) {
      console.error('Failed to load agent:', error);
      // Try to use agent from local list as fallback
      const localAgent = agents.find(a => a.id === agentId);
      if (localAgent) {
        console.log('Using local agent as fallback:', localAgent);
        setSelectedAgent(localAgent);
        setDrawerOpen(true);
      }
    }
  };

  const handleClearSelection = () => {
    setSelectedAgentIds([]);
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
          mode: 'gpt', // Always use GPT
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

      <div className={`flex-1 flex flex-col relative ${results ? 'mr-0' : ''}`}>
        {/* Hypothesis Input */}
        <div className="p-6 border-b border-dark-border">
            <HypothesisInput
              onRun={handleRunHypothesis}
              loading={loading}
            />
        </div>

        {/* Agent Grid */}
        <div className="flex-1 overflow-hidden p-6">
          <div className="h-full">
            <AgentGrid
              agents={agents}
              onAgentClick={handleAgentClick}
              selectedAgentIds={selectedAgentIds}
              onClearSelection={handleClearSelection}
            />
          </div>
        </div>
      </div>

      {/* Results Panel - Right Sidebar */}
      {results && (
        <div className="w-1/3 border-l border-dark-border bg-dark-bg flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto">
            <div className="p-6">
              <ResultsPanel
                results={results}
                onAgentSelect={handleAgentSelect}
              />
            </div>
          </div>
        </div>
      )}

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
