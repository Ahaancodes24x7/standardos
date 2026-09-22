import { createFileRoute,redirect } from "@tanstack/react-router";
import { getCurrentUserFn } from "@/server/auth";
import { AppLayout } from "@/components/layout/app-layout";
import { hasDemoSession } from "@/contexts/auth-context";
export const Route=createFileRoute("/_authenticated")({ssr:false,beforeLoad:async({location})=>{if(hasDemoSession())return;const user=await getCurrentUserFn();if(!user)throw redirect({to:"/login",search:{redirect:location.href}});return{user}},component:AppLayout});
