using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.Win32.SafeHandles;
using Microsoft.Win32;

// Standalone scratch probe. Never links to or launches the MAYA product.
internal static class FinalOutputNativeProbeV2
{
    const uint ReadControl=0x20000, ReadAttributes=0x80, GenericRead=0x80000000, GenericWrite=0x40000000;
    const uint NoFollow=0x00200000, DirectoryHandle=0x02000000, SecurityFields=0x17;
    const uint OpenExisting=3, CreateNew=1, Directory=0x10, Reparse=0x400;
    const int Budget=15000, Limit=16384;
    const string Leaf="probe-journal.jsonl";
    static readonly UTF8Encoding Utf8=new UTF8Encoding(false,true);
    static readonly string[] Interruptions={"before-intent","partial-intent","intent-flushed","fake-accepted",
        "partial-confirmation","confirmation-flushed"};

    [StructLayout(LayoutKind.Sequential)] struct SecurityAttributes
    { internal uint size; internal IntPtr descriptor; internal int inherit; }
    [StructLayout(LayoutKind.Sequential)] struct FileInformation
    {
        internal uint attributes;
        internal System.Runtime.InteropServices.ComTypes.FILETIME creation, access, write;
        internal uint volume, sizeHigh, sizeLow, links, fileHigh, fileLow;
    }

    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern SafeFileHandle CreateFileW(
        string path,uint access,uint share,IntPtr attributes,uint disposition,uint flags,IntPtr template);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateDirectoryW(string path,IntPtr attributes);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle handle,out FileInformation info);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern uint GetFinalPathNameByHandleW(
        SafeFileHandle handle,StringBuilder path,uint length,uint flags);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetHandleInformation(SafeFileHandle handle,out uint flags);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode)] static extern uint GetDriveTypeW(string root);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateProcess(IntPtr process,uint exitCode);
    [DllImport("kernel32.dll",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle,uint milliseconds);
    [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr pointer);
    [DllImport("advapi32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool ConvertStringSecurityDescriptorToSecurityDescriptorW(
        string text,uint revision,out IntPtr descriptor,out uint size);
    [DllImport("advapi32.dll")] static extern bool IsValidSecurityDescriptor(IntPtr descriptor);
    [DllImport("advapi32.dll")] static extern uint GetSecurityDescriptorLength(IntPtr descriptor);
    [DllImport("advapi32.dll")] static extern uint GetSecurityInfo(SafeFileHandle handle,int kind,uint fields,
        out IntPtr owner,out IntPtr group,out IntPtr dacl,out IntPtr sacl,out IntPtr descriptor);

    static void Check(bool ok,string code)
    { if(!ok) throw new IOException(code); }

    static string Descriptor()
    {
        using(var identity=WindowsIdentity.GetCurrent())
        {
            Check(identity.User!=null,"token_identity");
            string sid=identity.User.Value;
            // File/directory-specific full access for the test SID and SYSTEM only; no inheritance.
            return "O:"+sid+"G:"+sid+"D:P(A;;FA;;;"+sid+")(A;;FA;;;SY)S:(ML;;NW;;;ME)";
        }
    }

    static IntPtr NewDescriptor()
    {
        IntPtr descriptor; uint size;
        Check(ConvertStringSecurityDescriptorToSecurityDescriptorW(Descriptor(),1,out descriptor,out size),"descriptor_build");
        return descriptor;
    }

    static T WithAttributes<T>(Func<IntPtr,T> action)
    {
        IntPtr descriptor=NewDescriptor(), pointer=IntPtr.Zero;
        try
        {
            int size=Marshal.SizeOf(typeof(SecurityAttributes));pointer=Marshal.AllocHGlobal(size);
            Marshal.StructureToPtr(new SecurityAttributes{size=(uint)size,descriptor=descriptor,inherit=0},pointer,false);
            return action(pointer);
        }
        finally {if(pointer!=IntPtr.Zero)Marshal.FreeHGlobal(pointer);LocalFree(descriptor);}
    }

    static void VerifyDescriptor(SafeFileHandle handle)
    {
        IntPtr owner,group,dacl,sacl,actual;
        Check(GetSecurityInfo(handle,1,SecurityFields,out owner,out group,out dacl,out sacl,out actual)==0,"descriptor_read");
        try
        {
            Check(actual!=IntPtr.Zero && IsValidSecurityDescriptor(actual),"descriptor_invalid");
            uint length=GetSecurityDescriptorLength(actual);
            Check(length>=20 && length<=16384,"descriptor_bounds");
            var bytes=new byte[(int)length]; Marshal.Copy(actual,bytes,0,bytes.Length);
            using(var identity=WindowsIdentity.GetCurrent())
            {
                string mismatch=FinalOutputProbeDescriptor.Compare(bytes,identity.User);
                Check(mismatch==null,mismatch);
            }
        }
        finally {LocalFree(actual);}
    }

    static string FixedLocalPath(string raw)
    {
        Check(raw!=null && Regex.IsMatch(raw,@"\A[A-Za-z]:\\[^""\r\n:]+\z") && !raw.EndsWith("\\"),"scratch_path");
        string full=Path.GetFullPath(raw), root=Path.GetPathRoot(full);
        Check(string.Equals(full,raw,StringComparison.OrdinalIgnoreCase) && root.Length==3 && GetDriveTypeW(root)==3 &&
            string.Equals(new DriveInfo(root).DriveFormat,"NTFS",StringComparison.OrdinalIgnoreCase),"scratch_volume");
        return full;
    }

    static FileInformation Inspect(SafeFileHandle handle,string path,bool directory)
    {
        Check(handle!=null && !handle.IsInvalid && !handle.IsClosed,"open_failed");
        uint flags;Check(GetHandleInformation(handle,out flags) && (flags&1)==0,"inheritable_handle");
        FileInformation info;Check(GetFileInformationByHandle(handle,out info),"file_identity");
        Check((info.attributes&Reparse)==0 && ((info.attributes&Directory)!=0)==directory,"object_type");
        var name=new StringBuilder(32768);uint size=GetFinalPathNameByHandleW(handle,name,(uint)name.Capacity,0);
        Check(size>0 && size<name.Capacity && string.Equals(name.ToString(),"\\\\?\\"+path.TrimEnd('\\'),StringComparison.OrdinalIgnoreCase)
            || directory && path.Length==3 && size>0 && size<name.Capacity &&
               string.Equals(name.ToString(),"\\\\?\\"+path,StringComparison.OrdinalIgnoreCase),"opened_path");
        if(!directory)Check(info.links==1 && info.sizeHigh==0 && info.sizeLow<=Limit,"file_bounds");
        return info;
    }

    sealed class PinnedDirectories : IDisposable
    {
        readonly List<SafeFileHandle> handles=new List<SafeFileHandle>();
        internal PinnedDirectories(string path)
        {
            var names=new Stack<string>();
            for(string current=path;current!=null;current=Path.GetDirectoryName(current))names.Push(current);
            try
            {
                uint? volume=null;
                foreach(string name in names)
                {
                    var handle=CreateFileW(name,ReadAttributes|ReadControl,3,IntPtr.Zero,OpenExisting,NoFollow|DirectoryHandle,IntPtr.Zero);
                    handles.Add(handle);
                    var info=Inspect(handle,name,true);
                    Check(!volume.HasValue || volume.Value==info.volume,"ancestor_volume"); volume=info.volume;
                }
            }
            catch {Dispose();throw;}
        }
        internal void VerifyLeafDescriptor() {VerifyDescriptor(handles[handles.Count-1]);}
        public void Dispose() {for(int i=handles.Count-1;i>=0;i--)handles[i].Dispose();}
    }

    static string Id(FileInformation info)
    {return info.volume.ToString("x8")+info.fileHigh.ToString("x8")+info.fileLow.ToString("x8");}
    static byte[] Record(string attempt,string stage)
    {return Utf8.GetBytes("{\"v\":1,\"attempt\":\""+attempt+"\",\"event\":\""+stage+"\"}\n");}

    static byte[] ReadExact(FileStream file,int length)
    {
        Check(length>=0 && length<=Limit && file.Length==length,"read_length");
        byte[] data=new byte[length];file.Position=0;
        for(int count=0;count<length;)
        {int n=file.Read(data,count,length-count);Check(n>0,"short_read");count+=n;}
        Check(file.ReadByte()==-1,"trailing_bytes");
        return data;
    }

    static void Append(FileStream file,SafeFileHandle handle,string path,string id,byte[] bytes,byte[] expected)
    {
        Check(Id(Inspect(handle,path,false))==id && expected.Length<=Limit,"append_identity");
        file.Position=file.Length;file.Write(bytes,0,bytes.Length);file.Flush(true);
        Check(expected.SequenceEqual(ReadExact(file,expected.Length)) && Id(Inspect(handle,path,false))==id,"append_readback");
        VerifyDescriptor(handle);
    }

    static void Helper(string folder,string attempt,string stage)
    {
        Check(Regex.IsMatch(attempt,"\\A[0-9a-f]{32}\\z") && Path.GetFileName(folder)=="MayaJournalProbe-"+attempt,"helper_attempt");
        Check(stage=="baseline" || Interruptions.Contains(stage),"helper_stage");
        Check(Console.IsInputRedirected && Console.IsOutputRedirected &&
            Console.ReadLine()=="start|"+attempt+"|"+stage,"helper_start_not_authorized");
        folder=FixedLocalPath(folder);
        using(var pins=new PinnedDirectories(folder))
        {
            pins.VerifyLeafDescriptor();
            string path=Path.Combine(folder,Leaf);
            using(var handle=WithAttributes(p=>CreateFileW(path,GenericRead|GenericWrite|ReadControl,0,p,CreateNew,NoFollow,IntPtr.Zero)))
            {
                var info=Inspect(handle,path,false);Check(info.sizeLow==0,"journal_not_empty");VerifyDescriptor(handle);
                string id=Id(info);
                using(var file=new FileStream(handle,FileAccess.ReadWrite))
                {
                    byte[] intent=Record(attempt,"release_intent"), confirmed=Record(attempt,"delivery_confirmed");
                    if(stage=="partial-intent")
                    {byte[] half=intent.Take(intent.Length/2).ToArray();Append(file,handle,path,id,half,half);}
                    else if(stage!="before-intent") Append(file,handle,path,id,intent,intent);
                    bool accepted=stage=="fake-accepted" || stage=="partial-confirmation" || stage=="confirmation-flushed" || stage=="baseline";
                    // This boolean is a synthetic effect. No publisher or destination exists.
                    if(stage=="partial-confirmation")
                    {byte[] half=confirmed.Take(confirmed.Length/2).ToArray();Append(file,handle,path,id,half,intent.Concat(half).ToArray());}
                    else if(stage=="confirmation-flushed" || stage=="baseline")
                        Append(file,handle,path,id,confirmed,intent.Concat(confirmed).ToArray());
                    Console.WriteLine("checkpoint|"+attempt+"|"+stage+"|"+id+"|"+(accepted?"1":"0"));Console.Out.Flush();
                    Check(Console.ReadLine()=="close|"+attempt && stage=="baseline","helper_close_not_authorized");
                }
            }
        }
    }

    static void Supervisor(string root,string stage)
    {
        root=FixedLocalPath(root);
        string productRoot=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),"MayaProtectedPython-Startup1");
        Check(string.Equals(Path.GetFileName(root),"MayaJournalProbeScratch",StringComparison.Ordinal) &&
            !root.StartsWith(productRoot+"\\",StringComparison.OrdinalIgnoreCase),"scratch_root_not_dedicated");
        using(var key=Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion"))
        using(var identity=WindowsIdentity.GetCurrent())
        {
            Check(key!=null && identity.User!=null,"environment_identity");
            Console.WriteLine("build="+key.GetValue("CurrentBuildNumber")+"."+key.GetValue("UBR")+" filesystem=NTFS sid="+identity.User.Value+
                " admin_role="+new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator));
        }
        string attempt=Guid.NewGuid().ToString("N"), folder=Path.Combine(root,"MayaJournalProbe-"+attempt);
        using(var rootPins=new PinnedDirectories(root))
        {
            Check(WithAttributes(p=>CreateDirectoryW(folder,p)),"scratch_create_new");
            Console.WriteLine("scratch="+folder);
            using(var pins=new PinnedDirectories(folder))
            {
                pins.VerifyLeafDescriptor();
                var start=new ProcessStartInfo(typeof(FinalOutputNativeProbeV2).Assembly.Location,
                    "--helper \""+folder+"\" "+attempt+" "+stage) {UseShellExecute=false,CreateNoWindow=true,
                    RedirectStandardOutput=true,RedirectStandardInput=true};
                string id;
                using(var child=Process.Start(start))
                {
                    Check(child!=null,"helper_start");
                    IntPtr original=child.Handle;
                    try
                    {
                        child.StandardInput.WriteLine("start|"+attempt+"|"+stage);child.StandardInput.Flush();
                        Task<string> line=child.StandardOutput.ReadLineAsync();
                        Check(line.Wait(Budget) && line.Result!=null,"checkpoint_unavailable");
                        string[] fields=line.Result.Split('|');
                        bool accepted=stage=="fake-accepted" || stage=="partial-confirmation" || stage=="confirmation-flushed" || stage=="baseline";
                        Check(fields.Length==5 && fields[0]=="checkpoint" && fields[1]==attempt && fields[2]==stage &&
                            Regex.IsMatch(fields[3],"\\A[0-9a-f]{24}\\z") && fields[4]==(accepted?"1":"0"),"checkpoint_binding");
                        id=fields[3];
                        if(stage=="baseline") {child.StandardInput.WriteLine("close|"+attempt);child.StandardInput.Flush();}
                        else Check(TerminateProcess(original,93),"interrupt_failed");
                        Check(WaitForSingleObject(original,Budget)==0,"helper_exit_timeout");
                        Check(child.ExitCode==(stage=="baseline"?0:93),"helper_exit_code");
                        Check(child.StandardOutput.ReadLine()==null,"extra_checkpoint");
                    }
                    finally {child.StandardInput.Dispose();}
                }
                string path=Path.Combine(folder,Leaf);
                using(var handle=CreateFileW(path,GenericRead|ReadControl,0,IntPtr.Zero,OpenExisting,NoFollow,IntPtr.Zero))
                {
                    var info=Inspect(handle,path,false);Check(Id(info)==id,"restart_identity");VerifyDescriptor(handle);
                    using(var file=new FileStream(handle,FileAccess.Read))
                    {
                        byte[] raw=ReadExact(file,(int)info.sizeLow), intent=Record(attempt,"release_intent"), confirmation=Record(attempt,"delivery_confirmed");
                        bool complete=stage=="confirmation-flushed" || stage=="baseline";
                        byte[] expected=stage=="before-intent"?new byte[0]:stage=="partial-intent"?intent.Take(intent.Length/2).ToArray():
                            stage=="partial-confirmation"?intent.Concat(confirmation.Take(confirmation.Length/2)).ToArray():
                            complete?intent.Concat(confirmation).ToArray():intent;
                        Check(raw.SequenceEqual(expected) && Id(Inspect(handle,path,false))==id,"restart_readback");VerifyDescriptor(handle);
                        Console.WriteLine("stage="+stage+" identity="+id+" bytes="+raw.Length+" classification="+
                            (complete?"confirmed_as_recorded":raw.Length==0?"no_confirmed_evidence":"unknown_or_invalid"));
                    }
                }
            }
        }
    }

    static int Main(string[] args)
    {
        try
        {
            if(args.Length==4 && args[0]=="--helper") Helper(args[1],args[2],args[3]);
            else if(args.Length==2 && args[0]=="--baseline") Supervisor(args[1],"baseline");
            else if(args.Length==3 && args[0]=="--interrupt" && Interruptions.Contains(args[2])) Supervisor(args[1],args[2]);
            else throw new IOException("explicit_probe_case_and_scratch_root_required");
            return 0;
        }
        catch(Exception error)
        {Console.Error.WriteLine("probe_blocked: "+(error is IOException?error.Message:error.GetType().Name));return 2;}
    }
}
