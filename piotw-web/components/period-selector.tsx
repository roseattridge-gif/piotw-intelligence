export function PeriodSelector({ period, companyId, action }: { period: string; companyId?: string; action?: string }) {
  return <form className="period-selector" action={action}><label>Briefing period<select name="period" defaultValue={period}><option value="previous">Since previous observation</option><option value="7">Last 7 days</option><option value="30">Last 30 days</option><option value="all">All available history</option></select></label>{companyId ? <input type="hidden" name="company" value={companyId}/> : null}<button type="submit">Apply period</button></form>;
}
