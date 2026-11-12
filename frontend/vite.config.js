import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Locally the API runs on :8000; the dev server forwards /api there so the browser
// sees one origin. In AWS, CloudFront serves this build and routes /api to the ALB.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
