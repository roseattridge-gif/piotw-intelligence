import { CompanySearch } from "@/components/company-search";
import { searchCompanies } from "@/lib/data/companies";
import Link from "next/link";
export default async function Home() { const companies=await searchCompanies(); return <>
  <section className="hero"><div className="hero-main"><p className="eyebrow">Outside-in operational intelligence</p><h1>PUT IT ON<br/>THE WALL</h1><p className="hero-line">See the operational story hidden in public evidence.</p></div><div className="hero-entry"><p>PIOTW assembles fragmented company disclosures into a traceable view of what appears to be changing operationally—and shows the evidence behind every assessment.</p><CompanySearch companies={companies}/><Link className="truth-demo-link" href="/intelligence">Open the internal intelligence directory →</Link></div></section>
  <section className="method"><header><p className="eyebrow">How to read PIOTW</p><h2>Evidence first. Interpretation visible.</h2></header><div><article><span>01</span><h3>Evidence</h3><p>Source-grounded operational observations.</p></article><article><span>02</span><h3>Interpretation</h3><p>Conclusions linked back to supporting evidence.</p></article><article><span>03</span><h3>Prediction</h3><p>Shown only when validated model output exists.</p></article></div></section>
  </>; }
