using System;
using System.IO;
using ProjectMaya.WindowsRuntime;

internal static class OutputDenialPayloadFixtures
{
    static int Main(string[] args)
    {
        if(!ModelOutputDenialAdmission.Enabled || ModelRecreateAdmission.Enabled || ModelBudgetAdmission.Enabled)
            throw new Exception("Wrong profile");
        using(var stream=File.OpenRead(args[0]))
            if(ProductFiles.ReadIndex(stream,true).files.Count!=6783)
                throw new Exception("New inventory mismatch");
        bool rejected=false;
        try { using(var stream=File.OpenRead(args[1])) ProductFiles.ReadIndex(stream,true); }
        catch(StartupFailure){rejected=true;}
        if(!rejected)throw new Exception("Inactive predecessor index was admitted");
        foreach(string path in new[]{"model_recreate_child_entry.py","model_recreate_worker_entry.py",
                                     "model_budget_child_entry.py","model_budget_worker_entry.py",
                                     "model_replay_child_entry.py","model_replay_worker_entry.py"})
        {
            rejected=false;try{ProductFiles.PayloadPath(path);}catch(StartupFailure){rejected=true;}
            if(!rejected)throw new Exception("Inactive root admitted");
        }
        foreach(string path in new[]{"model_output_deny_child_entry.py","model_output_deny_worker_entry.py",
                                     "model_validation_worker_entry.py","project_maya/hermes_plugins/model_budget.py",
                                     "project_maya/hermes_plugins/model_recreate.py","project_maya/bridge/model_output_denial.py"})
            if(ProductFiles.PayloadPath(path)!=path.Replace('/',Path.DirectorySeparatorChar))
                throw new Exception("Required member path normalization mismatch");
        Console.WriteLine("M06 actual profile admits all 6783 members; Recreate1 index/inactive roots rejected; canonical helpers retained.");
        return 0;
    }
}
