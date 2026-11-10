#if MAYA_JOURNAL_TOKEN_ACCESS_FIXTURE || HERMES_JOURNAL_ACCESS
using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

namespace ProjectMaya.WindowsRuntime
{
#if MAYA_JOURNAL_TOKEN_ACCESS_FIXTURE
    internal sealed class JournalAccessStatus
    {
        internal readonly bool Opened, Closed;
        internal readonly int Error;
        internal readonly string Identity;
        internal JournalAccessStatus(bool opened,bool closed,int error,string identity)
        {Opened=opened;Closed=closed;Error=error;Identity=identity;}
        internal Dictionary<string,object> Fields()
        {return new Dictionary<string,object>{{"opened",Opened},{"closed",Closed},{"error",Error},{"identity",Identity}};}
    }

#endif
    internal static class JournalTokenAccessFixture
    {
        const string Leaf="final-output-journal.v1.jsonl";
        static readonly string[] Cases={"read_data","write_data","append_data","delete","write_dacl","write_owner","delete_child","add_file"};
        static readonly int[] Masks={1,2,4,65536,262144,524288,64,2};

        internal static bool Hex(string value,int count)
        {return value!=null && value.Length==count && Regex.IsMatch(value,"\\A[0-9a-f]+\\z");}
        internal static void Require(bool ok)
        {if(!ok)throw new StartupFailure("journal_access_invalid_evidence");}
        internal static bool Role(string role) {return role=="worker" || role=="child";}
        internal static int CaseCount {get{return Cases.Length;}}
        internal static string CaseName(int index) {return Cases[index];}
        internal static int CaseMask(int index) {return Masks[index];}
        internal static int CaseFlags(int index) {return 0x00200000|(index>=6?0x02000000:0);}
        internal static string RelativePath(string role,int index,bool control)
        {
            if(!control)return index>=6?".":Leaf;
            string directory=(role=="worker"?"host":"state")+"/journal-access-control";
            return index>=6?directory:directory+"/control.bin";
        }
#if MAYA_JOURNAL_TOKEN_ACCESS_FIXTURE
        const int Limit=8192;
        static readonly UTF8Encoding Utf8=new UTF8Encoding(false,true);
        internal delegate JournalAccessStatus OpenClose(string fixedRelativePath,int mask,int share,int disposition,int flags);
        static void Header(Dictionary<string,object> value,string type,string attempt,string role,string request)
        {
            Require(1.Equals(value["v"]) && type.Equals(value["type"]) && attempt.Equals(value["attempt"]) &&
                role.Equals(value["role"]) && request.Equals(value["request_id"]));
        }
        static Dictionary<string,object> Parse(byte[] raw)
        {Require(raw!=null && raw.Length>0 && raw.Length<=Limit);return StrictJson.Parse(raw);}

        internal sealed class ProbeSession
        {
            readonly object gate=new object();
            readonly string attempt,role,request;
            readonly int pid;
            bool used;
            internal ProbeSession(string attempt,string role,int pid,string request)
            {
                Require(Hex(attempt,32) && Role(role) && Hex(request,32) && pid>0);
                this.attempt=attempt;this.role=role;this.pid=pid;this.request=request;
            }
            internal byte[] Execute(byte[] command,OpenClose open)
            {
                lock(gate)
                {
                    Require(!used);used=true;
                    return Run(command,attempt,role,pid,request,open);
                }
            }
        }

        static byte[] Run(byte[] command,string attempt,string role,int pid,string request,OpenClose open)
        {
            Require(Hex(attempt,32) && Role(role) && Hex(request,32) && pid>0 && open!=null);
            var message=Parse(command);
            BridgeRuntime.Shape(message,"v","type","attempt","role","request_id");
            Header(message,"journal_access_probe",attempt,role,request);
            var rows=new List<object>();
            for(int i=0;i<Cases.Length;i++)
            {
                int flags=CaseFlags(i);
                var positive=open(RelativePath(role,i,true),Masks[i],7,3,flags);
                var target=open(RelativePath(role,i,false),Masks[i],7,3,flags);
                Require(positive!=null && target!=null);
                rows.Add(new Dictionary<string,object>{{"case",Cases[i]},{"mask",Masks[i]},
                    {"control",positive.Fields()},{"target",target.Fields()}});
            }
            var reply=new Dictionary<string,object>{{"v",1},{"type","journal_access_result"},{"attempt",attempt},
                {"role",role},{"pid",pid},{"request_id",request},{"rows",rows}};
            byte[] raw=Utf8.GetBytes(new JavaScriptSerializer().Serialize(reply));
            Require(raw.Length<=Limit);return raw;
        }

        static JournalAccessStatus Status(object value)
        {
            var status=value as Dictionary<string,object>;
            BridgeRuntime.Shape(status,"opened","closed","error","identity");
            Require(status["opened"] is bool && status["closed"] is bool && status["error"] is int);
            bool opened=(bool)status["opened"],closed=(bool)status["closed"];int error=(int)status["error"];
            string identity=status["identity"] as string;
            Require(opened?error==0 && Hex(identity,24):!closed && error>=1 && error<=65535 && status["identity"]==null);
            return new JournalAccessStatus(opened,closed,error,identity);
        }

        internal static string[] Verify(byte[] reply,string attempt,string role,int pid,string request,string controlFile,string controlDirectory)
        {
            var message=Parse(reply);
            BridgeRuntime.Shape(message,"v","type","attempt","role","pid","request_id","rows");
            Header(message,"journal_access_result",attempt,role,request);
            Require(pid.Equals(message["pid"]));
            var rows=message["rows"] as List<object>;
            Require(rows!=null && rows.Count==Cases.Length);
            var result=new string[Cases.Length];
            for(int i=0;i<Cases.Length;i++)
            {
                var row=rows[i] as Dictionary<string,object>;
                BridgeRuntime.Shape(row,"case","mask","control","target");
                Require(Cases[i].Equals(row["case"]) && Masks[i].Equals(row["mask"]));
                var control=Status(row["control"]);var target=Status(row["target"]);
                string expected=i<6?controlFile:controlDirectory;
                string outcome=target.Opened?"forbidden_open":control.Opened && control.Closed && control.Identity==expected &&
                    target.Error==5?"denied":"incomplete";
                result[i]=Cases[i]+":"+outcome;
            }
            return result;
        }
#endif
    }

    // Only a trusted owner can supply original launch objects and opened-file observations.
    internal sealed class JournalTokenAccessAdmission
    {
        readonly object gate=new object(), process, pipe;
        readonly string attempt,role,request,controlFile,controlDirectory,journal,parent;
        readonly int pid;
        bool used;
        internal JournalTokenAccessAdmission(object process,object pipe,string attempt,string role,int pid,string request,
            string controlFile,string controlDirectory,string journal,string parent)
        {
            JournalTokenAccessFixture.Require(process!=null && pipe!=null && pid>0 && JournalTokenAccessFixture.Role(role) &&
                JournalTokenAccessFixture.Hex(attempt,32) && JournalTokenAccessFixture.Hex(request,32));
            foreach(string id in new[]{controlFile,controlDirectory,journal,parent})JournalTokenAccessFixture.Require(JournalTokenAccessFixture.Hex(id,24));
            JournalTokenAccessFixture.Require(new HashSet<string>{controlFile,controlDirectory,journal,parent}.Count==4);
            this.process=process;this.pipe=pipe;this.attempt=attempt;this.role=role;this.pid=pid;this.request=request;
            this.controlFile=controlFile;this.controlDirectory=controlDirectory;this.journal=journal;this.parent=parent;
        }

#if MAYA_JOURNAL_TOKEN_ACCESS_FIXTURE
        internal string[] Admit(byte[] reply,object actualProcess,object actualPipe,bool actualRoleTokenVerified,
            bool writerClosedAndNoInheritance,bool cleanEof,bool naturalExitBeforeCleanup,string journalBefore,string parentBefore,
            string journalAfter,string parentAfter,bool exactDescriptorAndBytesUnchanged)
        {return AdmitCore(reply,actualProcess,actualPipe,actualRoleTokenVerified,writerClosedAndNoInheritance,cleanEof,
            naturalExitBeforeCleanup,journalBefore,parentBefore,journalAfter,parentAfter,exactDescriptorAndBytesUnchanged,false);}

#endif
#if MAYA_JOURNAL_TOKEN_ACCESS_NATIVE_FIXTURE || HERMES_JOURNAL_ACCESS
        internal string[] AdmitNative(byte[] reply,object actualProcess,object actualPipe,bool actualRoleTokenVerified,
            bool writerClosedAndNoInheritance,bool cleanEof,bool naturalExitBeforeCleanup,string journalBefore,string parentBefore,
            string journalAfter,string parentAfter,bool exactDescriptorAndBytesUnchanged
#if HERMES_JOURNAL_ACCESS
            ,List<Dictionary<string,object>> incomplete=null
#endif
            )
        {return AdmitCore(reply,actualProcess,actualPipe,actualRoleTokenVerified,writerClosedAndNoInheritance,cleanEof,
            naturalExitBeforeCleanup,journalBefore,parentBefore,journalAfter,parentAfter,exactDescriptorAndBytesUnchanged,true
#if HERMES_JOURNAL_ACCESS
            ,incomplete
#endif
            );}
#endif

        string[] AdmitCore(byte[] reply,object actualProcess,object actualPipe,bool actualRoleTokenVerified,
            bool writerClosedAndNoInheritance,bool cleanEof,bool naturalExitBeforeCleanup,string journalBefore,string parentBefore,
            string journalAfter,string parentAfter,bool exactDescriptorAndBytesUnchanged,bool native
#if HERMES_JOURNAL_ACCESS
            ,List<Dictionary<string,object>> incomplete
#endif
            )
        {
            lock(gate)
            {
                JournalTokenAccessFixture.Require(!used);used=true;
                JournalTokenAccessFixture.Require(object.ReferenceEquals(process,actualProcess) && object.ReferenceEquals(pipe,actualPipe) &&
                    actualRoleTokenVerified && writerClosedAndNoInheritance && cleanEof && naturalExitBeforeCleanup &&
                    journal==journalBefore && journal==journalAfter && parent==parentBefore && parent==parentAfter && exactDescriptorAndBytesUnchanged);
#if HERMES_JOURNAL_ACCESS
                JournalTokenAccessFixture.Require(native);
                return JournalTokenAccessNativeFixture.Verify(reply,attempt,role,pid,request,controlFile,controlDirectory,incomplete);
#else
#if MAYA_JOURNAL_TOKEN_ACCESS_NATIVE_FIXTURE
                if(native)return JournalTokenAccessNativeFixture.Verify(reply,attempt,role,pid,request,controlFile,controlDirectory);
#endif
                return JournalTokenAccessFixture.Verify(reply,attempt,role,pid,request,controlFile,controlDirectory);
#endif
            }
        }
    }
}
#endif
