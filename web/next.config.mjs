/** @type {import('next').NextConfig} */
const nextConfig = {
  // API routes at /app/api/* proxy to the Python FastAPI backend.
  // Set PYTHON_API_URL in .env.local to point to your backend.
  // Default: http://localhost:8000
};

export default nextConfig;

