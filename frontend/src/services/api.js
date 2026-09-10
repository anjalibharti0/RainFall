import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export const fetchForecast = async (date, leadTime = 24) => {
  const { data } = await api.get('/forecast/process', {
    params: { date, lead_time: leadTime, model_source: 'GFS' },
  });
  return data;
};

export const fetchRegime = async (date, leadTime = 24) => {
  const { data } = await api.get(`/regime/classify/${date}`, {
    params: { lead_time: leadTime },
  });
  return data;
};

export const fetchDistrictForecast = async (districtId, date, leadTime = 24) => {
  const { data } = await api.get(`/forecast/district/${districtId}`, {
    params: { date, lead_time: leadTime },
  });
  return data;
};

export const fetchProbabilityMap = async (date, leadTime = 24) => {
  const { data } = await api.get(`/probability/map/${date}`, {
    params: { lead_time: leadTime },
  });
  return data;
};

export const fetchVerificationReport = async (date, leadTime = 24) => {
  const { data } = await api.get(`/verification/report/${date}`, {
    params: { lead_time: leadTime },
  });
  return data;
};

export const fetchForecastTable = async (date, leadTime = 24) => {
  const { data } = await api.get('/forecast/table/${date}', {
    params: { date, lead_time: leadTime },
  });
  return data;
};

export default api;
