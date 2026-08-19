import { createHash } from "node:crypto";

type EstateSource={id:string;entity:string;title:string;url:string;publicationDate:string;evidenceSpan:string;hash:string};
const sourceRows:Omit<EstateSource,"hash">[]=[
 {id:"tp-2023",entity:"Travis Perkins Merchanting",title:"2023 full-year results",url:"https://www.travisperkinsplc.co.uk/news-and-media/press-releases/2024/full-year-results-2023/",publicationDate:"2024-03-05",evidenceSpan:"Merchanting ... Revenue £4,036m ... Branch network 769; 2022 branch network 767"},
 {id:"tp-2024",entity:"Travis Perkins Merchanting",title:"2024 full-year branch table",url:"https://www.travisperkinsplc.co.uk/media/bkwlo2vx/travis-perkins-plc-2024-full-year-results-presentation.pdf",publicationDate:"2025-04-01",evidenceSpan:"Merchanting 769; Openings 6; Closures (51); 31 Dec 2024 724"},
 {id:"tp-2024-impairment",entity:"Travis Perkins Merchanting",title:"2024 branch impairment review",url:"https://www.investegate.co.uk/announcement/eqs/travis-perkins--tpk/travis-perkins-plc-full-year-results-for-th-/8806937",publicationDate:"2025-04-01",evidenceSpan:"identified 209 Merchanting branches where the carrying value ... was above ... discounted future cash flows"},
 {id:"tp-2025",entity:"Travis Perkins Merchanting",title:"2025 annual report",url:"https://www.travisperkinsplc.co.uk/media/5rgdwalx/travis-perkins-annual-report-2025.pdf",publicationDate:"2026-03-17",evidenceSpan:"Merchanting branches 724; openings 4; closures (1); 727 ... Revenue £3,722m"},
 {id:"tp-property",entity:"Travis Perkins plc",title:"2025 annual report — property",url:"https://www.travisperkinsplc.co.uk/media/5rgdwalx/travis-perkins-annual-report-2025.pdf",publicationDate:"2026-03-17",evidenceSpan:"property profits of £10m ... £51m of cash proceeds; 2024 property profits £11m with £62m cash proceeds"},
 {id:"peer-howdens",entity:"Howden Joinery UK",title:"Howdens 2025 annual report",url:"https://www.howdenjoinerygroupplc.com/docs/librariesprovider25/archives/annual-reports/2025-annual-report.pdf",publicationDate:"2026-03-05",evidenceSpan:"2025 970; 2024 947 ... ended 2025 with 22 more depots in the UK"},
 {id:"peer-grafton",entity:"Grafton Great Britain",title:"Grafton 2025 annual report",url:"https://www.graftonplc.com/~/media/Files/G/Grafton-Group/2026%20AGM/Grafton-Annual-Report-2025.pdf",publicationDate:"2026-03-05",evidenceSpan:"Great Britain Number of branches/stores 122; 2024: 122; Revenue £765.4m; 2024 £767.0m"},
 {id:"peer-lords",entity:"Lords Merchanting",title:"Lords 2025 final results",url:"https://www.investegate.co.uk/announcement/rns/lords-group-trading--lord/final-results-/9576520",publicationDate:"2026-05-01",evidenceSpan:"Three new branch openings during the year ... 32 locations in the UK"},
 {id:"peer-sig",entity:"SIG plc",title:"SIG 2024 results",url:"https://www.investegate.co.uk/announcement/rns/sig--shi/full-year-results-for-year-ended-31-december-2024/8763481",publicationDate:"2025-03-05",evidenceSpan:"closure of 17 underperforming branches ... c.430 European sites"},
];
export const estateSources:EstateSource[]=sourceRows.map(s=>({...s,hash:createHash("sha256").update(s.evidenceSpan).digest("hex")}));

export const tpEstateHistory=[
 {year:2022,branches:767,openings:null,closures:null,net:null,revenue:4220,revenuePerBranch:5.50,coverage:"COUNT_AND_REVENUE"},
 {year:2023,branches:769,openings:null,closures:null,net:2,revenue:4036,revenuePerBranch:5.25,coverage:"COUNT_AND_REVENUE"},
 {year:2024,branches:724,openings:6,closures:51,net:-45,revenue:3786,revenuePerBranch:5.23,coverage:"COMPLETE_MOVEMENT"},
 {year:2025,branches:727,openings:4,closures:1,net:3,revenue:3722,revenuePerBranch:5.12,coverage:"COMPLETE_MOVEMENT"},
];

export const peerCohort=[
 {company:"Travis Perkins Merchanting",model:"National general + specialist merchant",start:724,end:727,netRate:0.41,eligible:true,sourceId:"tp-2025"},
 {company:"Grafton Great Britain",model:"Trade distribution plus adjacent manufacturing",start:122,end:122,netRate:0,eligible:true,sourceId:"peer-grafton"},
 {company:"Howdens UK",model:"Trade-only kitchen/joinery depot network",start:869,end:891,netRate:2.53,eligible:true,sourceId:"peer-howdens"},
 {company:"Lords Merchanting",model:"Regional building-material merchant",start:29,end:32,netRate:10.34,eligible:true,sourceId:"peer-lords"},
 {company:"SIG UK",model:"Specialist interiors/roofing distributor",start:null,end:170,netRate:null,eligible:false,sourceId:"peer-sig"},
];
export const peerMedian=2.53;
export const tpPeerGap=-2.12;

export const benchmarkFeatures=[
 {name:"2024 net estate change",tp:"−5.85%",peer:"WITHHELD",position:"No same-window 3-peer minimum",meaning:"Sharp one-year portfolio reset, dominated by standalone Benchmarx closures."},
 {name:"2025 net estate change",tp:"+0.41%",peer:"+2.53% median",position:"2.12ppt below peer median · 33rd percentile of 4",meaning:"Footprint stabilised, but expansion remained slower than the matched development cohort."},
 {name:"Revenue per Merchanting branch proxy",tp:"£5.50m → £5.12m (2022–25)",peer:"WITHHELD",position:"−6.9% over three years",meaning:"The network reset did not produce an observable recovery in this coarse productivity proxy."},
 {name:"Branches flagged by impairment review",tp:"209 / 724 · 28.9%",peer:"WITHHELD",position:"No comparable peer disclosure",meaning:"A large review population warrants branch-level diligence; impairment is not the same as negative contribution."},
];

export const valueScenarios=[
 {label:"Low",value:"£28m",formula:"£56.5m × 50%",assumption:"Half of the two-year average property cash proceeds repeats"},
 {label:"Base",value:"£42m",formula:"£56.5m × 75%",assumption:"Three quarters of the two-year average repeats"},
 {label:"High",value:"£57m",formula:"£56.5m × 100%",assumption:"The two-year average repeats"},
];

export const diligenceQuestions=[
 "How many of the 209 impaired branches are below branch-level cash contribution after central allocations?",
 "What customer-retention and delivery-radius tests govern consolidation or relocation decisions?",
 "Why did revenue per branch continue to decline after the 2024 closures, and how much is cyclical versus execution-driven?",
 "Which freeholds can release capital without weakening local density, service or optionality?",
 "What productivity uplift has been achieved at new destination-format and relocated branches versus their predecessors?",
];

export const falsifiers=[
 "Branch-level contribution and local market share show the impaired population is economically healthy through-cycle.",
 "Relocated/new formats do not outperform predecessor sites after maturity.",
 "The peer gap disappears after controlling for format, customer mix and geography.",
 "Property disposals would reduce service density or create offsetting lease costs greater than proceeds." 
];
