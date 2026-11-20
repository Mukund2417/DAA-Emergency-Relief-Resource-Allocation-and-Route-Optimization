import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react'
import { LoaderCircle } from 'lucide-react'

export function Button({children,className='',...props}:ButtonHTMLAttributes<HTMLButtonElement>&{className?:string}) {
  return <button className={`button ${className}`} {...props}>{children}</button>
}
export function Card({children,className=''}:{children:ReactNode;className?:string}) {
  return <section className={`card ${className}`}>{children}</section>
}
export function Field({label,className='',...props}:InputHTMLAttributes<HTMLInputElement>&{label:string;className?:string}) {
  return <label className="field"><span>{label}</span><input className={className} {...props}/></label>
}
export function SelectField({label,children,...props}:SelectHTMLAttributes<HTMLSelectElement>&{label:string;children:ReactNode}) {
  return <label className="field"><span>{label}</span><select {...props}>{children}</select></label>
}
export function TextareaField({label,...props}:TextareaHTMLAttributes<HTMLTextAreaElement>&{label:string}) {
  return <label className="field"><span>{label}</span><textarea className="textarea-input" {...props}/></label>
}
export function PageTitle({eyebrow,title,description,action}:{eyebrow:string;title:string;description:string;action?:ReactNode}) {
  return <header className="page-title"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</header>
}
export function EmptyState({title,body}:{title:string;body:string}) {
  return <div className="empty"><span className="empty-mark">—</span><strong>{title}</strong><p>{body}</p></div>
}
export function Loading() { return <div className="loading"><LoaderCircle size={18} className="spin"/> Loading records…</div> }
export function ErrorNotice({error}:{error:string}) { return <div role="alert" className="error-notice">{error}</div> }
export function DataTable({children}:{children:ReactNode}) { return <div className="table-scroll"><table className="data-table">{children}</table></div> }
export function StatusPill({children}:{children:ReactNode}) { return <span className="status-pill">{children}</span> }
