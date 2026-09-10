import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Main forecast endpoint - uses ML-corrected data
export const fetchForecast = async (date, leadTime = 24) => {
  const { data } = await api.get('/forecast', {
    params: { date, lead_time: leadTime },
  });
  return data;
};

// Verification report
export const fetchVerificationReport = async (date, leadTime = 24) => {
  const { data } = await api.get('/verification', {
    params: { date, lead_time: leadTime },
  });
  return data;
};

// IMD Real-time warnings
export const fetchIMDWarnings = async () => {
  const { data } = await api.get('/imd/warnings');
  return data;
};

// IMD Real-time rainfall
export const fetchIMDRainfall = async () => {
  const { data } = await api.get('/imd/rainfall');
  return data;
};

// IMD AWS station data
export const fetchIMDAWS = async (stateId = null) => {
  const { data } = await api.get('/imd/aws', {
    params: stateId ? { state_id: stateId } : {},
  });
  return data;
};

// IMD warning codes reference
export const fetchWarningCodes = async () => {
  const { data } = await api.get('/warning/codes');
  return data;
};

export default api;
