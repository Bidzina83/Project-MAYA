#if MAYA_DELETE_CHILD_CONTROL_INERT || HERMES_JOURNAL_DELETE_CHILD_SOURCE
using System;
using System.Linq;
using System.Security.AccessControl;
using System.Security.Principal;

namespace ProjectMaya.WindowsRuntime
{
    // Descriptor transformation only. This code does not open or modify an object.
    internal sealed class DeleteChildControlDescriptor
    {
        const int DeleteChild=64;
        readonly byte[] original, proposed;

        static byte[] Bytes(RawSecurityDescriptor descriptor)
        {
            var bytes=new byte[descriptor.BinaryLength];
            descriptor.GetBinaryForm(bytes,0);
            return bytes;
        }

        static void Require(bool valid,string diagnostic="restore_binding")
        {
            if(!valid)
            {
                var error=new ArgumentException("delete_child_control_descriptor");
                error.Data["delete_child_descriptor_check"]=diagnostic;
                throw error;
            }
        }

        internal DeleteChildControlDescriptor(byte[] baseline,SecurityIdentifier user,SecurityIdentifier package)
        {
            Require(baseline!=null && user!=null && package!=null && !user.Equals(package),"input_binding");
            var descriptor=new RawSecurityDescriptor(baseline,0);
            var dacl=descriptor.DiscretionaryAcl;
            Require(dacl!=null,"dacl_missing");
            Require((descriptor.ControlFlags&ControlFlags.DiscretionaryAclProtected)==0,"dacl_protected");
            bool packageAllows=false, userFound=false;
            int inheritedAt=0;
            foreach(GenericAce generic in dacl)
            {
                var ace=generic as CommonAce;
                string failed=ace==null?"not_common_ace":ace.IsCallback?"callback_ace":
                    ace.AceQualifier!=AceQualifier.AccessAllowed?"not_allow_ace":!ace.IsInherited?"not_inherited":null;
                if(failed!=null)
                {
                    var error=new ArgumentException("delete_child_control_descriptor");
                    error.Data["delete_child_descriptor_check"]="unexpected_ace";
                    error.Data["delete_child_ace_ordinal"]=inheritedAt+1;
                    error.Data["delete_child_ace_type"]=(int)generic.AceType;
                    error.Data["delete_child_ace_flags"]=(int)generic.AceFlags;
                    error.Data["delete_child_ace_failed_predicate"]=failed;
                    throw error;
                }
                if(ace.SecurityIdentifier.Equals(package) && (ace.AceFlags&AceFlags.InheritOnly)==0)
                    packageAllows|=(ace.AccessMask&DeleteChild)!=0;
                if(ace.SecurityIdentifier.Equals(user) && (ace.AceFlags&AceFlags.InheritOnly)==0)
                {
                    Require((ace.AccessMask&DeleteChild)==0,"operator_already_granted");
                    userFound=true;
                }
                inheritedAt++;
            }
            Require(inheritedAt!=0 && userFound && packageAllows,
                inheritedAt==0?"dacl_empty":!userFound?"operator_entry_missing":"package_right_missing");
            original=Bytes(descriptor);
            dacl.InsertAce(0,new CommonAce(AceFlags.None,AceQualifier.AccessAllowed,DeleteChild,user,false,null));
            proposed=Bytes(descriptor);
        }

        internal byte[] Proposed {get{return (byte[])proposed.Clone();}}
        internal bool MatchesApplied(byte[] observed) {return observed!=null && proposed.SequenceEqual(observed);}
        internal bool MatchesRestored(byte[] observed) {return observed!=null && original.SequenceEqual(observed);}

        internal byte[] Restore(byte[] observed,bool jobsStopped,bool sameControl)
        {
            Require(jobsStopped && sameControl && MatchesApplied(observed));
            return (byte[])original.Clone();
        }
    }
}
#endif
