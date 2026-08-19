import Link from "next/link";

export function SiteHeader() {
  return <header className="site-header"><Link href="/" className="wordmark"><i className="brand-bars" aria-hidden><b/><b/><b/></i><span>PUT IT ON<br/>THE WALL</span></Link><nav aria-label="Primary"><Link href="/" aria-label="Search companies">⌕</Link><span className="profile-mark" aria-hidden>RA</span></nav></header>;
}
