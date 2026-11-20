import { useEffect, useState } from 'react'
import { ArrowUpRight, MapPinned, PackageCheck, Route, Workflow } from 'lucide-react'
import { api, type Run } from '../services/api'
import { Card, DataTable, EmptyState, ErrorNotice, Loading, PageTitle, StatusPill } from '../components/ui'

type Dashboard={active_scenario:{name:string;scenario_type:string;status:string}|null;counts:{scenarios:number;locations:number;resources:number;runs:number};recent_runs:Run[];benchmarks:{id:number;algorithm:string;input_size:number;median_seconds:number;created_at:string}[]}
const stats=[{key:'locations',label:'Affected locations',icon:MapPinned},{key:'resources',label:'Stock records',icon:PackageCheck},{key:'runs',label:'Algorithm runs',icon:Workflow},{key:'scenarios',label:'Saved scenarios',icon:Route}]
export function Overview(){
 const [data,setData]=useState<Dashboard>();const [error,setError]=useState('')
 useEffect(()=>{api<Dashboard>('/dashboard').then(setData).catch(e=>setError(e.message))},[])
 return <><PageTitle eyebrow="RELIEF OPERATIONS / OVERVIEW" title="Planning overview" description="A clear view of saved scenarios, available resources and algorithm work." action={<StatusPill>Decision support only</StatusPill>}/>
  {error?<ErrorNotice error={error}/>:!data?<Loading/>:<>
   <Card className="scenario-banner"><div><div className="eyebrow">ACTIVE SCENARIO</div><h2>{data.active_scenario?.name??'No active scenario'}</h2><p>{data.active_scenario?`${data.active_scenario.scenario_type} · ${data.active_scenario.status}`:'Create a scenario to begin organizing locations and resources.'}</p></div><div className="banner-side"><span className="status-dot"/> MANUALLY ENTERED DATA</div></Card>
   <div className="stat-grid">{stats.map(({key,label,icon:Icon})=><Card className="stat-card" key={key}><div className="stat-top"><span>{label}</span><Icon size={17}/></div><strong>{data.counts[key as keyof Dashboard['counts']]}</strong><small>Records in local SQLite</small></Card>)}</div>
   <div className="content-grid two-col"><Card><div className="panel-heading"><div><h2>Recent algorithm runs</h2><p>Measured by the backend with the current inputs</p></div></div>{data.recent_runs.length?<DataTable><thead><tr><th>Algorithm</th><th>Execution</th><th>Operations</th><th>Recorded</th></tr></thead><tbody>{data.recent_runs.map(run=><tr key={run.id}><td className="strong-cell">{run.algorithm.replaceAll('_',' ')}</td><td>{(run.elapsed_seconds*1000).toFixed(3)} ms</td><td>{run.operations.toLocaleString()}</td><td>{new Date(run.created_at+'Z').toLocaleString()}</td></tr>)}</tbody></DataTable>:<EmptyState title="No runs yet" body="Algorithm results appear here after you run an allocation, route or sorting experiment."/>}</Card>
    <Card><div className="panel-heading"><div><h2>Performance measurements</h2><p>Saved benchmark medians · seconds</p></div></div>{data.benchmarks.length?<div className="benchmark-list">{data.benchmarks.map(b=><div className="benchmark-row" key={b.id}><div><strong>{b.algorithm.replaceAll('_',' ')}</strong><small>n = {b.input_size} · {b.created_at}</small></div><span>{b.median_seconds<0.001?`${(b.median_seconds*1e6).toFixed(1)} μs`:`${(b.median_seconds*1000).toFixed(2)} ms`}</span></div>)}</div>:<EmptyState title="No benchmarks saved" body="Measured data will appear once an experiment is recorded in the Performance Lab."/>}</Card></div>
   <div className="notice-line"><ArrowUpRight size={16}/> Scenarios, stock and road graphs are managed locally. Optional live weather context is available under Live data · India; it is not an official warning. Distances represent configured edge costs, not live travel times.</div>
  </>}
 </>
}
