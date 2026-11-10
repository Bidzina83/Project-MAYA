using System;
using System.IO;
using System.Linq;
using System.Web.Script.Serialization;
using ProjectMaya.WindowsRuntime;

internal static class JournalTokenAccessPythonParity
{
    public sealed class Vector
    {
        public string role {get;set;}
        public string frame {get;set;}
        public string[] expected {get;set;}
    }
    static readonly string Attempt=new string('a',32),Request=new string('b',32),Control=new string('c',24),
        ControlDirectory=new string('d',24),Journal=new string('e',24),Parent=new string('f',24);
    static int checks;
    static void Check(bool ok) {checks++;if(!ok)throw new Exception("Assertion "+checks);}
    static void Reject(Action action)
    {try {action();}catch(StartupFailure){Check(true);return;}Check(false);}
    static void Main(string[] args)
    {
        var data=new JavaScriptSerializer().Deserialize<Vector[]>(File.ReadAllText(args[0]));
        Check(data.Length==20 && data.Count(x=>x.role=="worker")==10 && data.Count(x=>x.role=="child")==10);
        foreach(var vector in data)
        {
            byte[] frame=Convert.FromBase64String(vector.frame);
            Check(frame.Length>=5 && frame.Length<=8196 && BitConverter.ToInt32(frame,0)==frame.Length-4);
            byte[] raw=frame.Skip(4).ToArray();
            var process=new object();var pipe=new object();
            var owner=new JournalTokenAccessAdmission(process,pipe,Attempt,vector.role,1234,Request,
                Control,ControlDirectory,Journal,Parent);
            var result=owner.AdmitNative(raw,process,pipe,true,true,true,true,Journal,Parent,Journal,Parent,true);
            Check(result.SequenceEqual(vector.expected));
            Reject(()=>owner.AdmitNative(raw,process,pipe,true,true,true,true,Journal,Parent,Journal,Parent,true));
        }
        Console.WriteLine("Python/C# v2 parity: "+data.Length+" vectors, "+checks+" assertions passed");
    }
}
