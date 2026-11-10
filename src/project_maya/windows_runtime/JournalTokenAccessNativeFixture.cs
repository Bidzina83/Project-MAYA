#if (MAYA_JOURNAL_TOKEN_ACCESS_FIXTURE && MAYA_JOURNAL_TOKEN_ACCESS_NATIVE_FIXTURE) || HERMES_JOURNAL_ACCESS
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Web.Script.Serialization;

namespace ProjectMaya.WindowsRuntime
{
#if MAYA_JOURNAL_TOKEN_ACCESS_NATIVE_FIXTURE
    internal interface IJournalTokenAccessNativeCalls
    {
        IntPtr Open(string path,int mask,int share,int disposition,int flags,out int error);
        string Identity(IntPtr handle,bool directory,out int error);
        bool Close(IntPtr handle);
    }

#endif
    internal sealed class JournalTokenAccessNativeFixture
    {
        const int Limit=8192;
#if MAYA_JOURNAL_TOKEN_ACCESS_NATIVE_FIXTURE
        const int InvalidData=13, GenericFailure=31;
        readonly object gate=new object();
        readonly string attempt,role,request,directory;
        readonly int pid;
        readonly IJournalTokenAccessNativeCalls calls;
        bool used;

        internal JournalTokenAccessNativeFixture(string attempt,string role,int pid,string request,IJournalTokenAccessNativeCalls calls)
        {
            Require(JournalTokenAccessFixture.Hex(attempt,32) && JournalTokenAccessFixture.Role(role) &&
                JournalTokenAccessFixture.Hex(request,32) && pid>0 && calls!=null);
            this.attempt=attempt;this.role=role;this.pid=pid;this.request=request;this.calls=calls;
            directory=Path.Combine(ProductFiles.Root,attempt);
        }

        static int Error(int value) {return BoundedError(value)?value:GenericFailure;}
#endif
        static void Require(bool ok) {JournalTokenAccessFixture.Require(ok);}
        static bool BoundedError(int value) {return value>=1 && value<=65535;}
        static Dictionary<string,object> Parse(byte[] raw)
        {Require(raw!=null && raw.Length>0 && raw.Length<=Limit);return StrictJson.Parse(raw);}
        static void Header(Dictionary<string,object> value,string type,string attempt,string role,string request)
        {
            Require(2.Equals(value["v"]) && type.Equals(value["type"]) && attempt.Equals(value["attempt"]) &&
                role.Equals(value["role"]) && request.Equals(value["request_id"]));
        }

        sealed class Status
        {
            internal readonly bool Opened, Closed;
            internal readonly int OpenError, IdentityError;
            internal readonly string Identity;
            internal Status(bool opened,bool closed,int openError,string identity,int identityError)
            {Opened=opened;Closed=closed;OpenError=openError;Identity=identity;IdentityError=identityError;}
            internal Dictionary<string,object> Fields()
            {return new Dictionary<string,object>{{"opened",Opened},{"closed",Closed},{"open_error",OpenError},
                {"identity",Identity},{"identity_error",IdentityError}};}
        }

#if MAYA_JOURNAL_TOKEN_ACCESS_NATIVE_FIXTURE
        Status Probe(int index,bool control)
        {
            string relative=JournalTokenAccessFixture.RelativePath(role,index,control);
            string path=relative=="."?directory:Path.Combine(directory,relative.Replace('/',Path.DirectorySeparatorChar));
            int error;
            IntPtr handle=calls.Open(path,JournalTokenAccessFixture.CaseMask(index),7,3,JournalTokenAccessFixture.CaseFlags(index),out error);
            if(handle==IntPtr.Zero || handle==new IntPtr(-1))return new Status(false,false,Error(error),null,0);

            string identity=null;int identityError=0;bool closed=false;
            try
            {
                int queryError;
                string observed=calls.Identity(handle,index>=6,out queryError);
                if(queryError==0 && JournalTokenAccessFixture.Hex(observed,24))identity=observed;
                else identityError=queryError==0?InvalidData:Error(queryError);
            }
            catch(Exception) {identityError=GenericFailure;}
            finally
            {
                try {closed=calls.Close(handle);}
                catch(Exception) {closed=false;}
            }
            return new Status(true,closed,0,identity,identityError);
        }

        internal byte[] Execute(byte[] command)
        {
            lock(gate)
            {
                Require(!used);used=true;
                var message=Parse(command);
                BridgeRuntime.Shape(message,"v","type","attempt","role","request_id");
                Header(message,"journal_access_probe",attempt,role,request);
                var rows=new List<object>();
                for(int i=0;i<JournalTokenAccessFixture.CaseCount;i++)
                    rows.Add(new Dictionary<string,object>{{"case",JournalTokenAccessFixture.CaseName(i)},
                        {"mask",JournalTokenAccessFixture.CaseMask(i)},{"control",Probe(i,true).Fields()},
                        {"target",Probe(i,false).Fields()}});
                var reply=new Dictionary<string,object>{{"v",2},{"type","journal_access_result"},{"attempt",attempt},
                    {"role",role},{"pid",pid},{"request_id",request},{"rows",rows}};
                byte[] raw=Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(reply));
                Require(raw.Length<=Limit);return raw;
            }
        }

#endif
        static Status ParseStatus(object value)
        {
            var status=value as Dictionary<string,object>;
            BridgeRuntime.Shape(status,"opened","closed","open_error","identity","identity_error");
            Require(status["opened"] is bool && status["closed"] is bool && status["open_error"] is int && status["identity_error"] is int);
            bool opened=(bool)status["opened"],closed=(bool)status["closed"];
            int open=(int)status["open_error"],identityError=(int)status["identity_error"];
            string identity=status["identity"] as string;
            if(opened)
                Require(open==0 && (identityError==0?JournalTokenAccessFixture.Hex(identity,24):
                    BoundedError(identityError) && status["identity"]==null));
            else Require(!closed && BoundedError(open) && status["identity"]==null && identityError==0);
            return new Status(opened,closed,open,identity,identityError);
        }

        internal static string[] Verify(byte[] reply,string attempt,string role,int pid,string request,string controlFile,string controlDirectory
#if HERMES_JOURNAL_ACCESS
            ,List<Dictionary<string,object>> incomplete=null
#endif
            )
        {
            var message=Parse(reply);
            BridgeRuntime.Shape(message,"v","type","attempt","role","pid","request_id","rows");
            Header(message,"journal_access_result",attempt,role,request);
            Require(pid.Equals(message["pid"]));
            var rows=message["rows"] as List<object>;
            Require(rows!=null && rows.Count==JournalTokenAccessFixture.CaseCount);
            var result=new string[rows.Count];
            for(int i=0;i<rows.Count;i++)
            {
                var row=rows[i] as Dictionary<string,object>;
                BridgeRuntime.Shape(row,"case","mask","control","target");
                string name=JournalTokenAccessFixture.CaseName(i);
                Require(name.Equals(row["case"]) && JournalTokenAccessFixture.CaseMask(i).Equals(row["mask"]));
                var control=ParseStatus(row["control"]);var target=ParseStatus(row["target"]);
                string expected=i<6?controlFile:controlDirectory;
                result[i]=name+":"+(target.Opened?"forbidden_open":control.Opened && control.Closed &&
                    control.IdentityError==0 && control.Identity==expected && target.OpenError==5?"denied":"incomplete");
#if HERMES_JOURNAL_ACCESS
                if(incomplete!=null && result[i]==name+":incomplete")
                    incomplete.Add(new Dictionary<string,object>{
                        {"case",name},{"control_opened",control.Opened},{"control_open_error",control.OpenError},
                        {"control_closed",control.Closed},{"control_identity_error",control.IdentityError},
                        {"control_identity_matches",control.Opened && control.IdentityError==0 && control.Identity==expected},
                        {"target_open_error",target.OpenError}
                    });
#endif
            }
            return result;
        }
    }

#if MAYA_JOURNAL_TOKEN_ACCESS_NATIVE_FIXTURE
    // Compiled only; injected tests never construct or invoke these native calls.
    internal sealed class JournalTokenAccessWindowsCalls : IJournalTokenAccessNativeCalls
    {
        [StructLayout(LayoutKind.Sequential)] struct FileInfo
        {
            internal uint Attributes;
            internal System.Runtime.InteropServices.ComTypes.FILETIME Creation,Access,Write;
            internal uint Volume,SizeHigh,SizeLow,Links,IdHigh,IdLow;
        }
        [DllImport("kernel32.dll",CharSet=CharSet.Unicode,ExactSpelling=true,SetLastError=true)] static extern IntPtr CreateFileW(
            string path,uint access,uint share,IntPtr attributes,uint disposition,uint flags,IntPtr template);
        [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandle(IntPtr handle,out FileInfo info);
        [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr handle);

        public IntPtr Open(string path,int mask,int share,int disposition,int flags,out int error)
        {
            IntPtr handle=CreateFileW(path,(uint)mask,(uint)share,IntPtr.Zero,(uint)disposition,(uint)flags,IntPtr.Zero);
            error=handle==new IntPtr(-1)?Marshal.GetLastWin32Error():0;
            return handle;
        }
        public string Identity(IntPtr handle,bool directory,out int error)
        {
            FileInfo info;
            if(!GetFileInformationByHandle(handle,out info)) {error=Marshal.GetLastWin32Error();return null;}
            if(((info.Attributes&16)!=0)!=directory || (info.Attributes&1024)!=0 || (!directory && info.Links!=1))
            {error=13;return null;}
            error=0;
            return info.Volume.ToString("x8",CultureInfo.InvariantCulture)+info.IdHigh.ToString("x8",CultureInfo.InvariantCulture)+
                info.IdLow.ToString("x8",CultureInfo.InvariantCulture);
        }
        public bool Close(IntPtr handle) {return CloseHandle(handle);}
    }
#endif
}
#endif
