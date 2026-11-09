using System;
using System.IO;
using ProjectMaya.WindowsRuntime;

internal static class FinalPayloadFixtures
{
    static int Main(string[] args)
    {
        if(!ModelFinalAdmission.Enabled || ModelAllowlistAdmission.Enabled || ModelMalformedAdmission.Enabled || ModelOutputDenialAdmission.Enabled || ModelRecreateAdmission.Enabled || ModelBudgetAdmission.Enabled)
            throw new Exception("Wrong profile");
        using(var stream=File.OpenRead(args[0]))
            if(ProductFiles.ReadIndex(stream,true).files.Count!=6787)
                throw new Exception("New inventory mismatch");
        bool rejected=false;
        try { using(var stream=File.OpenRead(args[1])) ProductFiles.ReadIndex(stream,true); }
        catch(StartupFailure){rejected=true;}
        if(!rejected)throw new Exception("Inactive predecessor index was admitted");
        foreach(string path in new[]{"model_allowlist_child_entry.py","model_allowlist_worker_entry.py","model_recreate_child_entry.py","model_recreate_worker_entry.py",
                                     "model_budget_child_entry.py","model_budget_worker_entry.py",
                                     "model_replay_child_entry.py","model_replay_worker_entry.py"})
        {
            rejected=false;try{ProductFiles.PayloadPath(path);}catch(StartupFailure){rejected=true;}
            if(!rejected)throw new Exception("Inactive root admitted");
        }
        foreach(string path in new[]{"model_final_child_entry.py","model_final_worker_entry.py",
                                     "model_validation_worker_entry.py","project_maya/hermes_plugins/model_budget.py",
                                     "project_maya/hermes_plugins/model_recreate.py","project_maya/bridge/model_output_denial.py","project_maya/bridge/model_malformed_response.py","project_maya/bridge/model_allowlist_response.py","project_maya/bridge/model_final_text.py"})
            if(ProductFiles.PayloadPath(path)!=path.Replace('/',Path.DirectorySeparatorChar))
                throw new Exception("Required member path normalization mismatch");
        Console.WriteLine("M08 actual profile admits all 6787 members; M07c index/inactive roots rejected; canonical helpers retained.");
        return 0;
    }
}
