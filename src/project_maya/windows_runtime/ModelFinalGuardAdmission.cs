using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelFinalGuardAdmission
    {
        static bool Flag(Dictionary<string,object> g,string key)
        {
            if(!(g[key] is bool))throw new StartupFailure("final_guard_flag");
            return (bool)g[key];
        }
        static void Empty(Dictionary<string,object> g,params string[] keys)
        {foreach(string key in keys)if(g[key]!=null)throw new StartupFailure("final_guard_unobserved");}
        internal static bool Validate(Dictionary<string,object> g,string attempt,string delivery,string command)
        {
            BridgeRuntime.Shape(g,"schema","attempt","runtime_delivery_command_id","final_command_id",
                "expected_phase","phase","closed","audit_failed","revoked","clock_called","clock_returned",
                "comparison_evaluated","at_or_after_deadline","decision","cause","timing_valid",
                "issue_sampled","elapsed_ms","remaining_ms","ttl_ms");
            foreach(string id in new[]{attempt,delivery,command})
                if(id==null || !Regex.IsMatch(id,"\\A[0-9a-f]{32}\\z"))throw new StartupFailure("final_guard_ID");
            if(delivery==command || !"maya.model.final_guard.v1".Equals(g["schema"]) ||
                !attempt.Equals(g["attempt"]) || !delivery.Equals(g["runtime_delivery_command_id"]) ||
                !command.Equals(g["final_command_id"]) || !"runtime_delivered".Equals(g["expected_phase"]) ||
                !2000.Equals(g["ttl_ms"]))throw new StartupFailure("final_guard_binding");
            foreach(string key in new[]{"closed","audit_failed","revoked","at_or_after_deadline"})
                if(g[key]!=null && !(g[key] is bool))throw new StartupFailure("final_guard_state_type");
            string phase=g["phase"] as string,decision=g["decision"] as string,cause=null;
            if(g["phase"]!=null && (phase==null || Array.IndexOf(new[]{"new","issued","admitted","dispatched",
                "runtime_prepared","runtime_delivered","operator_admitted","operator_prepared","complete","other"},phase)<0))
                throw new StartupFailure("final_guard_phase");
            if(decision!="allowed" && decision!="rejected" && decision!="raised")throw new StartupFailure("final_guard_decision");
            bool called=Flag(g,"clock_called"),returned=Flag(g,"clock_returned"),compared=Flag(g,"comparison_evaluated"),
                timing=Flag(g,"timing_valid"),issue=Flag(g,"issue_sampled");
            if(true.Equals(g["closed"])){cause="closed";Empty(g,"audit_failed","revoked","phase");}
            else if(false.Equals(g["closed"]) && true.Equals(g["audit_failed"]))
            {cause="audit_failed";Empty(g,"revoked","phase");}
            else if(false.Equals(g["closed"]) && false.Equals(g["audit_failed"]) && true.Equals(g["revoked"]))
            {cause="revoked";Empty(g,"phase");}
            else if(false.Equals(g["closed"]) && false.Equals(g["audit_failed"]) && false.Equals(g["revoked"]) && phase!=null)
            {if(phase!="runtime_delivered")cause="phase_mismatch";}
            else
            {
                cause="state_exception";bool missing=false;
                foreach(string key in new[]{"closed","audit_failed","revoked","phase"})
                {
                    if(g[key]==null)missing=true;
                    else if(missing)throw new StartupFailure("final_guard_state_order");
                }
                if(!missing)throw new StartupFailure("final_guard_missing_state");
            }
            if(cause!=null)
            {
                if(called || returned || compared || g["at_or_after_deadline"]!=null ||
                    decision!=(cause=="state_exception"?"raised":"rejected"))throw new StartupFailure("final_guard_short_circuit");
            }
            else
            {
                if(!called)throw new StartupFailure("final_guard_clock_called");
                if(!returned)
                {
                    cause="clock_exception";
                    if(compared || g["at_or_after_deadline"]!=null || decision!="raised")throw new StartupFailure("final_guard_clock_exception");
                }
                else if(!compared)
                {
                    cause="clock_value_exception";
                    if(g["at_or_after_deadline"]!=null || decision!="raised")throw new StartupFailure("final_guard_comparison");
                }
                else
                {
                    bool expired=Flag(g,"at_or_after_deadline");cause=expired?"expired":"allowed";
                    if(decision!=(expired?"rejected":"allowed"))throw new StartupFailure("final_guard_clock_decision");
                }
            }
            if(!cause.Equals(g["cause"]))throw new StartupFailure("final_guard_cause");
            if(timing)
            {
                if(!compared || !returned || !issue || !(g["elapsed_ms"] is int) || (int)g["elapsed_ms"]<0 ||
                    !(g["remaining_ms"] is int) || (int)g["remaining_ms"]==Int32.MinValue ||
                    (true.Equals(g["at_or_after_deadline"]) && (int)g["remaining_ms"]>0) ||
                    (false.Equals(g["at_or_after_deadline"]) && (int)g["remaining_ms"]<0))
                    throw new StartupFailure("final_guard_timing");
            }
            else Empty(g,"elapsed_ms","remaining_ms");
            return decision=="allowed" && timing;
        }
    }
}
