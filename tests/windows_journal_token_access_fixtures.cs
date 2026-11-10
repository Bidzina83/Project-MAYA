using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class JournalTokenAccessFixtures
{
    static readonly string Attempt=new string('a',32), Request=new string('b',32), Control=new string('c',24),
        ControlDirectory=new string('d',24), Journal=new string('e',24), Parent=new string('f',24);
    static readonly string[] Cases={"read_data","write_data","append_data","delete","write_dacl","write_owner","delete_child","add_file"};
    static readonly int[] Masks={1,2,4,65536,262144,524288,64,2};
    static readonly object Process=new object(), Pipe=new object();
    const int Pid=1234;
    static int checks;
    static void Check(bool ok) {checks++;if(!ok)throw new Exception("Assertion "+checks);}
    static void Reject(Action action)
    {try {action();}catch(StartupFailure){Check(true);return;}Check(false);}
    static byte[] Bytes(string value) {return Encoding.UTF8.GetBytes(value);}
    static byte[] Command(string role)
    {return Bytes("{\"v\":1,\"type\":\"journal_access_probe\",\"attempt\":\""+Attempt+"\",\"role\":\""+role+"\",\"request_id\":\""+Request+"\"}");}
    static JournalTokenAccessAdmission Owner(string role)
    {return new JournalTokenAccessAdmission(Process,Pipe,Attempt,role,Pid,Request,Control,ControlDirectory,Journal,Parent);}

    static byte[] Run(string role,string fault=null)
    {
        int calls=0;
        var session=new JournalTokenAccessFixture.ProbeSession(Attempt,role,Pid,Request);
        var reply=session.Execute(Command(role),(path,mask,share,disposition,flags)=>
        {
            int index=calls/2;bool control=calls++%2==0,directory=index>=6;
            string prefix=(role=="worker"?"host":"state")+"/journal-access-control";
            Check(path==(control?(directory?prefix:prefix+"/control.bin"):directory?".":"final-output-journal.v1.jsonl"));
            Check(mask==Masks[index] && share==7 && disposition==3 && flags==(directory?0x02200000:0x00200000));
            if(index!=0 || fault==null)
                return control?new JournalAccessStatus(true,true,0,directory?ControlDirectory:Control):new JournalAccessStatus(false,false,5,null);
            if(control)
            {
                if(fault=="control-denied" || fault=="open-without-control")return new JournalAccessStatus(false,false,5,null);
                return new JournalAccessStatus(true,fault!="control-close",0,fault=="control-id"?Journal:Control);
            }
            if(fault=="open" || fault=="open-without-control")return new JournalAccessStatus(true,false,0,Journal);
            return new JournalAccessStatus(false,false,fault=="share"?32:fault=="missing"?2:5,null);
        });
        Check(calls==16);
        Reject(()=>session.Execute(Command(role),(a,b,c,d,e)=>{throw new Exception("Repeated open");}));
        return reply;
    }
    static string[] Admit(JournalTokenAccessAdmission owner,byte[] raw,string fault=null)
    {
        return owner.Admit(raw,fault=="process"?new object():Process,fault=="pipe"?new object():Pipe,fault!="token",
            fault!="writer",fault!="eof",fault!="exit",fault=="before"?Control:Journal,Parent,Journal,
            fault=="parent"?ControlDirectory:Parent,fault!="modified");
    }

    static void Main()
    {
        foreach(string role in new[]{"worker","child"})
        {
            byte[] raw=Run(role);var owner=Owner(role);
            Check(Admit(owner,raw).SequenceEqual(Cases.Select(x=>x+":denied")));
            Reject(()=>Admit(owner,raw));
        }
        foreach(string fault in new[]{"control-denied","control-close","control-id","share","missing","open","open-without-control"})
        {
            var rows=Admit(Owner("worker"),Run("worker",fault));
            Check(rows[0]=="read_data:"+(fault.StartsWith("open",StringComparison.Ordinal)?"forbidden_open":"incomplete"));
            Check(rows.Skip(1).SequenceEqual(Cases.Skip(1).Select(x=>x+":denied")));
        }

        var source=Run("worker");string json=Encoding.UTF8.GetString(source);
        foreach(string fault in new[]{"process","pipe","token","writer","eof","exit","before","parent","modified"})
        {
            var owner=Owner("worker");Reject(()=>Admit(owner,source,fault));Reject(()=>Admit(owner,source));
        }
        foreach(string altered in new[]{json.Replace(Attempt,new string('0',32)),json.Replace(Request,new string('0',32)),
            json.Replace("\"pid\":1234","\"pid\":1235"),json.Replace("\"worker\"","\"child\""),
            json.Replace("\"case\":\"read_data\"","\"case\":\"append_data\""),json.Replace("\"mask\":1,","\"mask\":2,"),
            json.Replace("\"error\":5","\"error\":0"),json.Replace("\"opened\":false","\"opened\":false,\"opened\":false"),
            json.Replace("\"closed\":false","\"closed\":true"),json.Replace("\"error\":5","\"error\":65536"),
            json.Replace("\"identity\":null","\"identity\":\""+Journal+"\""),json.Substring(0,json.Length-4),json+"{}",
            json.Replace("\"rows\":[", "\"extra\":1,\"rows\":[")})
            Reject(()=>Admit(Owner("worker"),Bytes(altered)));
        var map=StrictJson.Parse(source);((List<object>)map["rows"]).RemoveAt(7);
        Reject(()=>Admit(Owner("worker"),Bytes(new JavaScriptSerializer().Serialize(map))));
        Reject(()=>Admit(Owner("worker"),new byte[8193]));
        Reject(()=>Admit(Owner("worker"),null));

        foreach(byte[] invalid in new[]{Command("child"),Bytes(Encoding.UTF8.GetString(Command("worker")).Replace("\"v\":1","\"v\":1,\"path\":\"other\"")),null})
        {
            var session=new JournalTokenAccessFixture.ProbeSession(Attempt,"worker",Pid,Request);
            JournalTokenAccessFixture.OpenClose never=(a,b,c,d,e)=>{throw new Exception("Invalid command caused open");};
            Reject(()=>session.Execute(invalid,never));Reject(()=>session.Execute(Command("worker"),never));
        }
        Console.WriteLine("Actual-token access inert fixture: "+checks+" assertions passed");
    }
}
