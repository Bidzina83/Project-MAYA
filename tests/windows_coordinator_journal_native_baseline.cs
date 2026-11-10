#if MAYA_FINAL_OUTPUT_INERT_FIXTURE && MAYA_JOURNAL_NATIVE_BASELINE
using System;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using Microsoft.Win32;
using ProjectMaya.WindowsRuntime;

internal static class CoordinatorJournalNativeBaseline
{
    [StructLayout(LayoutKind.Sequential)] struct Attributes {internal uint Size;internal IntPtr Descriptor;internal int Inherit;}
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,ExactSpelling=true,SetLastError=true)] static extern bool CreateDirectoryW(string path,IntPtr attributes);
    [DllImport("advapi32.dll",CharSet=CharSet.Unicode,ExactSpelling=true,SetLastError=true)] static extern bool ConvertStringSecurityDescriptorToSecurityDescriptorW(
        string text,uint revision,out IntPtr descriptor,out uint length);
    [DllImport("advapi32.dll",SetLastError=true)] static extern bool GetTokenInformation(IntPtr token,int kind,IntPtr buffer,uint size,out uint length);
    [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr value);

    static void Native(bool result) {if(!result)throw new Win32Exception(Marshal.GetLastWin32Error());}
    static bool CreateParent(string path,string descriptor)
    {
        IntPtr raw=IntPtr.Zero, attrs=IntPtr.Zero;uint size;
        try
        {
            Native(ConvertStringSecurityDescriptorToSecurityDescriptorW(descriptor,1,out raw,out size));
            int length=Marshal.SizeOf(typeof(Attributes));attrs=Marshal.AllocHGlobal(length);
            Marshal.StructureToPtr(new Attributes{Size=(uint)length,Descriptor=raw,Inherit=0},attrs,false);
            Native(CreateDirectoryW(path,attrs));return true;
        }
        finally {if(attrs!=IntPtr.Zero)Marshal.FreeHGlobal(attrs);if(raw!=IntPtr.Zero)LocalFree(raw);}
    }
    static void CheckToken()
    {
        using(var identity=WindowsIdentity.GetCurrent())
        {
            if(identity.User==null || identity.User.Value!=CoordinatorJournalScratchTarget.OperatorSid ||
                !new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator))throw new IOException("baseline_operator");
            IntPtr buffer=Marshal.AllocHGlobal(256);
            try
            {
                uint length;
                Native(GetTokenInformation(identity.Token,20,buffer,4,out length));
                if(length!=4 || Marshal.ReadInt32(buffer)!=1)throw new IOException("baseline_elevation");
                Native(GetTokenInformation(identity.Token,25,buffer,256,out length));
                long offset=Marshal.ReadIntPtr(buffer).ToInt64()-buffer.ToInt64();
                if(length<16 || length>256 || offset<16 || offset>length-8)throw new IOException("baseline_integrity_bounds");
                IntPtr label=IntPtr.Add(buffer,(int)offset);int count=Marshal.ReadByte(label,1);
                if(count>15 || offset+8+4*count>length)throw new IOException("baseline_integrity_bounds");
                string integrity=new SecurityIdentifier(label).Value;
                if(integrity!="S-1-16-12288")throw new IOException("baseline_integrity");
                using(var key=Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion"))
                {
                    string build=key==null?null:key.GetValue("CurrentBuildNumber") as string;
                    object revision=key==null?null:key.GetValue("UBR");
                    if(build!="26300" || !9711.Equals(revision))throw new IOException("baseline_build");
                    Console.WriteLine("build=26300.9711 sid="+identity.User.Value+" elevated=true admin_enabled=true integrity="+integrity);
                }
            }
            finally {Marshal.FreeHGlobal(buffer);}
        }
    }

    // The expected record is deliberately independent of the candidate serializer.
    static string Expected(string attempt,string kind)
    {
        return "{\"v\":1,\"event\":\""+kind+"\",\"attempt\":\""+attempt+"\",\"channel\":\""+new string('b',64)+
            "\",\"actor\":\"windows:"+CoordinatorJournalScratchTarget.OperatorSid+"\",\"delivery_id\":\""+new string('c',32)+
            "\",\"request_sha256\":\""+new string('d',64)+"\",\"response_sha256\":\""+new string('e',64)+
            "\",\"output_sha256\":\""+new string('f',64)+"\",\"output_bytes\":42,\"destination\":\"synthetic:fake-operator\""+
            ",\"consent_id\":\""+new string('0',32)+"\",\"epoch\":1,\"deadline\":100}\n";
    }
    internal static string Run(string root,string attempt,ICoordinatorJournalNativeCalls api,Func<string,string,bool> create,Action<string> report)
    {
        string result;
        report("stage=scratch_setup");
        if(root==CoordinatorJournalScratchTarget.Root && CoordinatorJournalBinding.Hex(attempt,32))
            report("attempt_target="+Path.Combine(root,attempt));
        using(var scratch=new CoordinatorJournalScratchTarget(root,attempt,api,create))
        {
            report("scratch="+scratch.Directory);
            var binding=new CoordinatorJournalBinding(attempt,new string('b',64),"windows:"+CoordinatorJournalScratchTarget.OperatorSid,
                new string('c',32),new string('d',64),new string('e',64),new string('f',64),42,new string('0',32),1,100);
            byte[] expected=Encoding.UTF8.GetBytes(Expected(attempt,"release_intent")+Expected(attempt,"pre_effect_stop"));
            CoordinatorJournalNativeTransport transport=null;
            string id;
            report("stage=journal_create");
            using(var journal=new CoordinatorJournalCandidate(binding,scratch,(p,d)=>
                transport=new CoordinatorJournalNativeTransport(scratch,p,d,api)))
            {
                report("stage=journal_intent");journal.Intent();
                report("stage=journal_pre_effect_stop");journal.PreEffectStop();
                byte[] verified=transport.ReadPrefix(expected.Length);
                if(!expected.SequenceEqual(verified))throw new IOException("baseline_expected_bytes");
                id=transport.Inspect().FileId;report("stage=writer_close");
            }
            report("stage=read_only_reopen");
            byte[] reopened=scratch.ReadClosedJournal(id,expected);
            result="classification=pre_effect_stop_as_recorded volume="+scratch.Volume+" file="+id+
                " bytes="+reopened.Length+" sha256="+BridgeHostFiles.Hash(reopened);
        }
        return result;
    }
    static int Main(string[] args)
    {
        try
        {
            if(args.Length!=2 || args[0]!="--baseline" || args[1]!=CoordinatorJournalScratchTarget.Root)
                throw new IOException("baseline_exact_target_required");
            CheckToken();
            string result=Run(args[1],Guid.NewGuid().ToString("N"),new CoordinatorJournalWindowsCalls(),CreateParent,Console.WriteLine);
            Console.WriteLine(result);return 0;
        }
        catch(Win32Exception error) {Console.Error.WriteLine("baseline_blocked win32="+error.NativeErrorCode);return 2;}
        catch(Exception error)
        {
            string reason=error is IOException && System.Text.RegularExpressions.Regex.IsMatch(error.Message,"\\A[a-z_]{1,64}\\z")
                ?error.Message:error.GetType().Name;
            Console.Error.WriteLine("baseline_blocked: "+reason);return 2;
        }
    }
}
#endif
