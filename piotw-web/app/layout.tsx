import type { Metadata } from "next";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";
export const metadata: Metadata = { title: "PIOTW — Outside-in operational intelligence", description: "See the operational story hidden in public evidence." };
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="en"><body><SiteHeader/><main>{children}</main><footer className="site-footer"><span><i className="brand-bars" aria-hidden><b/><b/><b/></i> PUT IT ON THE WALL</span><span>Outside-in operational intelligence · Development interface</span></footer></body></html>; }
