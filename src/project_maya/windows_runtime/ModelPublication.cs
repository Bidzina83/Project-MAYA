using System;
using System.Threading;
using System.Threading.Tasks;

namespace ProjectMaya.WindowsRuntime
{
    internal static class ModelPublication
    {
        // Cancellation before commit prevents a queued UI action from displaying later.
        // Once commit starts, failure is uncertain: bytes cannot be recalled.
        internal static void Run(Action<Action> dispatch, Action commit, int milliseconds)
        {
            if(dispatch==null || commit==null || milliseconds<1 || milliseconds>2000)
                throw new StartupFailure("model_operator_publication_arguments");
            int phase=0;var completed=new TaskCompletionSource<bool>();
            try
            {
                dispatch(delegate {
                    if(Interlocked.CompareExchange(ref phase,1,0)!=0){completed.TrySetResult(false);return;}
                    try{commit();completed.TrySetResult(true);}
                    catch{completed.TrySetResult(false);}
                });
                if(!completed.Task.Wait(milliseconds) || !completed.Task.Result)
                    throw new StartupFailure("model_operator_publication_failed");
            }
            catch
            {
                int observed=Interlocked.CompareExchange(ref phase,2,0);
                throw new StartupFailure(observed==0?"model_operator_not_published":"model_operator_publication_uncertain");
            }
        }
    }
}
