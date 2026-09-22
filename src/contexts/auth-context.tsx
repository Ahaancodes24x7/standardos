import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { User } from "@supabase/supabase-js";
import { supabase } from "@/integrations/supabase/client";

type Profile={full_name:string;organization:string};
type AuthState={user:User|null;profile:Profile|null;loading:boolean;isDemo:boolean;signOut:()=>Promise<void>;activateDemo:()=>void;refreshProfile:()=>Promise<void>};
const AuthContext=createContext<AuthState|undefined>(undefined);
const demoProfile={full_name:"Ahaan Luther",organization:"Infrastructure Procurement Cell"};
export function AuthProvider({children}:{children:ReactNode}){
 const [user,setUser]=useState<User|null>(null);const [profile,setProfile]=useState<Profile|null>(null);const [loading,setLoading]=useState(true);const [isDemo,setIsDemo]=useState(false);
 const refreshProfile=async()=>{const {data:{user:current}}=await supabase.auth.getUser();setUser(current);if(current){const {data}=await supabase.from("profiles").select("full_name,organization").eq("user_id",current.id).maybeSingle();setProfile(data??{full_name:String(current.user_metadata["full_name"]??current.email?.split("@")[0]??"User"),organization:String(current.user_metadata["organization"]??"My workspace")});}};
 useEffect(()=>{const demo=window.localStorage.getItem("standardos-demo")==="true";setIsDemo(demo);void refreshProfile().finally(()=>setLoading(false));const {data}=supabase.auth.onAuthStateChange((event,session)=>{if(event!=="SIGNED_IN"&&event!=="SIGNED_OUT"&&event!=="USER_UPDATED")return;setUser(session?.user??null);if(event==="SIGNED_OUT")setProfile(null);else void refreshProfile();});return()=>data.subscription.unsubscribe()},[]);
 const value=useMemo(()=>({user,profile:isDemo?demoProfile:profile,loading,isDemo,activateDemo:()=>{window.localStorage.setItem("standardos-demo","true");setIsDemo(true);setProfile(demoProfile)},refreshProfile,signOut:async()=>{window.localStorage.removeItem("standardos-demo");setIsDemo(false);await supabase.auth.signOut();setUser(null);setProfile(null)}}),[user,profile,loading,isDemo]);
 return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
export function useAuth(){const value=useContext(AuthContext);if(!value)throw new Error("useAuth must be used inside AuthProvider");return value}
export function hasDemoSession(){return typeof window!=="undefined"&&window.localStorage.getItem("standardos-demo")==="true"}
