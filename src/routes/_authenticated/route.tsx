import { createFileRoute,redirect } from "@tanstack/react-router";
import { supabase } from "@/integrations/supabase/client";
import { AppLayout } from "@/components/layout/app-layout";
import { hasDemoSession } from "@/contexts/auth-context";
export const Route=createFileRoute("/_authenticated")({ssr:false,beforeLoad:async({location})=>{if(hasDemoSession())return;const {data,error}=await supabase.auth.getUser();if(error||!data.user)throw redirect({to:"/login",search:{redirect:location.href}});return{user:data.user}},component:AppLayout});
