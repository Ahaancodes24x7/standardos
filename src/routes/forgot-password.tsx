import { createFileRoute,Link } from "@tanstack/react-router";
import { useState,type FormEvent } from "react";
import { Brand } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { supabase } from "@/integrations/supabase/client";
export const Route=createFileRoute("/forgot-password")({component:Forgot});
function Forgot(){const [sent,setSent]=useState(false);const [error,setError]=useState("");const submit=async(e:FormEvent<HTMLFormElement>)=>{e.preventDefault();const email=String(new FormData(e.currentTarget).get("email"));const {error:err}=await supabase.auth.resetPasswordForEmail(email,{redirectTo:`${window.location.origin}/settings`});if(err)setError(err.message);else setSent(true)};return <main className="site-container grid min-h-screen place-items-center py-10"><div className="w-full max-w-md glass-panel p-7"><Brand/><p className="eyebrow mt-10">Account recovery</p><h1 className="mt-3 font-display text-4xl text-primary">Reset your password.</h1>{sent?<p className="mt-6 text-sm leading-6 text-muted-foreground">Check your inbox for a secure reset link. You can close this page.</p>:<form onSubmit={submit} className="mt-7 grid gap-4"><div className="grid gap-2"><Label htmlFor="email">Work email</Label><Input id="email" name="email" type="email" required/></div>{error&&<p className="text-sm text-destructive">{error}</p>}<Button>Send reset link</Button></form>}<Link to="/login" className="mt-6 block text-sm font-bold text-accent-foreground">Back to sign in</Link></div></main>}
