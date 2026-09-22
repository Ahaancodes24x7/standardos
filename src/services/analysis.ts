import { documents, standardsCatalog, type ProcurementDocument } from "@/data/demo";
const wait=(ms:number)=>new Promise((resolve)=>setTimeout(resolve,ms));
export type AnalysisInput={file?:File;text?:string};
export async function extractRequirements(input:AnalysisInput){await wait(350); if(!input.file&&!input.text?.trim()) throw new Error("Add a document or specification text first."); return documents[0]?.requirements ?? []}
export async function findStandards(){await wait(350);return standardsCatalog.slice(0,4)}
export async function resolveDependencies(){await wait(300);return {nodes:8,links:7}}
export async function detectConflicts(){await wait(320);return documents[0]?.findings ?? []}
export async function generateRepair(documentId:string){await wait(500);return getAnalysis(documentId).repairs}
export async function getChangeImpact(){await wait(250);return import("@/data/demo").then((module)=>module.changeEvents)}
export async function analyzeDocument(input:AnalysisInput,onProgress?:(step:number)=>void):Promise<ProcurementDocument>{for(let i=0;i<8;i+=1){await wait(340);onProgress?.(i+1)} return documents[0] as ProcurementDocument}
export function getAnalysis(id:string){const result=documents.find((item)=>item.id===id);if(!result) throw new Error("Analysis not found");return result}
