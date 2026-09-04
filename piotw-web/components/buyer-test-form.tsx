"use client";
import { useState } from "react";

export function BuyerTestForm({ questions }: { questions: string[] }) { const [saved, setSaved] = useState(false); return <form className="op-buyer-form" onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); localStorage.setItem("piotw-buyer-test-v01", JSON.stringify(Object.fromEntries(form))); setSaved(true); }}><p>Responses remain in this browser only. No analytics or remote collection is configured.</p>{questions.map((question, index) => <label key={question}>{question}<textarea name={`question-${index + 1}`} rows={3}/></label>)}<button type="submit">Save locally</button>{saved && <output>Saved in this browser.</output>}</form>; }
