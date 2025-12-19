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

export default api;

