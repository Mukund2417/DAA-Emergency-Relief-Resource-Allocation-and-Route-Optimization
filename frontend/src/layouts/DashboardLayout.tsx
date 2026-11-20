import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { Activity, Boxes, ChartNoAxesCombined, ClipboardList, Compass, GitBranch, HeartPulse, Map, Package, Route, ShieldCheck, Truck, Waypoints, CloudSun } from 'lucide-react'

const nav=[
  {to:'/',label:'Overview',icon:Compass},
  {to:'/scenarios',label:'Scenarios',icon:ClipboardList},
  {to:'/locations',label:'Affected locations',icon:Map},
  {to:'/live-india',label:'Live data · India',icon:CloudSun},
  {to:'/inventory',label:'Resource inventory',icon:Package},
  {to:'/allocation',label:'Allocation',icon:Boxes},
  {to:'/network',label:'Road network',icon:Waypoints},
  {to:'/routes',label:'Route optimization',icon:Route},
  {to:'/tour',label:'Delivery tour',icon:Truck},
  {to:'/algorithms',label:'Algorithm explorer',icon:GitBranch},
  {to:'/performance',label:'Performance lab',icon:ChartNoAxesCombined},
  {to:'/reports',label:'Reports',icon:Activity},
]
const titles:Record<string,string>={'/':'Overview','/scenarios':'Scenarios','/locations':'Affected locations','/live-india':'Live data · India','/inventory':'Resource inventory','/allocation':'Resource allocation','/network':'Road network','/routes':'Route optimization','/tour':'Delivery tour','/algorithms':'Algorithm explorer','/performance':'Performance lab','/reports':'Reports'}

export function DashboardLayout(){
  const location=useLocation()
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><HeartPulse size={19}/></div><div><strong>Relief planning</strong><small>DAA workbench</small></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav className="side-nav">{nav.map(({to,label,icon:Icon})=><NavLink key={to} to={to} end={to==='/'} className={({isActive})=>`nav-link${isActive?' active':''}`}><Icon size={17} strokeWidth={1.8}/><span>{label}</span></NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="prototype-note"><ShieldCheck size={16}/><span>Academic prototype<br/><small>Not a dispatch system</small></span></div><a href="https://shadcndashboard.dev/" target="_blank" rel="noreferrer" className="credit">Dashboard design reference ↗</a></div>
    </aside>
    <div className="main-area">
      <div className="topbar"><div className="crumb">Relief operations <span>/</span> {titles[location.pathname]??'Workspace'}</div><div className="topbar-right"><span className="data-label"><i/> LOCAL + LIVE</span></div></div>
      <main className="page-content"><Outlet/></main>
    </div>
  </div>
}
