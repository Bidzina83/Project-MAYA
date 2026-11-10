using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class JournalAccessProfileFixtures
{
    static int assertions;
    static readonly string[] Roots={"journal_access_worker_entry.py","journal_access_child_entry.py","journal_access_role.py"};
    static readonly string[] Base={"python/python.exe","python/python313.dll","startup_check.py"};
    static void Check(bool ok)
    {assertions++;if(!ok)throw new Exception("assertion "+assertions);}
    static void Reject(Action action)
    {
        try {action();}
        catch(StartupFailure) {assertions++;return;}
        throw new Exception("expected rejection");
    }
    static void Index(IEnumerable<string> paths)
    {
        var digest=new string('a',64);
        var json=new JavaScriptSerializer().Serialize(new {
            python_version="3.13.14",zip_sha256=digest,files=paths.Select(path=>new {path=path,sha256=digest,size=0}).ToArray()
        });
        ProductFiles.ReadIndex(new MemoryStream(Encoding.UTF8.GetBytes(json)),true);
    }
#if HERMES_JOURNAL_ACCESS
    static void Admission()
    {
        string attempt=new string('a',32),request=new string('b',32),file=new string('c',24),
            folder=new string('d',24),journal=new string('e',24),parent=new string('f',24);
        var process=new object();var pipe=new object();
        var rows=Enumerable.Range(0,JournalTokenAccessFixture.CaseCount).Select(i=>new {
            @case=JournalTokenAccessFixture.CaseName(i),mask=JournalTokenAccessFixture.CaseMask(i),
            control=new {opened=true,closed=true,open_error=0,identity=i<6?file:folder,identity_error=0},
            target=new {opened=false,closed=false,open_error=5,identity=(string)null,identity_error=0}
        }).ToArray();
        var reply=Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(new {
            v=2,type="journal_access_result",attempt=attempt,role="worker",pid=1234,request_id=request,rows=rows
        }));
        foreach(string failure in new[]{"none","process","pipe","token","stdin","eof","exit","before","after","descriptor","stale","role","pid"})
        {
            var owner=new JournalTokenAccessAdmission(process,pipe,attempt,failure=="role"?"child":"worker",
                failure=="pid"?1235:1234,failure=="stale"?attempt:request,file,folder,journal,parent);
            Func<string[]> admit=()=>owner.AdmitNative(reply,failure=="process"?new object():process,
                failure=="pipe"?new object():pipe,failure!="token",failure!="stdin",failure!="eof",failure!="exit",
                failure=="before"?file:journal,parent,failure=="after"?file:journal,parent,failure!="descriptor");
            if(failure=="none")Check(admit().All(row=>row.EndsWith(":denied",StringComparison.Ordinal)));
            else Reject(()=>admit());
            Reject(()=>admit());
        }
        foreach(string failure in new[]{"control_open","control_identity","control_mismatch","control_close","target_error","forbidden"})
        {
            var message=StrictJson.Parse(reply);
            var row=(Dictionary<string,object>)((List<object>)message["rows"])[6];
            var control=(Dictionary<string,object>)row["control"];
            var target=(Dictionary<string,object>)row["target"];
            if(failure=="control_open")
            {
                control["opened"]=false;control["closed"]=false;control["identity"]=null;control["open_error"]=5;
            }
            if(failure=="control_identity") {control["identity"]=null;control["identity_error"]=6;}
            if(failure=="control_mismatch")control["identity"]=file;
            if(failure=="control_close")control["closed"]=false;
            if(failure=="target_error")target["open_error"]=32;
            if(failure=="forbidden")
            {
                target["opened"]=true;target["open_error"]=0;target["identity_error"]=6;
            }
            var raw=Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(message));
            var owner=new JournalTokenAccessAdmission(process,pipe,attempt,"worker",1234,request,file,folder,journal,parent);
            var diagnostics=new List<Dictionary<string,object>>();
            var result=owner.AdmitNative(raw,process,pipe,true,true,true,true,journal,parent,journal,parent,true,diagnostics);
            Check(result[6]=="delete_child:"+(failure=="forbidden"?"forbidden_open":"incomplete"));
            Check(result.Where((entry,index)=>index!=6).All(entry=>entry.EndsWith(":denied",StringComparison.Ordinal)));
            Check(diagnostics.Count==(failure=="forbidden"?0:1));
            if(failure=="forbidden")continue;
            var observed=diagnostics[0];
            Check(observed.Count==7 && "delete_child".Equals(observed["case"]));
            Check(control["opened"].Equals(observed["control_opened"]) && control["closed"].Equals(observed["control_closed"]));
            Check(control["open_error"].Equals(observed["control_open_error"]) && control["identity_error"].Equals(observed["control_identity_error"]));
            Check(folder.Equals(control["identity"]).Equals(observed["control_identity_matches"]));
            Check(target["open_error"].Equals(observed["target_open_error"]));
            var rejected=new JournalTokenAccessAdmission(process,pipe,attempt,"worker",1234,request,file,folder,journal,parent);
            diagnostics.Clear();
            Reject(()=>rejected.AdmitNative(raw,process,pipe,true,true,false,true,journal,parent,journal,parent,true,diagnostics));
            Check(diagnostics.Count==0);
        }
    }
#endif
    public static void Main()
    {
#if HERMES_JOURNAL_ACCESS
        Admission();
        Index(Base.Concat(Roots));Check(true);
        foreach(string root in Roots)
        {
            Check(ProductFiles.PayloadPath(root)==root);
            Reject(()=>Index(Base.Concat(Roots.Where(path=>path!=root))));
            Reject(()=>Index(Base.Concat(Roots).Concat(new[]{root})));
            Reject(()=>ProductFiles.PayloadPath(root.ToUpperInvariant()));
            Reject(()=>ProductFiles.PayloadPath("./"+root));
        }
        Check(JournalAccessRuntime.ExactEntries(new[]{"control"},"control"));
        Check(!JournalAccessRuntime.ExactEntries(new string[0],"control"));
        Check(!JournalAccessRuntime.ExactEntries(new[]{"control","extra"},"control"));
        Check(!JournalAccessRuntime.ExactEntries(new[]{"alias"},"control"));
        Check(typeof(ProtectedPython).Assembly.GetType("ProjectMaya.WindowsRuntime.JournalTokenAccessWindowsCalls")==null);
        Check(typeof(ProtectedPython).Assembly.GetType("ProjectMaya.WindowsRuntime.JournalTokenAccessNativeFixture").GetConstructors(
            System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).Length==0);
        Check(typeof(ProtectedPython).Assembly.GetTypes().All(type=>type.Name!="FinalOutputInertAdapter" &&
            type.Name!="CoordinatorJournalScratchTarget" && type.Name!="ProbeSession"));
        var denied=Enumerable.Range(0,JournalTokenAccessFixture.CaseCount).Select(i=>JournalTokenAccessFixture.CaseName(i)+":denied").ToArray();
        foreach(string scenario in new[]{"denied","incomplete","empty","forbidden","child_forbidden","changed","unbound"})
        {
            var record=new Dictionary<string,object>();
            var order=new List<string>();
            Func<string[]> worker=()=>{
                order.Add("worker");
                if(scenario=="unbound")throw new StartupFailure("stale");
                if(scenario=="forbidden")return new[]{"read_data:forbidden_open"};
                if(scenario=="incomplete")return new[]{"read_data:incomplete"};
                if(scenario=="empty")return new string[0];
                return denied;
            };
            Func<string[]> child=()=>{order.Add("child");return scenario=="child_forbidden"?new[]{"read_data:forbidden_open"}:denied;};
            Action readback=()=>{order.Add("readback");if(scenario=="changed")throw new StartupFailure("changed");};
            Action run=()=>JournalAccessRuntime.ProbeSequence(worker,child,readback,record);
            if(scenario=="denied")run();else Reject(run);
            Check(string.Join(",",order)==(scenario=="unbound"?"worker":scenario=="forbidden"?"worker,readback":"worker,child,readback"));
            record["journal_access_worker_stopped"]=true;
            record["journal_access_worker_natural_exit_verified"]=true;
            record["journal_access_child_natural_exit_verified"]=true;
            Check(JournalAccessRuntime.FinalStatus(record,false)=="blocked");
            Check(JournalAccessRuntime.FinalStatus(record,true)==(scenario=="denied"?"access_matrix_denied_pending_independent_cleanup":"blocked"));
            record["journal_access_worker_provisional_forbidden"]=new[]{"read_data:forbidden_open"};
            Check(JournalAccessRuntime.FinalStatus(record,true)=="blocked");
        }
#else
        Index(Base);Check(true);
        foreach(string root in Roots)
        {
            Reject(()=>ProductFiles.PayloadPath(root));
            Reject(()=>Index(Base.Concat(new[]{root})));
        }
        Check(typeof(ProtectedPython).Assembly.GetType("ProjectMaya.WindowsRuntime.JournalAccessRuntime")==null);
#endif
        Console.WriteLine("Journal access profile: {0} assertions",assertions);
    }
}
