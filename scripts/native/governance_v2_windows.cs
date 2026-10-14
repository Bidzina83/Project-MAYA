// Gate A only. Uses native LPAC/WFP APIs; never a production launcher.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;

public static class GateANative
{
    [StructLayout(LayoutKind.Sequential)] struct Display { public IntPtr name, description; }
    [StructLayout(LayoutKind.Sequential)] struct Blob { public uint size; public IntPtr data; }
    [StructLayout(LayoutKind.Explicit)] struct Scalar {
        [FieldOffset(0)] public byte u8; [FieldOffset(0)] public ushort u16;
        [FieldOffset(0)] public uint u32; [FieldOffset(0)] public IntPtr pointer;
    }
    [StructLayout(LayoutKind.Sequential)] struct Value { public uint type; public Scalar data; }
    [StructLayout(LayoutKind.Sequential)] struct Condition { public Guid key; public uint match; public Value value; }
    [StructLayout(LayoutKind.Sequential)] struct Action { public uint type; public Guid key; }
    [StructLayout(LayoutKind.Explicit, Size=16)] struct Context { [FieldOffset(0)] public ulong raw; }
    [StructLayout(LayoutKind.Sequential)] struct Filter {
        public Guid key; public Display display; public uint flags; public IntPtr provider;
        public Blob data; public Guid layer, sublayer; public Value weight; public uint count;
        public IntPtr conditions; public Action action; public Context context; public IntPtr reserved;
        public ulong id; public Value effectiveWeight;
    }
    [StructLayout(LayoutKind.Sequential)] struct Sublayer {
        public Guid key; public Display display; public uint flags; public IntPtr provider;
        public Blob data; public ushort weight;
    }
    [StructLayout(LayoutKind.Sequential)] struct SidAttributes { public IntPtr sid; public uint attributes; }
    [StructLayout(LayoutKind.Sequential)] struct Capabilities {
        public IntPtr sid, capabilities; public uint count, reserved;
    }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct Startup {
        public uint size; public IntPtr reserved, desktop, title;
        public uint x,y,xSize,ySize,xChars,yChars,fill,flags; public ushort show,reservedSize;
        public IntPtr reservedBytes, input, output, error;
    }
    [StructLayout(LayoutKind.Sequential)] struct StartupEx { public Startup startup; public IntPtr attributes; }
    [StructLayout(LayoutKind.Sequential)] struct ProcessInfo { public IntPtr process, thread; public uint pid, tid; }
    [StructLayout(LayoutKind.Sequential)] struct SecurityAttributes { public uint size; public IntPtr descriptor; public int inherit; }
    [StructLayout(LayoutKind.Sequential)] struct BasicLimits {
        public long processTime, jobTime; public uint flags; public UIntPtr minWorkingSet,maxWorkingSet;
        public uint activeProcessLimit; public UIntPtr affinity; public uint priority,scheduling;
    }
    [StructLayout(LayoutKind.Sequential)] struct IoCounters { public ulong readOps,writeOps,otherOps,readBytes,writeBytes,otherBytes; }
    [StructLayout(LayoutKind.Sequential)] struct JobLimits {
        public BasicLimits basic; public IoCounters io; public UIntPtr processMemory,jobMemory,peakProcess,peakJob;
    }
    [StructLayout(LayoutKind.Sequential)] struct GenericMapping { public uint read,write,execute,all; }
    [DllImport("userenv.dll", CharSet=CharSet.Unicode)] static extern int CreateAppContainerProfile(string name,string display,string description,IntPtr caps,uint count,out IntPtr sid);
    [DllImport("userenv.dll", CharSet=CharSet.Unicode)] static extern int DeriveAppContainerSidFromAppContainerName(string name,out IntPtr sid);
    [DllImport("userenv.dll", CharSet=CharSet.Unicode)] static extern int DeleteAppContainerProfile(string name);
    [DllImport("advapi32.dll")] static extern IntPtr FreeSid(IntPtr sid);
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool ConvertStringSidToSid(string text,out IntPtr sid);
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool ConvertStringSecurityDescriptorToSecurityDescriptor(string text,uint revision,out IntPtr descriptor,out uint size);
    [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr memory);
    [DllImport("fwpuclnt.dll")] static extern uint FwpmEngineOpen0(IntPtr server,uint auth,IntPtr identity,IntPtr session,out IntPtr engine);
    [DllImport("fwpuclnt.dll")] static extern uint FwpmEngineClose0(IntPtr engine);
    [DllImport("fwpuclnt.dll")] static extern uint FwpmTransactionBegin0(IntPtr engine,uint flags);
    [DllImport("fwpuclnt.dll")] static extern uint FwpmTransactionCommit0(IntPtr engine);
    [DllImport("fwpuclnt.dll")] static extern uint FwpmTransactionAbort0(IntPtr engine);
    [DllImport("fwpuclnt.dll")] static extern uint FwpmSubLayerAdd0(IntPtr engine,ref Sublayer layer,IntPtr security);
    [DllImport("fwpuclnt.dll")] static extern uint FwpmSubLayerDeleteByKey0(IntPtr engine,ref Guid key);
    [DllImport("fwpuclnt.dll")] static extern uint FwpmFilterAdd0(IntPtr engine,ref Filter filter,IntPtr security,out ulong id);
    [DllImport("fwpuclnt.dll")] static extern uint FwpmFilterGetByKey0(IntPtr engine,ref Guid key,out IntPtr filter);
    [DllImport("fwpuclnt.dll")] static extern uint FwpmFilterDeleteByKey0(IntPtr engine,ref Guid key);
    [DllImport("fwpuclnt.dll")] static extern void FwpmFreeMemory0(ref IntPtr pointer);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool InitializeProcThreadAttributeList(IntPtr list,int count,uint flags,ref UIntPtr size);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool UpdateProcThreadAttribute(IntPtr list,uint flags,IntPtr attribute,IntPtr value,UIntPtr size,IntPtr previous,IntPtr returned);
    [DllImport("kernel32.dll")] static extern void DeleteProcThreadAttributeList(IntPtr list);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateProcessW(string app,StringBuilder command,IntPtr ps,IntPtr ts,bool inherit,uint flags,IntPtr environment,string cwd,ref StartupEx startup,out ProcessInfo info);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateJobObject(IntPtr security,string name);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job,int type,ref JobLimits data,uint length);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
    [DllImport("kernel32.dll",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll")] static extern uint WaitForSingleObject(IntPtr handle,uint milliseconds);
    [DllImport("kernel32.dll")] static extern bool GetExitCodeProcess(IntPtr process,out uint code);
    [DllImport("kernel32.dll")] static extern bool TerminateProcess(IntPtr process,uint code);
    [DllImport("kernel32.dll")] static extern bool TerminateJobObject(IntPtr job,uint code);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool CreatePipe(out IntPtr read,out IntPtr write,ref SecurityAttributes attrs,uint size);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetHandleInformation(IntPtr handle,uint mask,uint flags);
    [DllImport("advapi32.dll",SetLastError=true)] static extern bool OpenProcessToken(IntPtr process,uint access,out IntPtr token);
    [DllImport("advapi32.dll",SetLastError=true)] static extern bool GetTokenInformation(IntPtr token,int type,IntPtr data,uint length,out uint required);
    [DllImport("advapi32.dll",SetLastError=true)] static extern bool DuplicateToken(IntPtr token,int level,out IntPtr duplicate);
    [DllImport("advapi32.dll",SetLastError=true)] static extern bool AccessCheck(IntPtr descriptor,IntPtr token,uint desired,
        ref GenericMapping mapping,IntPtr privileges,ref uint privilegeLength,out uint granted,out bool status);

    static Guid G(string value) { return new Guid(value); }
    static readonly Guid Connect4=G("c38d57d1-05a7-4c33-904f-7fbceee60e82"), Connect6=G("4a72393b-319f-44bc-84c3-ba54dcb3b6b4");
    static readonly Guid Listen4=G("88bb5dad-76d7-4227-9c71-df0a3ed7be7e"), Listen6=G("7ac9de24-17dd-4814-b4bd-a9fbc95a321b");
    static readonly Guid Receive4=G("e1cd9fe7-f4b5-4273-96c0-592e487b8650"), Receive6=G("a3b42c97-9f04-4672-b87e-cee9c483257f");
    static readonly Guid Package=G("71bc78fa-f17c-4997-a602-6abb261f351c"), Protocol=G("3971ef2b-623e-4f9a-8cb1-6e79b806b9a7");
    static readonly Guid Address=G("b235ae9a-1d64-49b8-a44c-5ff3d9095045"), Port=G("c35a604d-d22b-4e1a-91b4-68f674ee674b");
    static string root, profile; static ushort port;
    static Guid Key(string label) {
        using (var hash=SHA256.Create()) {
            byte[] all=hash.ComputeHash(Encoding.UTF8.GetBytes(profile+":"+label));
            byte[] bytes=new byte[16]; Array.Copy(all,bytes,16); return new Guid(bytes);
        }
    }
    static void Check(uint code,string op) { if(code!=0) throw new InvalidOperationException(op+":"+code); }
    static void Bool(bool value,string op) { if(!value) throw new InvalidOperationException(op+":"+Marshal.GetLastWin32Error()); }
    static string Quote(string text) { if(text.Contains("\"") || text.Contains("\n")) throw new ArgumentException("native.bad_argument"); return "\""+text+"\""; }
    static void ValidateRoot(string path) {
        root=Path.GetFullPath(path).TrimEnd(Path.DirectorySeparatorChar);
        string expected=Path.GetFullPath(Path.Combine(Environment.CurrentDirectory,".codex-build","governance-v2-lpac-stage"));
        if(!String.Equals(root,expected,StringComparison.OrdinalIgnoreCase)) throw new ArgumentException("native.workspace_mismatch");
        DirectoryInfo cursor=new DirectoryInfo(root);
        while(cursor!=null) {
            if(cursor.Exists && (cursor.Attributes&FileAttributes.ReparsePoint)!=0) throw new ArgumentException("native.reparse_root");
            cursor=cursor.Parent;
        }
        profile="Maya.GateA."+KeyForName(root+WindowsIdentity.GetCurrent().User.Value);
    }
    static string KeyForName(string text) {
        using(var hash=SHA256.Create()) return BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(text))).Replace("-","").Substring(0,16);
    }
    static IntPtr Sid() { IntPtr sid; Check(unchecked((uint)DeriveAppContainerSidFromAppContainerName(profile,out sid)),"native.derive_sid"); return sid; }
    static Condition SidCondition(IntPtr sid) { return new Condition {key=Package,match=0,value=new Value {type=13,data=new Scalar {pointer=sid}}}; }
    static Condition Number(Guid field,uint type,uint number) { return new Condition {key=field,match=10,value=new Value {type=type,data=new Scalar {u32=number}}}; }
    static List<Filter> Filters(IntPtr sid) {
        var result=new List<Filter>();
        // Complementary block predicates avoid an allow rule overriding a deny.
        AddFilter(result,Connect4,sid,Number(Protocol,1,6));
        AddFilter(result,Connect4,sid,Number(Address,3,0x7f000001));
        AddFilter(result,Connect4,sid,Number(Port,2,port));
        foreach(Guid layer in new[]{Connect6,Listen4,Listen6,Receive4,Receive6}) AddFilter(result,layer,sid,null);
        return result;
    }
    static void AddFilter(List<Filter> filters,Guid layer,IntPtr sid,Condition? extra) {
        var conditions=new List<Condition>(); conditions.Add(SidCondition(sid)); if(extra.HasValue) conditions.Add(extra.Value);
        int size=Marshal.SizeOf(typeof(Condition)); IntPtr memory=Marshal.AllocHGlobal(size*conditions.Count);
        for(int i=0;i<conditions.Count;i++) Marshal.StructureToPtr(conditions[i],IntPtr.Add(memory,i*size),false);
        filters.Add(new Filter {key=Key("filter-"+filters.Count),layer=layer,sublayer=Key("sublayer"),
            display=new Display {name=Marshal.StringToHGlobalUni("Maya Gate A deny "+filters.Count)},
            flags=1,count=(uint)conditions.Count,conditions=memory,action=new Action {type=0x1001}});
    }
    static void FreeFilters(List<Filter> filters) { foreach(var f in filters) { Marshal.FreeHGlobal(f.conditions); Marshal.FreeHGlobal(f.display.name); } }
    static void Verify(IntPtr engine,IntPtr sid) {
        var expected=Filters(sid);
        try { foreach(var want in expected) {
            IntPtr pointer; Guid key=want.key; Check(FwpmFilterGetByKey0(engine,ref key,out pointer),"native.missing_filter");
            try {
                var got=(Filter)Marshal.PtrToStructure(pointer,typeof(Filter));
                if(got.key!=want.key || got.layer!=want.layer || got.sublayer!=want.sublayer)
                    throw new InvalidOperationException("native.filter_key_mismatch");
                // Windows adds the documented INDEXED flag; it does not change
                // the action. No disabled, permit or unknown flags are accepted.
                if((got.flags & ~0x40u)!=1) throw new InvalidOperationException("native.filter_flags_mismatch:"+got.flags);
                if(got.action.type!=0x1001) throw new InvalidOperationException("native.filter_action_mismatch:"+got.action.type);
                if(got.provider!=IntPtr.Zero) throw new InvalidOperationException("native.filter_provider_mismatch");
                if(got.count!=want.count) throw new InvalidOperationException("native.filter_count_mismatch:"+got.count);
                for(int i=0;i<got.count;i++) {
                    int size=Marshal.SizeOf(typeof(Condition));
                    var a=(Condition)Marshal.PtrToStructure(IntPtr.Add(got.conditions,i*size),typeof(Condition));
                    var b=(Condition)Marshal.PtrToStructure(IntPtr.Add(want.conditions,i*size),typeof(Condition));
                    if(a.key!=b.key || a.match!=b.match || a.value.type!=b.value.type)
                        throw new InvalidOperationException("native.condition_mismatch");
                    if(a.value.type==13) {
                        if(new SecurityIdentifier(a.value.data.pointer).Value!=new SecurityIdentifier(sid).Value)
                            throw new InvalidOperationException("native.sid_mismatch");
                    } else if(a.value.data.u32!=b.value.data.u32) throw new InvalidOperationException("native.value_mismatch");
                }
            } finally { FwpmFreeMemory0(ref pointer); }
        }} finally { FreeFilters(expected); }
    }
    static void RunSystem(string file,string arguments) {
        var start=new ProcessStartInfo(file,arguments) {UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true};
        using(var process=Process.Start(start)) {
            process.StandardOutput.ReadToEnd(); process.StandardError.ReadToEnd();
            if(!process.WaitForExit(30000) || process.ExitCode!=0) throw new InvalidOperationException("native.system_action_failed");
        }
    }
    static void AbandonUnprovisioned() {
        IntPtr sid=Sid(),engine=IntPtr.Zero;
        try {
            Check(FwpmEngineOpen0(IntPtr.Zero,10,IntPtr.Zero,IntPtr.Zero,out engine),"native.engine");
            for(int i=0;i<8;i++) {
                Guid key=Key("filter-"+i);IntPtr found;uint code=FwpmFilterGetByKey0(engine,ref key,out found);
                if(code==0) {FwpmFreeMemory0(ref found);throw new InvalidOperationException("native.profile_has_filters");}
                if(code!=0x80320003) Check(code,"native.filter_inspection");
            }
            var start=new ProcessStartInfo(Path.Combine(Environment.SystemDirectory,"CheckNetIsolation.exe"),"LoopbackExempt -s") {
                UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true};
            using(var process=Process.Start(start)) {
                string output=process.StandardOutput.ReadToEnd();process.StandardError.ReadToEnd();process.WaitForExit();
                if(process.ExitCode!=0 || output.Contains(new SecurityIdentifier(sid).Value))
                    throw new InvalidOperationException("native.profile_exemption_unknown");
            }
            Check(unchecked((uint)DeleteAppContainerProfile(profile)),"native.delete_unprovisioned_profile");
        } finally {if(engine!=IntPtr.Zero) FwpmEngineClose0(engine);FreeSid(sid);}
    }
    static void Report(object value) {
        string json=new JavaScriptSerializer().Serialize(value);
        if(root!=null && Directory.Exists(Path.Combine(root,"host")))
            File.WriteAllText(Path.Combine(root,"host","native-operation.json"),json,Encoding.UTF8);
        Console.WriteLine(json);
    }
    static void Grant(string directory,SecurityIdentifier sid,FileSystemRights rights) {
        if(!Directory.Exists(directory)) throw new InvalidOperationException("native.stage_missing");
        foreach(string item in Directory.EnumerateFileSystemEntries("\\\\?\\"+directory,"*",SearchOption.AllDirectories))
            if((File.GetAttributes(item)&FileAttributes.ReparsePoint)!=0) throw new InvalidOperationException("native.stage_reparse");
        var acl=Directory.GetAccessControl(directory);
        acl.AddAccessRule(new FileSystemAccessRule(sid,rights,InheritanceFlags.ContainerInherit|InheritanceFlags.ObjectInherit,PropagationFlags.None,AccessControlType.Allow));
        Directory.SetAccessControl(directory,acl);
    }
    static void Provision() {
        IntPtr sid; int hr=CreateAppContainerProfile(profile,"Maya Gate A test","Isolated synthetic-data evaluation",IntPtr.Zero,0,out sid);
        if(hr!=0) throw new InvalidOperationException("native.profile_create:"+unchecked((uint)hr));
        IntPtr engine=IntPtr.Zero,descriptor=IntPtr.Zero; var filters=Filters(sid);
        try {
            uint descriptorSize;
            string sddl="O:BAG:BAD:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;0x20080;;;"+WindowsIdentity.GetCurrent().User.Value+")";
            Bool(ConvertStringSecurityDescriptorToSecurityDescriptor(sddl,1,out descriptor,out descriptorSize),"native.policy_security_descriptor");
            Check(FwpmEngineOpen0(IntPtr.Zero,10,IntPtr.Zero,IntPtr.Zero,out engine),"native.engine");
            Check(FwpmTransactionBegin0(engine,0),"native.begin");
            try {
                var sub=new Sublayer {key=Key("sublayer"),flags=1,weight=65535,
                    display=new Display {name=Marshal.StringToHGlobalUni("Maya Gate A isolated deny policy")}};
                try {Check(FwpmSubLayerAdd0(engine,ref sub,descriptor),"native.sublayer");} finally {Marshal.FreeHGlobal(sub.display.name);}
                foreach(var item in filters) { var filter=item; ulong id; Check(FwpmFilterAdd0(engine,ref filter,descriptor,out id),"native.filter"); }
                Check(FwpmTransactionCommit0(engine),"native.commit");
            } catch { FwpmTransactionAbort0(engine); throw; }
            Verify(engine,sid);
            var identity=new SecurityIdentifier(sid);
            Grant(Path.Combine(root,"runtime"),identity,FileSystemRights.ReadAndExecute);
            Grant(Path.Combine(root,"state"),identity,FileSystemRights.Modify);
            RunSystem(Path.Combine(Environment.SystemDirectory,"icacls.exe"),Quote(Path.Combine(root,"state"))+" /setintegritylevel (OI)(CI)L /T /Q");
            // The exemption is profile-specific, and is installed only after deny filters.
            RunSystem(Path.Combine(Environment.SystemDirectory,"CheckNetIsolation.exe"),"LoopbackExempt -a -n="+profile);
        } finally { FreeFilters(filters); if(engine!=IntPtr.Zero) FwpmEngineClose0(engine);if(descriptor!=IntPtr.Zero) LocalFree(descriptor); FreeSid(sid); }
    }
    static void FinishProvision() {
        IntPtr sid=Sid(),engine=IntPtr.Zero;
        try {
            Check(FwpmEngineOpen0(IntPtr.Zero,10,IntPtr.Zero,IntPtr.Zero,out engine),"native.engine");Verify(engine,sid);
            var identity=new SecurityIdentifier(sid);
            Grant(Path.Combine(root,"runtime"),identity,FileSystemRights.ReadAndExecute);
            Grant(Path.Combine(root,"state"),identity,FileSystemRights.Modify);
            RunSystem(Path.Combine(Environment.SystemDirectory,"icacls.exe"),Quote(Path.Combine(root,"state"))+" /setintegritylevel (OI)(CI)L /T /Q");
            RunSystem(Path.Combine(Environment.SystemDirectory,"CheckNetIsolation.exe"),"LoopbackExempt -a -n="+profile);
        } finally {if(engine!=IntPtr.Zero) FwpmEngineClose0(engine);FreeSid(sid);}
    }
    static void Cleanup() {
        IntPtr sid=Sid(),engine=IntPtr.Zero;
        try {
            RunSystem(Path.Combine(Environment.SystemDirectory,"CheckNetIsolation.exe"),"LoopbackExempt -d -n="+profile);
            Check(FwpmEngineOpen0(IntPtr.Zero,10,IntPtr.Zero,IntPtr.Zero,out engine),"native.engine");
            Check(FwpmTransactionBegin0(engine,0),"native.begin");
            try {
                for(int i=0;i<8;i++) { Guid key=Key("filter-"+i); uint code=FwpmFilterDeleteByKey0(engine,ref key); if(code!=0 && code!=0x80320003) Check(code,"native.delete_filter"); }
                Guid sub=Key("sublayer"); uint subCode=FwpmSubLayerDeleteByKey0(engine,ref sub); if(subCode!=0 && subCode!=0x80320007) Check(subCode,"native.delete_sublayer");
                Check(FwpmTransactionCommit0(engine),"native.commit");
            } catch {FwpmTransactionAbort0(engine);throw;}
            var identity=new SecurityIdentifier(sid);
            foreach(string directory in new[]{Path.Combine(root,"runtime"),Path.Combine(root,"state")}) {
                var acl=Directory.GetAccessControl(directory);acl.PurgeAccessRules(identity);Directory.SetAccessControl(directory,acl);
            }
            RunSystem(Path.Combine(Environment.SystemDirectory,"icacls.exe"),Quote(Path.Combine(root,"state"))+" /setintegritylevel (OI)(CI)M /T /Q");
            Check(unchecked((uint)DeleteAppContainerProfile(profile)),"native.delete_profile");
        } finally {if(engine!=IntPtr.Zero) FwpmEngineClose0(engine);FreeSid(sid);}
    }
    static bool AccessProbe(IntPtr duplicate,string packageGrant) {
        IntPtr descriptor=IntPtr.Zero,privileges=Marshal.AllocHGlobal(256);
        try {
            // The first ACE satisfies the ordinary user check; the second is
            // the synthetic AppContainer restricted-principal grant under test.
            string user=WindowsIdentity.GetCurrent().User.Value;
            string sddl="O:BAG:BAD:P(A;;0x1;;;"+user+")";
            if(packageGrant!=null) sddl += "(A;;0x1;;;"+packageGrant+")";
            uint size;Bool(ConvertStringSecurityDescriptorToSecurityDescriptor(sddl,1,out descriptor,out size),"native.probe_descriptor");
            var mapping=new GenericMapping {read=1,write=2,execute=4,all=7};
            uint privilegeLength=256,granted;bool status;
            Bool(AccessCheck(descriptor,duplicate,1,ref mapping,privileges,ref privilegeLength,out granted,out status),"native.access_probe_api");
            if(privilegeLength>256 || (status ? granted!=1 : granted!=0))
                throw new InvalidOperationException("native.access_probe_result");
            return status;
        } finally {
            bool descriptorFreed=descriptor==IntPtr.Zero || LocalFree(descriptor)==IntPtr.Zero;
            Marshal.FreeHGlobal(privileges);
            if(!descriptorFreed) throw new InvalidOperationException("native.probe_descriptor_cleanup_failed");
        }
    }
    static void TokenCheck(IntPtr process,IntPtr expectedSid,bool lpac) {
        IntPtr token; Bool(OpenProcessToken(process,10,out token),"native.token");
        IntPtr duplicate=IntPtr.Zero;
        try {
            uint needed; IntPtr memory=Marshal.AllocHGlobal(256);
            try {
                Bool(GetTokenInformation(token,29,memory,256,out needed),"native.appcontainer_token");
                if(Marshal.ReadInt32(memory)!=1) throw new InvalidOperationException("native.not_appcontainer");
                Bool(GetTokenInformation(token,31,memory,256,out needed),"native.package_token");
                if(new SecurityIdentifier(Marshal.ReadIntPtr(memory)).Value!=new SecurityIdentifier(expectedSid).Value)
                    throw new InvalidOperationException("native.wrong_package_token");
                Bool(GetTokenInformation(token,25,memory,256,out needed),"native.integrity_token");
                if(new SecurityIdentifier(Marshal.ReadIntPtr(memory)).Value!="S-1-16-4096")
                    throw new InvalidOperationException("native.not_low_integrity");
                Bool(GetTokenInformation(token,1,memory,256,out needed),"native.user_token");
                if(new SecurityIdentifier(Marshal.ReadIntPtr(memory)).Value!=WindowsIdentity.GetCurrent().User.Value)
                    throw new InvalidOperationException("native.wrong_user_token");
            } finally {Marshal.FreeHGlobal(memory);}
            Bool(DuplicateToken(token,2,out duplicate),"native.duplicate_token");
            string package=new SecurityIdentifier(expectedSid).Value;
            // API failure is never a successful denial determination.
            if(!AccessProbe(duplicate,package) || AccessProbe(duplicate,null) ||
               AccessProbe(duplicate,"S-1-15-2-987654321-987654321-987654321-987654321-987654321-987654321-987654321") ||
               AccessProbe(duplicate,"S-1-15-2-1")==lpac)
                throw new InvalidOperationException("native.lpac_behavior_mismatch");
        } finally {
            bool duplicateClosed=duplicate==IntPtr.Zero || CloseHandle(duplicate);
            bool tokenClosed=CloseHandle(token);
            if(!duplicateClosed || !tokenClosed) throw new InvalidOperationException("native.token_cleanup_failed");
        }
    }
    static void Attribute(IntPtr list,int id,IntPtr value,int bytes) {
        Bool(UpdateProcThreadAttribute(list,0,new IntPtr(id),value,new UIntPtr((uint)bytes),IntPtr.Zero,IntPtr.Zero),"native.attribute");
    }
    static void Launch(bool verificationOnly) {
        IntPtr sid=Sid(),engine=IntPtr.Zero,attributes=IntPtr.Zero,job=IntPtr.Zero,environment=IntPtr.Zero;
        ProcessInfo child=new ProcessInfo(); var allocations=new List<IntPtr>(); var handles=new List<IntPtr>();
        try {
            Check(FwpmEngineOpen0(IntPtr.Zero,10,IntPtr.Zero,IntPtr.Zero,out engine),"native.engine"); Verify(engine,sid);
            UIntPtr bytes=UIntPtr.Zero; InitializeProcThreadAttributeList(IntPtr.Zero,3,0,ref bytes);
            attributes=Marshal.AllocHGlobal(checked((int)bytes.ToUInt64()));
            Bool(InitializeProcThreadAttributeList(attributes,3,0,ref bytes),"native.attributes");
            IntPtr capabilitySid; Bool(ConvertStringSidToSid("S-1-15-3-3",out capabilitySid),"native.capability"); allocations.Add(capabilitySid);
            IntPtr capArray=Marshal.AllocHGlobal(Marshal.SizeOf(typeof(SidAttributes))); allocations.Add(capArray);
            Marshal.StructureToPtr(new SidAttributes {sid=capabilitySid,attributes=4},capArray,false);
            IntPtr security=Marshal.AllocHGlobal(Marshal.SizeOf(typeof(Capabilities))); allocations.Add(security);
            Marshal.StructureToPtr(new Capabilities {sid=sid,capabilities=capArray,count=1},security,false);
            Attribute(attributes,0x20009,security,Marshal.SizeOf(typeof(Capabilities)));
            IntPtr optOut=Marshal.AllocHGlobal(4); allocations.Add(optOut); Marshal.WriteInt32(optOut,1);
            // PROC_THREAD_ATTRIBUTE_ALL_APPLICATION_PACKAGES_POLICY (SDK 15).
            // Attribute 14 is child-process policy, not LPAC selection.
            Attribute(attributes,0x2000F,optOut,4);
            var sa=new SecurityAttributes {size=(uint)Marshal.SizeOf(typeof(SecurityAttributes)),inherit=1};
            IntPtr inputRead,inputWrite,outputRead,outputWrite,errorRead,errorWrite;
            Bool(CreatePipe(out inputRead,out inputWrite,ref sa,0),"native.input_pipe"); handles.Add(inputRead);handles.Add(inputWrite);
            Bool(CreatePipe(out outputRead,out outputWrite,ref sa,0),"native.output_pipe"); handles.Add(outputRead);handles.Add(outputWrite);
            Bool(CreatePipe(out errorRead,out errorWrite,ref sa,0),"native.error_pipe"); handles.Add(errorRead);handles.Add(errorWrite);
            foreach(IntPtr h in new[]{inputWrite,outputRead,errorRead}) Bool(SetHandleInformation(h,1,0),"native.handle_flags");
            IntPtr inheritList=Marshal.AllocHGlobal(3*IntPtr.Size);allocations.Add(inheritList);
            Marshal.WriteIntPtr(inheritList,0,inputRead);Marshal.WriteIntPtr(inheritList,IntPtr.Size,outputWrite);Marshal.WriteIntPtr(inheritList,2*IntPtr.Size,errorWrite);
            Attribute(attributes,0x20002,inheritList,3*IntPtr.Size);
            string runtime=Path.Combine(root,"runtime"),state=Path.Combine(root,"state");
            string windir=Environment.GetEnvironmentVariable("SystemRoot");
            string env="HERMES_HOME="+state+"\0LOCALAPPDATA="+state+"\0PATH="+Path.Combine(runtime,"python")+";"+Environment.SystemDirectory+
                "\0SYSTEMROOT="+windir+"\0TEMP="+state+"\0TMP="+state+"\0USERPROFILE="+state+"\0WINDIR="+windir+"\0\0";
            environment=Marshal.StringToHGlobalUni(env);
            var startup=new StartupEx {startup=new Startup {size=(uint)Marshal.SizeOf(typeof(StartupEx)),flags=0x100,input=inputRead,output=outputWrite,error=errorWrite},attributes=attributes};
            string python=Path.Combine(runtime,"python","python.exe"),worker=Path.Combine(runtime,"worker.py");
            Bool(CreateProcessW(python,new StringBuilder(Quote(python)+" -I -S "+Quote(worker)),IntPtr.Zero,IntPtr.Zero,true,0x80404,environment,state,ref startup,out child),"native.create_process");
            job=CreateJobObject(IntPtr.Zero,null); if(job==IntPtr.Zero) throw new InvalidOperationException("native.create_job");
            var limits=new JobLimits {basic=new BasicLimits {flags=0x2000|8,activeProcessLimit=8}};
            Bool(SetInformationJobObject(job,9,ref limits,(uint)Marshal.SizeOf(typeof(JobLimits))),"native.job_limits");
            Bool(AssignProcessToJobObject(job,child.process),"native.assign_job"); TokenCheck(child.process,sid,true);
            // Paired ordinary-AppContainer control: same image, SID, capabilities
            // and environment, no LPAC opt-out. It is never resumed.
            ProcessInfo control=new ProcessInfo();
            IntPtr controlAttributes=IntPtr.Zero;
            bool controlAttributesReady=false;
            try {
                UIntPtr controlBytes=UIntPtr.Zero;
                InitializeProcThreadAttributeList(IntPtr.Zero,2,0,ref controlBytes);
                controlAttributes=Marshal.AllocHGlobal(checked((int)controlBytes.ToUInt64()));
                Bool(InitializeProcThreadAttributeList(controlAttributes,2,0,ref controlBytes),"native.control_attributes");
                controlAttributesReady=true;
                Attribute(controlAttributes,0x20009,security,Marshal.SizeOf(typeof(Capabilities)));
                Attribute(controlAttributes,0x20002,inheritList,3*IntPtr.Size);
                var controlStartup=new StartupEx {startup=startup.startup,attributes=controlAttributes};
                Bool(CreateProcessW(python,new StringBuilder(Quote(python)+" -I -S "+Quote(worker)),IntPtr.Zero,IntPtr.Zero,true,0x80404,environment,state,ref controlStartup,out control),"native.control_create");
                Bool(AssignProcessToJobObject(job,control.process),"native.control_assign_job");
                TokenCheck(control.process,sid,false);
            } finally {
                try {
                    if(control.process!=IntPtr.Zero) {Bool(TerminateProcess(control.process,0),"native.control_terminate");if(WaitForSingleObject(control.process,5000)!=0) throw new InvalidOperationException("native.control_cleanup_failed");}
                } finally {
                    bool threadClosed=control.thread==IntPtr.Zero || CloseHandle(control.thread);
                    bool processClosed=control.process==IntPtr.Zero || CloseHandle(control.process);
                    if(controlAttributesReady) DeleteProcThreadAttributeList(controlAttributes);
                    if(controlAttributes!=IntPtr.Zero) Marshal.FreeHGlobal(controlAttributes);
                    if(!threadClosed || !processClosed) throw new InvalidOperationException("native.control_handle_cleanup_failed");
                }
            }
            if(verificationOnly) {
                Bool(TerminateProcess(child.process,0),"native.probe_terminate");
                if(WaitForSingleObject(child.process,5000)!=0) throw new InvalidOperationException("native.probe_cleanup_failed");
                Bool(CloseHandle(child.process),"native.probe_process_close");child.process=IntPtr.Zero;
                Bool(CloseHandle(child.thread),"native.probe_thread_close");child.thread=IntPtr.Zero;
                Bool(TerminateJobObject(job,0),"native.probe_job_terminate");Bool(CloseHandle(job),"native.probe_job_close");job=IntPtr.Zero;
                foreach(IntPtr handle in handles) Bool(CloseHandle(handle),"native.probe_pipe_close");handles.Clear();
                Report(new {status="lpac_behavior_verified",selected_package_allowed=true,selected_aap_denied=true,
                    ordinary_control_aap_allowed=true,wrong_package_denied=true,no_grant_denied=true,
                    low_integrity=true,control_never_resumed=true,worker_never_resumed=true,production_qualified=false});
                return;
            }
            foreach(IntPtr h in new[]{inputRead,outputWrite,errorWrite}) {CloseHandle(h);handles.Remove(h);}
            string input=Console.ReadLine(); if(input==null || input.Length>65536) throw new InvalidOperationException("native.bad_admission");
            byte[] output=null; var outputThread=new Thread(delegate() {try {output=ReadPipe(outputRead,1024*1024);} catch {output=null;}});
            var errorThread=new Thread(delegate() {try {ReadPipe(errorRead,64*1024);} catch {}});
            outputThread.IsBackground=true;errorThread.IsBackground=true;outputThread.Start();errorThread.Start();
            if(ResumeThread(child.thread)==UInt32.MaxValue) throw new InvalidOperationException("native.resume");
            using(var stream=new FileStream(new Microsoft.Win32.SafeHandles.SafeFileHandle(inputWrite,false),FileAccess.Write)) {
                byte[] data=Encoding.UTF8.GetBytes(input+"\n");stream.Write(data,0,data.Length);
            }
            CloseHandle(inputWrite);handles.Remove(inputWrite);
            if(WaitForSingleObject(child.process,90000)!=0) {TerminateJobObject(job,1);throw new InvalidOperationException("native.timeout");}
            uint code; Bool(GetExitCodeProcess(child.process,out code),"native.exit_code");
            outputThread.Join(5000);errorThread.Join(5000);
            if(output==null || outputThread.IsAlive || errorThread.IsAlive) throw new InvalidOperationException("native.capture_failed");
            File.WriteAllBytes(Path.Combine(root,"child-result.json"),output);
            Console.WriteLine("{\"status\":\"native_returned\",\"exit_code\":"+code+",\"production_qualified\":false}");
        } finally {
            if(job!=IntPtr.Zero) {TerminateJobObject(job,1);CloseHandle(job);}
            if(child.process!=IntPtr.Zero) {TerminateProcess(child.process,1);CloseHandle(child.process);} if(child.thread!=IntPtr.Zero) CloseHandle(child.thread);
            foreach(IntPtr h in handles) CloseHandle(h);
            if(attributes!=IntPtr.Zero) {DeleteProcThreadAttributeList(attributes);Marshal.FreeHGlobal(attributes);}
            // ConvertStringSidToSid uses LocalAlloc; the other scratch buffers use HGlobal.
            for(int i=0;i<allocations.Count;i++) {if(i==0) LocalFree(allocations[i]);else Marshal.FreeHGlobal(allocations[i]);}
            if(environment!=IntPtr.Zero) Marshal.FreeHGlobal(environment);
            if(engine!=IntPtr.Zero) FwpmEngineClose0(engine);FreeSid(sid);
        }
    }
    static byte[] ReadPipe(IntPtr handle,int limit) {
        using(var stream=new FileStream(new Microsoft.Win32.SafeHandles.SafeFileHandle(handle,false),FileAccess.Read))
        using(var memory=new MemoryStream()) {
            byte[] buffer=new byte[4096];int count;bool overflow=false;
            while((count=stream.Read(buffer,0,buffer.Length))>0) {
                if(memory.Length+count<=limit) memory.Write(buffer,0,count);else overflow=true;
            }
            return overflow ? null : memory.ToArray();
        }
    }
    public static int Main(string[] args) {
        try {
            AppContext.SetSwitch("Switch.System.IO.UseLegacyPathHandling",false);
            AppContext.SetSwitch("Switch.System.IO.BlockLongPaths",false);
            if(IntPtr.Size!=8 || args.Length<3) throw new ArgumentException("native.invalid_invocation");
            ValidateRoot(args[1]);port=UInt16.Parse(args[2]);if(port<1024) throw new ArgumentException("native.bad_port");
            using(var mutex=new Mutex(false,"Local\\"+profile+".owner")) {
            if(!mutex.WaitOne(5000)) throw new InvalidOperationException("native.owner_busy");
            try {
            if(args[0]=="plan") {
                IntPtr sid=Sid();try {Console.WriteLine(new JavaScriptSerializer().Serialize(new {status="plan_only",profile=profile,sid=new SecurityIdentifier(sid).Value,port=port,filters=8,capability="privateNetworkClientServer",production_qualified=false}));} finally {FreeSid(sid);} return 0;
            }
            if(args[0]=="provision" || args[0]=="finish-provision" || args[0]=="cleanup" || args[0]=="abandon-unprovisioned") {
                if(args.Length!=4 || args[3]!="--consent-test-security-changes") throw new ArgumentException("native.consent_required");
                if(args[0]=="provision") Provision();else if(args[0]=="finish-provision") FinishProvision();else if(args[0]=="cleanup") Cleanup();else AbandonUnprovisioned();
            } else if(args[0]=="inspect-runtime") {
                int count=0;foreach(string item in Directory.EnumerateFileSystemEntries("\\\\?\\"+Path.Combine(root,"runtime"),"*",SearchOption.AllDirectories)) {
                    if((File.GetAttributes(item)&FileAttributes.ReparsePoint)!=0) throw new InvalidOperationException("native.stage_reparse");count++;
                }
                Report(new {status="runtime_inspected",entries=count,production_qualified=false});return 0;
            } else if(args[0]=="verify") {
                IntPtr sid=Sid(),engine=IntPtr.Zero;try {Check(FwpmEngineOpen0(IntPtr.Zero,10,IntPtr.Zero,IntPtr.Zero,out engine),"native.engine");Verify(engine,sid);} finally {if(engine!=IntPtr.Zero) FwpmEngineClose0(engine);FreeSid(sid);}
            } else if(args[0]=="launch" || args[0]=="verify-tokens") {Launch(args[0]=="verify-tokens");return 0;} else throw new ArgumentException("native.unknown_operation");
            Report(new {status="operation_completed",production_qualified=false});return 0;
            } finally {mutex.ReleaseMutex();}
            }
        } catch(Exception error) {
            // Error messages are native fixed codes/numbers, never provider bodies or input.
            string code=error is InvalidOperationException || error is ArgumentException ? error.Message : "native.operation_failed";
            if(!code.StartsWith("native.")) code="native.operation_failed";
            if(code=="native.operation_failed") code += ":"+error.GetType().Name;
            Report(new {status="blocked",reason_code=code,production_qualified=false});return 1;
        }
    }
}
