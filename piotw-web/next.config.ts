import type { NextConfig } from "next";

const githubPagesBasePath =
  process.env.GITHUB_ACTIONS === "true" ? "/piotw-intelligence" : "";

const nextConfig: NextConfig = {
  outputFileTracingRoot: process.cwd(),
  output: "export",
  basePath: githubPagesBasePath,
  assetPrefix: githubPagesBasePath || undefined,
  trailingSlash: true,
};
export default nextConfig;
