#if HERMES_JOURNAL_ACCESS
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Web.Script.Serialization;
using Microsoft.Win32.SafeHandles;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class JournalAccessRuntime : IDisposable
    {
        static readonly string[] Roots={"journal_access_worker_entry.py","journal_access_child_entry.py","journal_access_role.py"};
        internal static bool IsRoleRoot(string name) {return Array.IndexOf(Roots,name)>=0;}
        internal static bool HasRoleRoots(HashSet<string> names) {return Roots.All(names.Contains);}
        const string ControlDirectory="journal-access-control", ControlFile="control.bin";
        readonly string directory, attempt;
        readonly SecurityIdentifier user;
        readonly Dictionary<string,object> record;
        readonly ICoordinatorJournalNativeCalls calls=new CoordinatorJournalWindowsCalls();
        readonly WindowsIsolation worker;
        BridgeChannel workerChannel, childChannel;
        Snapshot parent, journal, workerFolder, workerFile, childFolder, childFile;
        static readonly byte[] Control=Encoding.ASCII.GetBytes("Maya synthetic journal access control v1");

        sealed class Snapshot
        {
            internal readonly string Volume, Id, Hash, DescriptorHash;
            internal readonly int Length;
            internal string Identity {get{return Volume+Id;}}
            internal Snapshot(CoordinatorNativeFile file,string hash,byte[] descriptor)
            {
                Volume=file.Volume;Id=file.Id;Length=file.Directory?0:file.Length;Hash=hash;
                DescriptorHash=descriptor==null?null:BridgeHostFiles.Hash(descriptor);
            }
            internal bool Matches(Snapshot other)
            {return Identity==other.Identity && Length==other.Length && Hash==other.Hash && DescriptorHash==other.DescriptorHash;}
        }

        internal JournalAccessRuntime(string directory,string attempt,SecurityIdentifier user,Dictionary<string,object> record)
        {
            this.directory=directory;this.attempt=attempt;this.user=user;this.record=record;
            worker=new WindowsIsolation("Maya.JournalAccessWorker."+attempt);
        }

        static void Require(bool ok,string reason)
        {if(!ok)throw new StartupFailure(reason);}

        internal static bool ExactEntries(string[] entries,string expected)
        {return entries.Length==1 && entries[0]==expected;}

        void Inventory(string root)
        {
            ProductFiles.NoLinks(root);
            string folder=Path.Combine(root,ControlDirectory);
            ProductFiles.NoLinks(folder);
            Require(ExactEntries(Directory.GetFileSystemEntries(root),folder) &&
                ExactEntries(Directory.GetFileSystemEntries(folder),Path.Combine(folder,ControlFile)),"journal_access_inventory");
        }

        Snapshot Inspect(string path,bool folder,bool content,bool descriptor,bool? low)
        {
            ProductFiles.NoLinks(path);
            using(var handle=calls.Open(path,content?0x80020080u:0x20080u,1,3,0x00200000u|(folder?0x02000000u:0),null))
            {
                Require(!handle.IsInvalid,"journal_access_open");
                var file=calls.Inspect(handle);
                Require(file.Disk && file.Directory==folder && !file.Reparse && !file.Inheritable &&
                    string.Equals(file.Path.TrimEnd('\\'),path.TrimEnd('\\'),StringComparison.OrdinalIgnoreCase) &&
                    CoordinatorJournalBinding.Hex(file.Volume,8) && CoordinatorJournalBinding.Hex(file.Id,16) &&
                    (parent==null || file.Volume==parent.Volume) &&
                    (folder || file.Links==1 && file.Length>=0 && file.Length<=16384),"journal_access_identity");
                byte[] sd=descriptor?calls.Descriptor(handle):null;
                if(low.HasValue)
                {
                    var raw=new RawSecurityDescriptor(sd,0);
                    if(low.Value)
                    {
                        Require(raw.SystemAcl!=null && raw.SystemAcl.Count==1,"journal_access_control_label");
                        byte[] ace=new byte[raw.SystemAcl[0].BinaryLength];
                        raw.SystemAcl[0].GetBinaryForm(ace,0);
                        Require((ace[1]&16)!=0,"journal_access_control_label");
                        ace[1]=(byte)(ace[1]&~16);
                        raw.SystemAcl[0]=GenericAce.CreateFromBinaryForm(ace,0);
                    }
                    Native.VerifyLabel(raw,low.Value,folder);
                }
                if(path==Path.Combine(directory,CoordinatorJournalCandidate.Leaf))
                    Require(CoordinatorJournalDescriptor.Compare(sd)==null,"journal_access_descriptor");
                var snapshot=new Snapshot(file,content?BridgeHostFiles.Hash(calls.Read(handle,0,file.Length)):null,sd);
                var after=calls.Inspect(handle);
                Require(after.Id==file.Id && after.Volume==file.Volume && after.Length==file.Length &&
                    after.Links==file.Links && !after.Reparse,"journal_access_read_changed");
                return snapshot;
            }
        }

        string Host {get{return Path.Combine(directory,"host");}}
        string State {get{return Path.Combine(directory,"state");}}
        string Journal {get{return Path.Combine(directory,CoordinatorJournalCandidate.Leaf);}}

        Snapshot[] Controls(string root,bool low)
        {
            Inventory(root);
            string folder=Path.Combine(root,ControlDirectory), file=Path.Combine(folder,ControlFile);
            if(!low)
            {
                BridgeHostFiles.Verify(Directory.GetAccessControl(root),user,true);
                BridgeHostFiles.Verify(Directory.GetAccessControl(folder),user,true);
                BridgeHostFiles.Verify(File.GetAccessControl(file),user,false);
            }
            var result=new[]{Inspect(folder,true,false,true,low),Inspect(file,false,true,true,low)};
            Require(result[1].Hash==BridgeHostFiles.Hash(Control),"journal_access_control_bytes");
            return result;
        }

        internal void PrepareWorker()
        {
            Require(directory==Path.Combine(ProductFiles.Root,attempt),"journal_access_attempt");
            ProductFiles.NoLinks(directory);
            parent=Inspect(directory,true,false,false,null);
            Require(!Directory.Exists(Host) && !File.Exists(Host) &&
                Directory.GetFileSystemEntries(State).Length==0,"journal_access_inventory");
            foreach(string folder in new[]{Host,Path.Combine(Host,ControlDirectory)})
            {
                Directory.CreateDirectory(folder,BridgeHostFiles.DirectoryAcl(user));
                Native.SetLabel(folder,false);
            }
            BridgeHostFiles.Write(Path.Combine(Host,ControlDirectory,ControlFile),Control,user);
            string stateControl=Path.Combine(State,ControlDirectory);
            Directory.CreateDirectory(stateControl);
            using(var file=new FileStream(Path.Combine(stateControl,ControlFile),FileMode.CreateNew,FileAccess.Write,FileShare.None))
            {file.Write(Control,0,Control.Length);file.Flush(true);}
            var host=Controls(Host,false);workerFolder=host[0];workerFile=host[1];
            var state=Controls(State,true);childFolder=state[0];childFile=state[1];

            var digest=BridgeHostFiles.Hash(Control);
            var binding=new CoordinatorJournalBinding(attempt,digest,"windows:"+user.Value,attempt,digest,digest,digest,
                Control.Length,attempt,0,0);
            CoordinatorJournalNativeTransport transport=null;
            using(var candidate=new CoordinatorJournalCandidate(binding,parent.Id,parent.Volume,
                (path,sd)=>transport=new CoordinatorJournalNativeTransport(attempt,parent.Id,parent.Volume,path,sd,calls)))
            {
                candidate.Intent();candidate.PreEffectStop();
                var observed=transport.Inspect();
                var bytes=transport.ReadPrefix(observed.Length);
                var file=new CoordinatorNativeFile(Journal,observed.VolumeId,observed.FileId,observed.Length,observed.Links,true,false,false,false);
                journal=new Snapshot(file,BridgeHostFiles.Hash(bytes),observed.Descriptor);
            }
            Recheck();
            record["journal_access_journal_identity"]=journal.Identity;
            record["journal_access_journal_sha256"]=journal.Hash;
            record["journal_access_journal_bytes"]=journal.Length;
            worker.StartJournalAccessWorker(directory,attempt,user);
            record["journal_access_worker_pid"]=worker.ChildPid;
            record["journal_access_worker_token_verified"]=worker.ReducedLaunchTokenVerified;
        }

        Snapshot[] Recheck()
        {
            var observedParent=Inspect(directory,true,false,false,null);
            var observedJournal=Inspect(Journal,false,true,true,null);
            Require(parent.Matches(observedParent) && journal.Matches(observedJournal),"journal_access_journal_changed");
            var host=Controls(Host,false);
            var state=Controls(State,true);
            Require(workerFolder.Matches(host[0]) && workerFile.Matches(host[1]) &&
                childFolder.Matches(state[0]) && childFile.Matches(state[1]),"journal_access_controls_changed");
            return new[]{observedParent,observedJournal};
        }

        internal static bool Forbidden(string[] rows)
        {return rows.Any(row=>row.EndsWith(":forbidden_open",StringComparison.Ordinal));}

        static bool CompleteDenied(string[] rows)
        {
            return rows!=null && rows.Length==JournalTokenAccessFixture.CaseCount &&
                rows.Select((row,index)=>row==JournalTokenAccessFixture.CaseName(index)+":denied").All(match=>match);
        }

        internal static void ProbeSequence(Func<string[]> workerProbe,Func<string[]> childProbe,
            Action readback,Dictionary<string,object> record)
        {
            var workerRows=workerProbe();
            string[] childRows=Forbidden(workerRows)?null:childProbe();
            bool forbidden=Forbidden(workerRows) || childRows!=null && Forbidden(childRows);
            if(forbidden)record["journal_access_forbidden_open"]=true;
            readback();
            record["journal_access_readback_verified"]=true;
            Require(!forbidden,"journal_access_forbidden_open");
            Require(CompleteDenied(workerRows) && CompleteDenied(childRows),"journal_access_incomplete");
            record["journal_access_both_denied"]=true;
        }

        string[] Probe(WindowsIsolation process,BridgeChannel channel,string role,Snapshot file,Snapshot folder,int budget)
        {
            var before=Recheck();
            var time=Stopwatch.StartNew();
            Func<int> left=()=> {
                int remaining=budget-(int)time.ElapsedMilliseconds;
                Require(remaining>0,"journal_access_deadline");return remaining;
            };
            int pid=checked((int)process.ChildPid);
            string request=BridgeHostFiles.RandomHex(16), key="journal_access_"+role;
            var admission=new JournalTokenAccessAdmission(process,channel,attempt,role,pid,request,file.Identity,folder.Identity,
                journal.Identity,parent.Identity);
            Require(process.ReducedLaunchTokenVerified && !process.Resumed && process.BridgeInput!=IntPtr.Zero,
                "journal_access_launch_binding");
            process.ResumeBridge();
            channel.Write(new Dictionary<string,object>{{"v",2},{"type","journal_access_probe"},{"attempt",attempt},
                {"role",role},{"request_id",request}},Math.Min(2000,left()));
            process.CloseJournalAccessInput();
            var reply=Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(channel.Read(left())));
            var provisional=JournalTokenAccessNativeFixture.Verify(reply,attempt,role,pid,request,file.Identity,folder.Identity);
            if(Forbidden(provisional))
                record[key+"_provisional_forbidden"]=provisional.Where(row=>row.EndsWith(":forbidden_open",StringComparison.Ordinal)).ToArray();
            channel.Eof(Math.Min(2000,left()));
            process.WaitBridge((uint)left());
            var after=Recheck();
            var incomplete=new List<Dictionary<string,object>>();
            var rows=admission.AdmitNative(reply,process,channel,process.ReducedLaunchTokenVerified,
                process.BridgeInput==IntPtr.Zero,true,process.ExitCode==0,before[1].Identity,before[0].Identity,
                after[1].Identity,after[0].Identity,before[1].Matches(after[1]),incomplete);
            record[key+"_rows"]=rows;
            if(incomplete.Count!=0)record[key+"_incomplete_diagnostics"]=incomplete;
            record[key+"_natural_exit_verified"]=true;
            record.Remove(key+"_provisional_forbidden");
            return rows;
        }

        internal void Run(WindowsIsolation child)
        {
            workerChannel=new BridgeChannel(worker.BridgeOutput,worker.BridgeInput);
            childChannel=new BridgeChannel(child.BridgeOutput,child.BridgeInput);
            ProbeSequence(()=>Probe(worker,workerChannel,"worker",workerFile,workerFolder,5000),
                ()=>Probe(child,childChannel,"child",childFile,childFolder,22000),()=>Recheck(),record);
            record["status"]="journal_access_roles_completed";
        }

        internal static string FinalStatus(Dictionary<string,object> record,bool cleanup)
        {
            if(record.ContainsKey("journal_access_worker_provisional_forbidden") ||
                record.ContainsKey("journal_access_child_provisional_forbidden"))
            {
                record["reason_code"]="journal_access_provisional_forbidden_open";
                return "blocked";
            }
            if(record.ContainsKey("journal_access_forbidden_open"))
            {
                record["reason_code"]="journal_access_forbidden_open";
                return "blocked";
            }
            return cleanup && record.ContainsKey("journal_access_both_denied") &&
                true.Equals(record["journal_access_both_denied"]) &&
                record.ContainsKey("journal_access_readback_verified") && true.Equals(record["journal_access_readback_verified"]) &&
                record.ContainsKey("journal_access_worker_natural_exit_verified") && true.Equals(record["journal_access_worker_natural_exit_verified"]) &&
                record.ContainsKey("journal_access_child_natural_exit_verified") && true.Equals(record["journal_access_child_natural_exit_verified"]) &&
                record.ContainsKey("journal_access_worker_stopped") && true.Equals(record["journal_access_worker_stopped"])
                ? "access_matrix_denied_pending_independent_cleanup":"blocked";
        }

        internal void Stop()
        {
            worker.CloseBridgeInput();worker.Stop();
            if(workerChannel!=null)workerChannel.Dispose();
            if(childChannel!=null)childChannel.Dispose();
            record["journal_access_worker_stopped"]=true;
        }

        public void Dispose() {worker.Dispose();}
    }
}
#endif
