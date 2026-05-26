import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail;

      if (status === 422) {
        console.error("Validation error:", detail);
      } else if (status === 404) {
        console.error("Resource not found:", detail);
      } else if (status >= 500) {
        console.error("Server error:", detail);
      }
    } else if (error.request) {
      console.error("Network error: no response received");
    }

    return Promise.reject(error);
  }
);

export default client;
