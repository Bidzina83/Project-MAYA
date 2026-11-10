using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using ProjectMaya.WindowsRuntime;

internal static class JournalAccessOfflineCheck
{
    static void Require(bool ok,string reason)
    {if(!ok)throw new InvalidDataException(reason);}

    static void Main(string[] args)
    {
        using(var index=File.OpenRead(args[1]))
            Require(ProductFiles.ReadIndex(index,true).files.Count==892,"actual_profile_inventory");

        // Reflection-only context cannot execute the inspected assembly.
        var product=Assembly.ReflectionOnlyLoadFrom(args[0]);
        var names=product.GetManifestResourceNames();
        Require(names.OrderBy(n=>n,StringComparer.Ordinal).SequenceEqual(new[]{
            "MayaPython.payload-index.json","MayaPython.payload.zip"}),"resource_names");
        for(int i=0;i<2;i++)
            using(var embedded=product.GetManifestResourceStream(i==0?"MayaPython.payload-index.json":"MayaPython.payload.zip"))
            using(var bytes=new MemoryStream())
            {
                embedded.CopyTo(bytes);
                Require(bytes.ToArray().SequenceEqual(File.ReadAllBytes(args[i+1])),"resource_bytes");
            }
        var launcher=product.GetType("ProjectMaya.WindowsRuntime.ProtectedPython",true);
        const BindingFlags fields=BindingFlags.Static|BindingFlags.NonPublic;
        Require((string)launcher.GetField("Version",fields).GetRawConstantValue()=="0.2.2-journal-access.1","version");
        Require((string)launcher.GetField("Scope",fields).GetRawConstantValue()=="offline-journal-access-matrix-v1","scope");
        Require(FileVersionInfo.GetVersionInfo(args[0]).FileVersion=="0.2.2.1","file_version");
        Require(product.GetType("ProjectMaya.WindowsRuntime.JournalAccessRuntime")!=null,"access_coordinator");
        foreach(string name in new[]{"FinalOutputInertAdapter","FinalOutputInertHandles","CoordinatorJournalScratchTarget",
            "ProjectMaya.WindowsRuntime.FinalOutputInertAdapter","ProjectMaya.WindowsRuntime.FinalOutputInertHandles",
            "ProjectMaya.WindowsRuntime.CoordinatorJournalScratchTarget","ProjectMaya.WindowsRuntime.JournalTokenAccessWindowsCalls",
            "ProjectMaya.WindowsRuntime.JournalTokenAccessFixture+ProbeSession"})
            Require(product.GetType(name)==null,"excluded_type:"+name);
        Console.WriteLine("Actual access profile index, exact embedded resources, versions and type exclusions passed.");
    }
}
