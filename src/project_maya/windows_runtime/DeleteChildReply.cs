#if MAYA_DELETE_CHILD_CONTROL_INERT || HERMES_JOURNAL_DELETE_CHILD_SOURCE
using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class DeleteChildReply
    {
        readonly string attempt, request;
        readonly int pid;
        bool consumed;

        internal DeleteChildReply(string attempt,string request,int pid)
        {
            Require(Hex(attempt,32) && Hex(request,32) && pid>0);
            this.attempt=attempt;this.request=request;this.pid=pid;
        }

        static bool Hex(string value,int length)
        {return value!=null && value.Length==length && Regex.IsMatch(value,"\\A[0-9a-f]+\\z");}

        static void Require(bool valid)
        {if(!valid)throw new ArgumentException("delete_child_reply");}

        static void Shape(Dictionary<string,object> value,params string[] keys)
        {
            Require(value!=null && value.Count==keys.Length);
            foreach(string key in keys)Require(value.ContainsKey(key));
        }

        static DeleteChildProbe.OpenResult ParseOpen(object value)
        {
            var row=value as Dictionary<string,object>;
            Shape(row,"opened","closed","identity","open_error","identity_error");
            Require(row["opened"] is bool && row["closed"] is bool &&
                row["open_error"] is int && row["identity_error"] is int);
            bool opened=(bool)row["opened"], closed=(bool)row["closed"];
            int error=(int)row["open_error"], identityError=(int)row["identity_error"];
            string identity=row["identity"] as string;
            Require(opened ? error==0 && (identityError==0 ? Hex(identity,24) :
                identityError>0 && identityError<=65535 && row["identity"]==null) :
                !closed && row["identity"]==null && identityError==0 && error>0 && error<=65535);
            return new DeleteChildProbe.OpenResult(opened,closed,identity,error);
        }

        internal DeleteChildProbe.OpenResult[] Admit(Dictionary<string,object> reply)
        {
            Require(!consumed);consumed=true;
            Shape(reply,"v","type","attempt","request_id","pid","control","target");
            Require(1.Equals(reply["v"]) && "delete_child_result".Equals(reply["type"]) &&
                attempt.Equals(reply["attempt"]) && request.Equals(reply["request_id"]) && pid.Equals(reply["pid"]));
            return new[]{ParseOpen(reply["control"]),ParseOpen(reply["target"])};
        }
    }
}
#endif
