import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';
const api = axios.create({ baseURL: API_BASE, timeout: 30000 });

export const fetchForecast = async (date, leadTime = 24) => {
  const { data } = await api.get('/forecast/process', { params: { date, lead_time: leadTime } });
  return data;
};

export const fetchVerificationReport = async (date, leadTime = 24) => {
  const { data } = await api.get('/verification/report/' + date, { params: { lead_time: leadTime } });
  return data;
};

export const fetchDistricts = async (date = '2026-09-10') => {
  const { data } = await api.get('/forecast/table/' + date, { params: { lead_time: 24 } });
  return data;
};

export const fetchDistrictSearch = async (query, date = '2026-09-10') => {
  const { data } = await api.get('/forecast/table/' + date, { params: { lead_time: 24 } });
  const districts = data.districts || [];
  const ql = query.toLowerCase();
  return {
    results: districts
      .filter(d => d.name?.toLowerCase().includes(ql) || d.state?.toLowerCase().includes(ql))
      .slice(0, 50)
  };
};

export default api;
