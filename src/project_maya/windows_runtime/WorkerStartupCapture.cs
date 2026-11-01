using System;
using System.Collections.Generic;
using System.Text;

namespace ProjectMaya.WindowsRuntime
{
    // Diagnostic evidence only. Never admits readiness, output or a passed case.
    internal sealed class WorkerStartupCapture
    {
        readonly object gate=new object();
        readonly List<byte> saved=new List<byte>();
        bool started,complete,failed,overflow;
        int observed;
        internal static readonly string[] Stages={"bootstrap_preflight","bootstrap_imports","bootstrap_paths","worker_import",
            "worker_preflight","worker_root","dependency_readback","canonical_preflight","config_read","policy_read",
            "literals_read","audit_open","service_config","request_build","request_open","request_write","request_flush",
            "request_sync","request_close","request_write_checked","service_import","service_construct","ready_send","ready_sent"};
        internal static readonly string[] Errors={"PreflightRejected","OtherError","ProtocolError","HostFileError","ValueError","OSError",
            "PermissionError","FileNotFoundError","ModuleNotFoundError","ImportError","TypeError","AttributeError","RuntimeError",
            "KeyError","UnicodeError","UnicodeDecodeError","UnicodeEncodeError"};
        internal void Start(){lock(gate){started=true;}}
        internal void Append(byte[] buffer,int count)
        {
            if(buffer==null || count<0 || count>buffer.Length)throw new ArgumentException();
            lock(gate)
            {
                observed=checked(observed+count);
                if(observed>256){overflow=true;saved.Clear();return;}
                if(!overflow)for(int i=0;i<count;i++)saved.Add(buffer[i]);
            }
        }
        internal void Complete(bool captureFailed){lock(gate){complete=true;failed=captureFailed;}}
        internal Dictionary<string,object> Snapshot(string processState,uint? exitCode)
        {
            lock(gate)
            {
                string state=!started?"unavailable":!complete?"pending":failed?"capture_failed":observed==0?"empty":"invalid";
                string stage=null,code=null;
                if(started && complete && !failed && !overflow && observed>0)
                {
                    bool ascii=true;foreach(byte b in saved)if(b>127)ascii=false;
                    string text=ascii?Encoding.ASCII.GetString(saved.ToArray()):"";
                    int tail=text.EndsWith("\r\n",StringComparison.Ordinal)?2:text.EndsWith("\n",StringComparison.Ordinal)?1:0;
                    string[] parts=tail>0?text.Substring(0,text.Length-tail).Split('|'):new string[0];
                    if(parts.Length==3 && parts[0]=="MAYA_WORKER_STARTUP_V1" && Array.IndexOf(Stages,parts[1])>=0 && Array.IndexOf(Errors,parts[2])>=0)
                    {state="reported_failure";stage=parts[1];code=parts[2];}
                }
                return new Dictionary<string,object> {
                    {"process_state",processState},{"exit_code_hex",exitCode.HasValue?"0x"+exitCode.Value.ToString("X8"):null},
                    {"stderr_bytes_observed",started?(object)observed:null},{"stderr_capture_complete",started && complete && !failed},
                    {"diagnostic_state",state},{"diagnostic_stage",stage},{"diagnostic_error_type",code}
                };
            }
        }
    }
}
