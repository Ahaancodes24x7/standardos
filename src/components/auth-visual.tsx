import { BadgeCheck,BookOpenCheck,FileText,ListChecks,ShieldCheck } from "lucide-react";
const stages=[{label:"Specification",icon:FileText},{label:"Requirement",icon:ListChecks},{label:"Indian Standard",icon:BookOpenCheck},{label:"Test / Certification",icon:BadgeCheck},{label:"Compliance",icon:ShieldCheck}];
export function AuthVisual(){return <div className="pointer-events-none absolute inset-0 overflow-hidden">
  <div className="absolute inset-0 opacity-[.05] [background-image:linear-gradient(var(--primary-foreground)_1px,transparent_1px),linear-gradient(90deg,var(--primary-foreground)_1px,transparent_1px)] [background-size:46px_46px]"/>
  <svg className="absolute -right-28 -top-28 size-[440px] opacity-[.09]" viewBox="0 0 100 100" fill="none" stroke="var(--primary-foreground)">
    <circle cx="50" cy="50" r="46" strokeWidth=".6"/>
    <circle cx="50" cy="50" r="6" strokeWidth=".6"/>
    {Array.from({length:16}).map((_,i)=>{const a=(i*Math.PI*2)/16;return <line key={i} x1={50+6*Math.cos(a)} y1={50+6*Math.sin(a)} x2={50+46*Math.cos(a)} y2={50+46*Math.sin(a)} strokeWidth=".4"/>})}
  </svg>
  <div className="absolute inset-0 opacity-60 [background-image:radial-gradient(circle_at_55%_36%,color-mix(in_oklab,var(--accent)_55%,transparent),transparent_45%)]"/>
  <div className="absolute inset-0 flex items-center justify-center pb-40">
    <div className="flex flex-col items-center">
      {stages.map(({label,icon:Icon},i)=>{const last=i===stages.length-1;return <div key={label} className="flex flex-col items-center">
        <div className={`flex flex-col items-center gap-2 rounded-xl border px-6 py-4 backdrop-blur-md transition-colors duration-500 ${last?"border-accent/70 bg-accent/15 shadow-[0_0_44px_-10px_var(--accent)]":"border-primary-foreground/15 bg-primary-foreground/5"}`}>
          <Icon className={last?"size-5 text-accent":"size-5 text-primary-foreground/70"}/>
          <span className={`text-[10px] font-bold uppercase tracking-[.12em] ${last?"text-accent":"text-primary-foreground/55"}`}>{label}</span>
        </div>
        {!last&&<span className="pulse-line my-1 h-8 w-px bg-gradient-to-b from-accent/70 to-accent/10"/>}
      </div>})}
    </div>
  </div>
</div>}
