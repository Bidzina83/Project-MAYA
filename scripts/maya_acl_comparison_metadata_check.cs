using System;
using System.Reflection;

internal static class AclComparisonMetadataCheck
{
    static int Main(string[] args)
    {
        var assembly=Assembly.ReflectionOnlyLoadFrom(args[0]);
        if(assembly.EntryPoint.DeclaringType.FullName!="DeleteChildAclComparisonNative" ||
            assembly.GetManifestResourceNames().Length!=0)return 1;
        Console.WriteLine("Standalone entry point and zero embedded resources verified.");
        return 0;
    }
}
