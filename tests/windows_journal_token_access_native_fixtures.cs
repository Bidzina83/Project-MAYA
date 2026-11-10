using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using ProjectMaya.WindowsRuntime;

internal static class JournalTokenAccessNativeFixtures
{
    static readonly string Attempt=new string('a',32), Request=new string('b',32), Control=new string('c',24),
        ControlDirectory=new string('d',24), Journal=new string('e',24), Parent=new string('f',24);
    static readonly int[] Masks={1,2,4,65536,262144,524288,64,2};
    static readonly object Process=new object(), Pipe=new object();
    const int Pid=1234;
    static int checks;
    static void Check(bool ok) {checks++;if(!ok)throw new Exception("Assertion "+checks);}
    static void Reject(Action action)
    {try {action();}catch(StartupFailure){Check(true);return;}Check(false);}
    static byte[] Bytes(string value) {return Encoding.UTF8.GetBytes(value);}
    static byte[] Command(string role,int version=2)
    {return Bytes("{\"v\":"+version+",\"type\":\"journal_access_probe\",\"attempt\":\""+Attempt+"\",\"role\":\""+role+"\",\"request_id\":\""+Request+"\"}");}

    sealed class Api : IJournalTokenAccessNativeCalls
    {
        readonly string role,fault;
        internal int Opens;
        internal readonly List<IntPtr> Opened=new List<IntPtr>(), Queried=new List<IntPtr>(), Closed=new List<IntPtr>();
        internal Api(string role,string fault) {this.role=role;this.fault=fault;}
        public IntPtr Open(string path,int mask,int share,int disposition,int flags,out int error)
        {
            int index=Opens/2;bool control=Opens++%2==0,directory=index>=6;
            string root=Path.Combine(ProductFiles.Root,Attempt);
            string prefix=Path.Combine(root,role=="worker"?"host":"state","journal-access-control");
            Check(path==(control?(directory?prefix:Path.Combine(prefix,"control.bin")):directory?root:Path.Combine(root,"final-output-journal.v1.jsonl")));
            Check(mask==Masks[index] && share==7 && disposition==3 && flags==(directory?0x02200000:0x00200000));
            if(!control && !(index==0 && fault!=null && fault.StartsWith("target-open",StringComparison.Ordinal)))
            {error=index==0 && fault=="share"?32:index==0 && fault=="no-open-error"?0:5;return new IntPtr(-1);}
            error=0;var handle=new IntPtr(Opens);Opened.Add(handle);return handle;
        }
        public string Identity(IntPtr handle,bool directory,out int error)
        {
            Check(Opened.Contains(handle) && !Queried.Contains(handle) && !Closed.Contains(handle));Queried.Add(handle);
            int id=handle.ToInt32();Check(directory==(id>=13));error=0;
            if(id==1 && fault=="control-query" || id==2 && fault=="target-open-query") {error=5;return null;}
            if(id==2 && fault=="target-open-invalid-id")return "bad";
            if(id==2 && fault=="target-open-throws")throw new IOException("fixture");
            return id%2==0?Journal:directory?ControlDirectory:Control;
        }
        public bool Close(IntPtr handle)
        {
            Check(Opened.Contains(handle) && Queried.Contains(handle) && !Closed.Contains(handle));Closed.Add(handle);
            if(handle.ToInt32()==2 && fault=="target-open-throws")throw new IOException("fixture");
            return !(handle.ToInt32()==1 && fault=="control-close" || handle.ToInt32()==2 && fault=="target-open-close");
        }
    }

    static byte[] Run(string role,string fault=null)
    {
        var api=new Api(role,fault);
        var fixture=new JournalTokenAccessNativeFixture(Attempt,role,Pid,Request,api);
        byte[] raw=fixture.Execute(Command(role));
        Check(api.Opens==16 && api.Opened.SequenceEqual(api.Queried) && api.Opened.SequenceEqual(api.Closed));
        Reject(()=>fixture.Execute(Command(role)));Check(api.Opens==16);return raw;
    }
    static string[] Admit(byte[] raw,string role="worker",bool native=true,bool token=true)
    {
        var owner=new JournalTokenAccessAdmission(Process,Pipe,Attempt,role,Pid,Request,Control,ControlDirectory,Journal,Parent);
        return native?owner.AdmitNative(raw,Process,Pipe,token,true,true,true,Journal,Parent,Journal,Parent,true):
            owner.Admit(raw,Process,Pipe,token,true,true,true,Journal,Parent,Journal,Parent,true);
    }
    static void Main()
    {
        foreach(string role in new[]{"worker","child"})Check(Admit(Run(role),role).All(x=>x.EndsWith(":denied")));
        foreach(string fault in new[]{"control-query","control-close","share","no-open-error","target-open-query",
            "target-open-invalid-id","target-open-close","target-open-throws"})
        {
            byte[] raw=Run("worker",fault);
            Check(Admit(raw)[0]=="read_data:"+(fault.StartsWith("target-open",StringComparison.Ordinal)?"forbidden_open":"incomplete"));
            var first=(Dictionary<string,object>)((List<object>)StrictJson.Parse(raw)["rows"])[0];
            var target=(Dictionary<string,object>)first["target"];
            if(fault=="target-open-query" || fault=="target-open-invalid-id" || fault=="target-open-throws")
                Check(true.Equals(target["opened"]) && 0.Equals(target["open_error"]) && target["identity"]==null &&
                    (fault=="target-open-query"?5:fault=="target-open-invalid-id"?13:31).Equals(target["identity_error"]));
        }
        byte[] good=Run("worker");string text=Encoding.UTF8.GetString(good);
        Reject(()=>Admit(good,native:false));Reject(()=>Admit(good,token:false));
        byte[] legacy=new JournalTokenAccessFixture.ProbeSession(Attempt,"worker",Pid,Request).Execute(Command("worker",1),
            (p,m,s,d,f)=>p.EndsWith("control.bin")?new JournalAccessStatus(true,true,0,Control):new JournalAccessStatus(false,false,5,null));
        Reject(()=>Admit(legacy));
        foreach(string invalid in new[]{text.Replace("\"v\":2","\"v\":1"),text.Replace("\"open_error\":5","\"open_error\":0"),
            text.Replace("\"identity_error\":0","\"identity_error\":5"),text.Replace("\"closed\":false","\"closed\":true"),
            text.Replace("\"open_error\":5","\"open_error\":5,\"path\":\"x\""),text.Replace("\"pid\":1234","\"pid\":1235")})
            Reject(()=>Admit(Bytes(invalid)));
        foreach(byte[] invalid in new[]{Command("child"),Command("worker",1),null})
        {
            var api=new Api("worker",null);var fixture=new JournalTokenAccessNativeFixture(Attempt,"worker",Pid,Request,api);
            Reject(()=>fixture.Execute(invalid));Reject(()=>fixture.Execute(Command("worker")));Check(api.Opens==0);
        }
        Console.WriteLine("Native token open/close injected fixture: "+checks+" assertions passed");
    }
}
