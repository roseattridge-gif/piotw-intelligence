export function generateStaticParams() {
  return ["travis-perkins", "cloudflare", "datadog", "kingfisher-screwfix-ukie"].map(companyId => ({ companyId }));
}

export default function CompanyIntelligenceLayout({ children }: { children: React.ReactNode }) {
  return children;
}
