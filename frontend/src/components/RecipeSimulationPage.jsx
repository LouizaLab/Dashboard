import { useState, useEffect } from 'react';
import RecipeEditor from './recipe/RecipeEditor';
import SimulationControls from './recipe/SimulationControls';
import SimulationResults from './recipe/SimulationResults';
import ApprovalPanel from './recipe/ApprovalPanel';
import LPMVisualization from './recipe/LPMVisualization';
import { getRecipeVariants, runSimulation, getSimulationResults, createRecipeVariant } from '../api';

function RecipeSimulationPage() {
  const [recipeVariants, setRecipeVariants] = useState([]);
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [simulationRun, setSimulationRun] = useState(null);
  const [simulationResults, setSimulationResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingVariants, setLoadingVariants] = useState(true);
  const [error, setError] = useState(null);
  const [showRecipeEditor, setShowRecipeEditor] = useState(false);
  const [rightPanelView, setRightPanelView] = useState('approval');

  // Ensure recipeVariants is always an array
  const safeRecipeVariants = Array.isArray(recipeVariants) ? recipeVariants : [];

  useEffect(() => {
    loadRecipeVariants();
  }, []);

  const loadRecipeVariants = async () => {
    try {
      setLoadingVariants(true);
      setError(null);
      const response = await getRecipeVariants();
      console.log('Recipe variants API response:', response);
      
      // Handle different response structures
      let variants = [];
      if (Array.isArray(response.data)) {
        variants = response.data;
      } else if (response.data && Array.isArray(response.data.results)) {
        variants = response.data.results;
      } else if (Array.isArray(response)) {
        variants = response;
      } else {
        console.warn('Unexpected response structure:', response);
        variants = [];
      }
      
      setRecipeVariants(variants);
      if (variants.length > 0 && !selectedVariant) {
        setSelectedVariant(variants[0]);
      }
    } catch (error) {
      console.error('Failed to load recipe variants:', error);
      console.error('Error details:', error.response?.data || error.message);
      setError('Failed to load recipe variants. Make sure the backend is running on http://localhost:8000');
      setRecipeVariants([]);
    } finally {
      setLoadingVariants(false);
    }
  };

  const handleCreateNew = async (newVariant) => {
    await loadRecipeVariants();
    setSelectedVariant(newVariant);
    setShowRecipeEditor(false);
  };

  const handleDelete = async (variantId) => {
    await loadRecipeVariants();
    if (selectedVariant?.id === variantId) {
      setSelectedVariant(null);
    }
  };

  const handleRunSimulation = async (params) => {
    if (!selectedVariant) {
      alert('Please select a recipe variant first');
      return;
    }

    setLoading(true);
    setSimulationResults(null);
    try {
      const response = await runSimulation({
        recipe_variant_id: selectedVariant.id,
        ...params
      });
      
      setSimulationRun(response.data);
      
      // Poll for results
      const simulationRunId = response.data.simulation_run_id || response.data.id;
      if (simulationRunId) {
        pollSimulationResults(simulationRunId);
      } else {
        alert('Invalid response from server');
        setLoading(false);
      }
    } catch (error) {
      console.error('Failed to run simulation:', error);
      alert('Failed to start simulation: ' + (error.response?.data?.error || error.message));
      setLoading(false);
    }
  };

  const pollSimulationResults = async (simulationRunId) => {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await getSimulationResults(simulationRunId);
        const data = response.data;
        
        console.log('Polling simulation results:', {
          status: data.status,
          hasResults: !!data.results_json,
          hasApproval: !!data.approval_assessment_json,
          data: data
        });

        if (data.status === 'completed') {
          console.log('Simulation completed, setting results:', data);
          setSimulationResults(data);
          setLoading(false);
        } else if (data.status === 'failed') {
          alert('Simulation failed: ' + (data.error_message || 'Unknown error'));
          setLoading(false);
        } else {
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(poll, 5000); // Poll every 5 seconds
          } else {
            alert('Simulation timeout');
            setLoading(false);
          }
        }
      } catch (error) {
        console.error('Failed to poll simulation results:', error);
        console.error('Error details:', error.response?.data || error.message);
        setLoading(false);
      }
    };

    poll();
  };

  if (loadingVariants) {
    return (
      <div className="flex-1 flex items-center justify-center bg-dark-bg text-gray-200">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary mx-auto mb-4"></div>
          <div>Loading recipe variants...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full bg-dark-bg text-gray-200 overflow-hidden">
      {/* Top Bar - Simulation Controls (Prominent) */}
      <div className="bg-dark-surface border-b border-dark-border p-3 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-xl font-bold">Recipe & Launch Simulation</h1>
          <button
            onClick={() => {
              setSelectedVariant({ id: null, name: '', base_product_id: '', base_product_name: '' });
              setShowRecipeEditor(true);
            }}
            className="px-3 py-1.5 bg-accent-primary rounded hover:bg-accent-primary/80 text-sm"
          >
            + New Recipe Variant
          </button>
        </div>
        
        {selectedVariant && (
          <div className="mb-2">
            <div className="text-xs text-gray-400 mb-1">Selected Variant:</div>
            <div className="text-base font-semibold">{selectedVariant.name || 'Unnamed Variant'}</div>
          </div>
        )}

        <SimulationControls
          onRunSimulation={handleRunSimulation}
          loading={loading}
          disabled={!selectedVariant}
        />
      </div>

      {/* Main Content Area - Takes remaining height */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Left Panel - Recipe Variants List */}
        <div className="w-48 border-r border-dark-border overflow-y-auto bg-dark-surface flex-shrink-0">
          <div className="p-4">
            <h2 className="text-lg font-bold mb-4">Recipe Variants</h2>
            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded text-red-400 text-sm">
                {error}
              </div>
            )}
            {safeRecipeVariants.length === 0 && !error ? (
              <div className="text-gray-400 text-sm mb-4">
                No recipe variants found. Click "New Recipe Variant" to create one.
              </div>
            ) : (
              <div className="space-y-2">
                {safeRecipeVariants.map((variant) => (
                  <button
                    key={variant.id}
                    onClick={() => {
                      setSelectedVariant(variant);
                      setShowRecipeEditor(false);
                      setSimulationResults(null); // Clear results when switching variants
                    }}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      selectedVariant?.id === variant.id
                        ? 'border-accent-primary bg-accent-primary/10'
                        : 'border-dark-border hover:border-gray-600'
                    }`}
                  >
                    <div className="font-medium">{variant.name}</div>
                    <div className="text-sm text-gray-400">
                      {variant.base_product_name || variant.base_product_id}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Center Panel - Recipe Editor or Simulation Results */}
        <div className="flex-1 flex flex-col overflow-hidden min-w-0">
          {showRecipeEditor ? (
            <div className="flex-1 overflow-y-auto p-6">
              {selectedVariant ? (
                <div>
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-xl font-bold">Recipe Editor</h2>
                    <button
                      onClick={() => setShowRecipeEditor(false)}
                      className="px-3 py-1 text-sm bg-dark-surface border border-dark-border rounded hover:bg-dark-hover"
                    >
                      ← Back to Simulation
                    </button>
                  </div>
                  <RecipeEditor
                    variant={selectedVariant}
                    onVariantChange={(updated) => {
                      setSelectedVariant(updated);
                      loadRecipeVariants();
                      setShowRecipeEditor(false);
                    }}
                    onDelete={handleDelete}
                    onCreateNew={handleCreateNew}
                  />
                </div>
              ) : (
                <div className="text-center text-gray-400 py-12">
                  <p className="mb-4">Select a recipe variant or create a new one to get started</p>
                  <button
                    onClick={() => {
                      setSelectedVariant({ id: null, name: '', base_product_id: '', base_product_name: '' });
                      setShowRecipeEditor(true);
                    }}
                    className="px-6 py-3 bg-accent-primary rounded hover:bg-accent-primary/80"
                  >
                    Create New Recipe Variant
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-6">
              {simulationResults ? (
                <div>
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-xl font-bold">LPM Simulation Results</h2>
                    <button
                      onClick={() => setShowRecipeEditor(true)}
                      className="px-3 py-1 text-sm bg-dark-surface border border-dark-border rounded hover:bg-dark-hover"
                    >
                      Edit Recipe →
                    </button>
                  </div>
                  <SimulationResults results={simulationResults} />
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  {loading ? (
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary mx-auto mb-4"></div>
                      <div className="text-lg font-semibold mb-2">Running LPM Simulation</div>
                      <div className="text-sm">Simulating large population with Phase 3-4 behavioral dynamics...</div>
                      <div className="text-xs mt-2 text-gray-500">This may take a moment for large populations</div>
                    </div>
                  ) : selectedVariant ? (
                    <div className="text-center max-w-md">
                      <div className="text-6xl mb-4">🎯</div>
                      <div className="text-2xl font-semibold mb-2">Ready to Simulate</div>
                      <div className="text-sm text-gray-400 mb-4">
                        Configure simulation parameters above and click "Run LPM Simulation" to see how your recipe changes affect the population
                      </div>
                      <button
                        onClick={() => setShowRecipeEditor(true)}
                        className="px-4 py-2 bg-dark-surface border border-dark-border rounded hover:bg-dark-hover"
                      >
                        Edit Recipe Variant
                      </button>
                    </div>
                  ) : (
                    <div className="text-center text-gray-400 py-12">
                      <p className="mb-4">Select a recipe variant or create a new one to get started</p>
                      <button
                        onClick={() => {
                          setSelectedVariant({ id: null, name: '', base_product_id: '', base_product_name: '' });
                          setShowRecipeEditor(true);
                        }}
                        className="px-6 py-3 bg-accent-primary rounded hover:bg-accent-primary/80"
                      >
                        Create New Recipe Variant
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Panel - Split into two sections - Takes up remaining space to fill screen */}
        <div className="flex-1 min-w-[600px] border-l border-dark-border bg-dark-surface flex flex-col overflow-hidden flex-shrink-0">
          {/* Tabs for switching between views */}
          <div className="flex border-b border-dark-border">
            <button
              onClick={() => setRightPanelView('approval')}
              className={`flex-1 px-4 py-2 text-sm font-medium ${
                rightPanelView === 'approval'
                  ? 'border-b-2 border-accent-primary text-accent-primary bg-dark-surface'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Approval
            </button>
            <button
              onClick={() => setRightPanelView('lpm')}
              className={`flex-1 px-4 py-2 text-sm font-medium ${
                rightPanelView === 'lpm'
                  ? 'border-b-2 border-accent-primary text-accent-primary bg-dark-surface'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              LPM Visualization
            </button>
          </div>
          
          <div className="flex-1 overflow-hidden">
            {rightPanelView === 'approval' ? (
              simulationResults ? (
                <ApprovalPanel simulationResults={simulationResults} />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 text-sm p-4">
                  Complete a simulation to see approval assessment
                </div>
              )
            ) : (
              <LPMVisualization 
                simulationResults={simulationResults} 
                recipeVariant={selectedVariant}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default RecipeSimulationPage;
