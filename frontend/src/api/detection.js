import axios from 'axios';

const baseURL = 'http://localhost:8000/api';

const request = axios.create({
  baseURL,
  timeout: 60000,
});

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

request.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const detectFrame = (data) => {
  return request({
    url: '/camera/detect',
    method: 'post',
    data,
  });
};

export const startCameraDetection = (data) => {
  return request({
    url: '/camera/start',
    method: 'post',
    data,
  });
};

export const stopCameraDetection = () => {
  return request({
    url: '/camera/stop',
    method: 'post',
  });
};

export const pauseCameraDetection = () => {
  return request({
    url: '/camera/pause',
    method: 'post',
  });
};

export const resumeCameraDetection = () => {
  return request({
    url: '/camera/resume',
    method: 'post',
  });
};

export const getCameraStatus = () => {
  return request({
    url: '/camera/status',
    method: 'get',
  });
};

export const detectSingle = (formData) => {
  return request({
    url: '/inference/single',
    method: 'post',
    data: formData,
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const detectBatch = (formData) => {
  return request({
    url: '/inference/batch',
    method: 'post',
    data: formData,
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const detectVideo = (formData) => {
  return request({
    url: '/inference/video',
    method: 'post',
    data: formData,
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const getHistoryList = (params) => {
  return request({
    url: '/history/list',
    method: 'get',
    params,
  });
};

export const getHistoryDetail = (recordId) => {
  return request({
    url: `/history/detail/${recordId}`,
    method: 'get',
  });
};

export const deleteHistory = (recordId) => {
  return request({
    url: `/history/${recordId}`,
    method: 'delete',
  });
};

export const chatCompletion = (messages) => {
  return request({
    url: '/chat/completion',
    method: 'post',
    data: { messages },
    timeout: 60000,
  });
};

export default request;