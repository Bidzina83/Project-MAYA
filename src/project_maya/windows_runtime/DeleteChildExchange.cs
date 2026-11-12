#if HERMES_JOURNAL_DELETE_CHILD_SOURCE
using System;
using System.Collections.Generic;
using System.Diagnostics;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class DeleteChildExchange : IDisposable
    {
        readonly WindowsIsolation child;
        readonly BridgeChannel channel;
        bool used;

        internal DeleteChildExchange(WindowsIsolation child)
        {
            if(child==null || !child.ReducedLaunchTokenVerified || child.Resumed ||
                child.BridgeInput==IntPtr.Zero || child.BridgeOutput==IntPtr.Zero)
                throw new StartupFailure("delete_child_launch_binding");
            this.child=child;
            channel=new BridgeChannel(child.BridgeOutput,child.BridgeInput);
        }

        internal DeleteChildProbe.OpenResult[] Run(string attempt,Dictionary<string,object> record)
        {
            if(used || child.Resumed)throw new StartupFailure("delete_child_launch_binding");
            used=true;
            int pid=checked((int)child.ChildPid);
            string request=BridgeHostFiles.RandomHex(16);
            var admission=new DeleteChildReply(attempt,request,pid);
            var time=Stopwatch.StartNew();
            Func<int> left=()=> {
                int remaining=22000-(int)time.ElapsedMilliseconds;
                if(remaining<=0)throw new StartupFailure("delete_child_deadline");
                return remaining;
            };
            child.ResumeBridge();
            channel.Write(new Dictionary<string,object>{{"v",1},{"type","delete_child_probe"},
                {"attempt",attempt},{"request_id",request}},Math.Min(2000,left()));
            child.CloseDeleteChildInput();
            var rows=admission.Admit(channel.Read(left()));
            if(rows[1].Opened)record["delete_child_provisional_forbidden_open"]=true;
            channel.Eof(Math.Min(2000,left()));
            child.WaitBridge((uint)left());
            if(child.ExitCode!=0 || child.BridgeInput!=IntPtr.Zero)
                throw new StartupFailure("delete_child_lifecycle");
            record["delete_child_natural_exit_verified"]=true;
            // Final classification still requires coordinator readback and cleanup.
            return rows;
        }

        // The owner calls this after stopping the job, including on a timed-out read.
        public void Dispose() {channel.Dispose();}
    }
}
#endif
