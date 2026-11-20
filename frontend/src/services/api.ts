export const api = async <T,>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(body.detail ?? `Request failed (${response.status})`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export type Scenario = { id:number; name:string; scenario_type:string; description:string; status:string; created_at:string; location_count?:number }
export type Location = { id:number; scenario_id:number; name:string; identifier?:string|null; priority:number; latitude?:number|null; longitude?:number|null; x:number; y:number }
export type Resource = { id:number; scenario_id:number|null; resource_type_id:number; name:string; category:string; unit:string; unit_weight:number; available:number; divisible:boolean|number; value_score:number }
export type Run = { id:number; scenario_id?:number|null; algorithm:string; input_json:string; output_json:string; elapsed_seconds:number; operations:number; created_at:string; input?:Record<string,unknown>; output?:Record<string,unknown> }
export type Benchmark = { id:number; algorithm:string; input_size:number; seed:number; repeat_count:number; median_seconds:number; python_version:string; platform:string; created_at:string }
