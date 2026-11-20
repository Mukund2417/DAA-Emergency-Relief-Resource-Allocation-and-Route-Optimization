import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { DashboardLayout } from './layouts/DashboardLayout'
import { Loading } from './components/ui'

const Overview=lazy(()=>import('./pages/Overview').then(m=>({default:m.Overview})))
const Scenarios=lazy(()=>import('./pages/Scenarios').then(m=>({default:m.Scenarios})))
const Locations=lazy(()=>import('./pages/Locations').then(m=>({default:m.Locations})))
const Inventory=lazy(()=>import('./pages/Inventory').then(m=>({default:m.Inventory})))
const Allocation=lazy(()=>import('./pages/Allocation').then(m=>({default:m.Allocation})))
const Network=lazy(()=>import('./pages/Network').then(m=>({default:m.Network})))
const RoutesPage=lazy(()=>import('./pages/RoutesPage').then(m=>({default:m.RoutesPage})))
const Tour=lazy(()=>import('./pages/Tour').then(m=>({default:m.Tour})))
const Explorer=lazy(()=>import('./pages/Explorer').then(m=>({default:m.Explorer})))
const Performance=lazy(()=>import('./pages/Performance').then(m=>({default:m.Performance})))
const Reports=lazy(()=>import('./pages/Reports').then(m=>({default:m.Reports})))
const IndiaLiveData=lazy(()=>import('./pages/IndiaLiveData').then(m=>({default:m.IndiaLiveData})))

export function App(){
 return <Suspense fallback={<div className="page-content"><Loading/></div>}><Routes><Route element={<DashboardLayout/>}>
   <Route index element={<Overview/>}/><Route path="scenarios" element={<Scenarios/>}/>
   <Route path="locations" element={<Locations/>}/><Route path="inventory" element={<Inventory/>}/>
   <Route path="allocation" element={<Allocation/>}/><Route path="network" element={<Network/>}/>
   <Route path="routes" element={<RoutesPage/>}/><Route path="tour" element={<Tour/>}/>
   <Route path="algorithms" element={<Explorer/>}/><Route path="performance" element={<Performance/>}/>
   <Route path="reports" element={<Reports/>}/><Route path="live-india" element={<IndiaLiveData/>}/>
   <Route path="*" element={<Navigate to="/" replace/>}/>
 </Route></Routes></Suspense>
}
