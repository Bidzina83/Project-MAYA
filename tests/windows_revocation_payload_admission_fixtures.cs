using System;
using System.IO;
using System.Text;
using ProjectMaya.WindowsRuntime;

internal static class PayloadAdmissionFixtures
{
    static int Main(string[] args)
    {
        if(!ModelRevocationAdmission.Enabled || (ModelExpiryAdmission.Enabled || ModelBodyAdmission.Enabled || ModelRouteAdmission.Enabled || ModelAttemptAdmission.Enabled))throw new Exception("Wrong fixture profile");
        int count;
        using(var stream=File.OpenRead(args[0]))count=ProductFiles.ReadIndex(stream,true).files.Count;
        if(count!=Int32.Parse(args[2]))throw new Exception("Inventory mismatch");
        bool rejected=false;
        try {using(var stream=File.OpenRead(args[1]))ProductFiles.ReadIndex(stream,true);}catch(StartupFailure){rejected=true;}
        if(!rejected)throw new Exception("Inactive predecessor entries admitted");
        foreach(string name in new[]{"model_expiry_child_entry.py","model_expiry_worker_entry.py"})
        {
            rejected=false;try{ProductFiles.PayloadPath(name);}catch(StartupFailure){rejected=true;}
            if(!rejected)throw new Exception("Inactive expiry entry admitted");
        }
        Console.WriteLine("M04b payload admission passed for "+count+" members; predecessor index and both inactive entries rejected. No product execution.");
        return 0;
    }
}
