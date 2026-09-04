import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  outputFileTracingRoot: process.cwd(),
  output: "export",
  trailingSlash: true,
};
export default nextConfig;
