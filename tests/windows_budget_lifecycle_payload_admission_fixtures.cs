using System;
using System.IO;
using ProjectMaya.WindowsRuntime;

internal static class PayloadAdmissionFixtures
{
    static int Main(string[] args)
    {
        if(!ModelBudgetAdmission.Enabled || ModelReplayAdmission.Enabled || ModelRevocationAdmission.Enabled ||
            ModelExpiryAdmission.Enabled || ModelBodyAdmission.Enabled || ModelRouteAdmission.Enabled || ModelAttemptAdmission.Enabled)
            throw new Exception("Wrong fixture profile");
        foreach(string index in new[]{args[0],args[1]})
        {
            using(var stream=File.OpenRead(index))
                if(ProductFiles.ReadIndex(stream,true).files.Count!=6781)throw new Exception("Inventory mismatch");
        }
        foreach(string name in new[]{"model_replay_child_entry.py","model_replay_worker_entry.py"})
        {
            bool rejected=false;try{ProductFiles.PayloadPath(name);}catch(StartupFailure){rejected=true;}
            if(!rejected)throw new Exception("Inactive replay entry admitted");
        }
        foreach(string name in new[]{"model_budget_child_entry.py","model_budget_worker_entry.py"})
            if(ProductFiles.PayloadPath(name)!=name)throw new Exception("Budget entry rejected");
        Console.WriteLine("Budget2 and Budget1 indexes admitted: 6781 members each; inactive replay roots rejected. Content identity is separately pinned. No product execution.");
        return 0;
    }
}
