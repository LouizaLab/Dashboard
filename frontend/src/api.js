import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getCompanies = () => api.get('/companies/');
export const getCompany = (id) => api.get(`/companies/${id}/`);
export const getCompanyTimeseries = (id, metric, start, end) => {
  const params = { metric };
  if (start) params.start = start;
  if (end) params.end = end;
  return api.get(`/companies/${id}/timeseries/`, { params });
};

export const getNetwork = (view = 'Market Insight', filters = {}) => {
  const params = { view };
  Object.keys(filters).forEach(key => {
    if (filters[key]) params[key] = filters[key];
  });
  return api.get('/network/', { params });
};

export const getEdge = (id) => api.get(`/edges/${id}/`);

export const compareCompanies = (companyAId, companyBId, metric = 'foot_traffic') => {
  return api.get('/compare/', {
    params: { a: companyAId, b: companyBId, metric },
  });
};

// Hypothesis and Report Generation APIs
export const runHypothesis = (data) => api.post('/hypothesis/run/', data);
export const listHypothesisRuns = () => api.get('/hypothesis/');
export const getHypothesisRun = (runId) => api.get(`/hypothesis/${runId}/`);
export const generateReportForRun = (runId) => api.post(`/hypothesis/${runId}/generate_report/`);
export const generateStandaloneReport = (data) => api.post('/hypothesis/generate_standalone_report/', data);

// Recipe Simulation APIs
export const getRecipeVariants = () => api.get('/recipe/variants/');
export const getRecipeVariant = (id) => api.get(`/recipe/variants/${id}/`);
export const createRecipeVariant = (data) => api.post('/recipe/variants/', data);
export const updateRecipeVariant = (id, data) => api.patch(`/recipe/variants/${id}/`, data);
export const deleteRecipeVariant = (id) => api.delete(`/recipe/variants/${id}/`);

export const getApprovalPersonas = () => api.get('/recipe/personas/');
export const getApprovalPersona = (id) => api.get(`/recipe/personas/${id}/`);

export const runSimulation = (data) => api.post('/recipe/simulations/run_simulation/', data);
export const getSimulationResults = (simulationRunId) => api.get(`/recipe/simulations/${simulationRunId}/`);
export const getSimulationRun = (simulationRunId) => api.get(`/recipe/simulations/${simulationRunId}/`);
export const generateFocusGroup = (simulationRunId) => api.post(`/recipe/simulations/${simulationRunId}/generate_focus_group/`);
export const generateSurvey = (simulationRunId) => api.post(`/recipe/simulations/${simulationRunId}/generate_survey/`);
export const generateReadinessReport = (simulationRunId) => api.post(`/recipe/simulations/${simulationRunId}/generate_readiness_report/`);

export default api;

