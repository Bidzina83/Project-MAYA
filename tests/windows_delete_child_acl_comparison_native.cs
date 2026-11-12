#if MAYA_DELETE_CHILD_ACL_COMPARISON_INERT && HERMES_JOURNAL_DELETE_CHILD_SOURCE
using System;
using System.Collections.Generic;
using System.IO;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Web.Script.Serialization;
using Microsoft.Win32.SafeHandles;
using ProjectMaya.WindowsRuntime;

internal static class DeleteChildAclComparisonNative
{
    const string Root=@"C:\Users\Bidzina\AppData\Local\MayaJournalProbeScratch";
    const string Operator="S-1-5-21-748951685-2862888470-2464618232-500";
    static readonly CoordinatorJournalWindowsCalls Calls=new CoordinatorJournalWindowsCalls();

    static void Require(bool ok,string reason)
    {if(!ok)throw new IOException(reason);}

    static string Identity(SafeFileHandle handle,string path)
    {
        Require(handle!=null && !handle.IsInvalid && !handle.IsClosed,"acl_comparison_handle");
        var file=Calls.Inspect(handle);
        Require(file.Disk && file.Directory && !file.Reparse && !file.Inheritable &&
            CoordinatorJournalBinding.Hex(file.Volume,8) && CoordinatorJournalBinding.Hex(file.Id,16) &&
            String.Equals(file.Path.TrimEnd('\\'),path.TrimEnd('\\'),StringComparison.OrdinalIgnoreCase),"acl_comparison_object");
        return file.Volume+file.Id;
    }

    static DeleteChildAclCollector.Snapshot Read(SafeFileHandle handle,string path,string id)
    {
        Require(Identity(handle,path)==id,"acl_comparison_identity");
        var descriptor=Calls.Descriptor(handle);
        Require(Identity(handle,path)==id,"acl_comparison_identity_changed");
        return new DeleteChildAclCollector.Snapshot(id,descriptor);
    }

    static int Main(string[] args)
    {
        string scratch=null;
        var pins=new List<SafeFileHandle>();
        var paths=new List<string>();
        var identities=new List<string>();
        var json=new JavaScriptSerializer();
        try
        {
            Require(args.Length==2 && args[0]=="--compare" && args[1]==Root,"acl_comparison_arguments");
            using(var token=WindowsIdentity.GetCurrent())
            {
                Require(token.User.Value==Operator &&
                    new WindowsPrincipal(token).IsInRole(WindowsBuiltInRole.Administrator),"acl_comparison_operator");
                Require(Calls.LocalNtfs(Path.GetPathRoot(Root)) &&
                    !Root.StartsWith(ProductFiles.Root+"\\",StringComparison.OrdinalIgnoreCase),"acl_comparison_volume");
                var chain=new Stack<string>();
                for(string path=Root;path!=null;path=Path.GetDirectoryName(path))chain.Push(path);
                foreach(string path in chain)
                {
                    var pin=Calls.Open(path,0x20080,3,3,0x02200000,null);
                    pins.Add(pin);paths.Add(path);identities.Add(Identity(pin,path));
                }
                var package=new SecurityIdentifier("S-1-15-2-103745-921147-614201-103077-848391-126345-791825");
                var expectedParent=DeleteChildAclExpectedPolicy.Build(token.User,package,false);
                var expectedChild=DeleteChildAclExpectedPolicy.Build(token.User,package,true);
                var roles=new Dictionary<SecurityIdentifier,string>{
                    {new SecurityIdentifier("S-1-5-18"),"system"},{new SecurityIdentifier("S-1-5-32-544"),"administrators"},
                    {token.User,"operator"},{package,"synthetic_package"}};
                var scratchSecurity=new RawSecurityDescriptor(CoordinatorJournalCandidate.CreationDescriptor);
                var security=new byte[scratchSecurity.BinaryLength];
                scratchSecurity.GetBinaryForm(security,0);
                string nonce=Guid.NewGuid().ToString("N");
                scratch=Path.Combine(Root,"acl-comparison-"+nonce);
                using(var outer=DeleteChildControlCreate.NewScratchParent(pins[pins.Count-1],nonce,security))
                {
                    string outerId=Identity(outer,scratch);
                    Require(CoordinatorJournalDescriptor.Compare(Calls.Descriptor(outer))==null &&
                        Directory.GetFileSystemEntries(scratch).Length==0,"acl_comparison_scratch_baseline");
                    string state=Path.Combine(scratch,"state");
                    Directory.CreateDirectory(state,ProductFiles.StateSecurity(package,token.User));
                    Native.SetLabel(state,true);
                    ProductFiles.NoLinks(state);
                    using(var parent=Calls.Open(state,0x20080,3,3,0x02200000,null))
                    {
                        string parentId=Identity(parent,state);
                        Require(outerId!=parentId && outerId.Substring(0,8)==parentId.Substring(0,8) &&
                            Directory.GetFileSystemEntries(state).Length==0,"acl_comparison_parent_binding");
                        string childPath=Path.Combine(state,"delete-child-control");
                        using(var child=DeleteChildControlCreate.New(parent,0x60080))
                        {
                            string childId=Identity(child,childPath);
                            Require(parentId.Substring(0,8)==childId.Substring(0,8),"acl_comparison_volume_changed");
                            var result=DeleteChildAclCollector.Collect(parentId,childId,()=>Read(parent,state,parentId),
                                ()=>Read(child,childPath,childId),expectedParent,expectedChild,roles);
                            for(int i=0;i<pins.Count;i++)
                                Require(Identity(pins[i],paths[i])==identities[i],"acl_comparison_ancestor_changed");
                            Require(Identity(outer,scratch)==outerId,"acl_comparison_scratch_changed");
                            result["scratch"]=scratch;
                            result["scratch_retained_for_independent_cleanup"]=true;
                            result["synthetic_package"]=true;
                            Console.WriteLine(json.Serialize(result));
                        }
                    }
                }
            }
            return 0;
        }
        catch(Exception error)
        {
            Console.WriteLine(json.Serialize(new Dictionary<string,object>{{"outcome","inconclusive"},
                {"failure_type",error.GetType().Name},{"scratch",scratch},
                {"scratch_retained_for_independent_cleanup",scratch!=null}}));
            return 2;
        }
        finally {for(int i=pins.Count-1;i>=0;i--)pins[i].Dispose();}
    }
}
#endif
