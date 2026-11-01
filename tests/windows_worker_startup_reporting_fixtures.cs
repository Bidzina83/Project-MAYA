using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using ProjectMaya.WindowsRuntime;

internal static class WorkerStartupReportingFixtures
{
    static int checks;
    static void Check(bool ok){checks++;if(!ok)throw new Exception("startup reporting fixture "+checks);}
    static Dictionary<string,object> Capture(string text,bool done=true,bool failed=false)
    {
        var capture=new WorkerStartupCapture();capture.Start();byte[] raw=Encoding.UTF8.GetBytes(text);
        foreach(byte b in raw)capture.Append(new byte[]{b},1);
        if(done)capture.Complete(failed);
        return capture.Snapshot("exited",3);
    }
    sealed class FailureStream:MemoryStream
    {
        public override int ReadByte(){throw new IOException("secret path and canary");}
    }
    sealed class WaitingStream:MemoryStream
    {
        internal readonly ManualResetEvent Release=new ManualResetEvent(false);
        public override int ReadByte(){Release.WaitOne();return -1;}
    }
    static void ChannelFailure(Stream stream,string category)
    {
        using(var channel=new BridgeChannel(stream,new MemoryStream()))
        {
            bool rejected=false;
            try{channel.Read(1000);}catch(StartupFailure e){rejected=e.Message=="bridge_channel_failed";}
            Check(rejected);Check(channel.FailureCategory==category);
        }
    }
    static int Main()
    {
        string prefix="MAYA_WORKER_STARTUP_V1|";
        foreach(string stage in WorkerStartupCapture.Stages)
        foreach(string error in WorkerStartupCapture.Errors)
        {
            var report=Capture(prefix+stage+"|"+error+"\n");
            Check((string)report["diagnostic_stage"]==stage);Check((string)report["diagnostic_error_type"]==error);
        }
        Check((string)Capture(prefix+"service_import|ImportError\r\n")["diagnostic_state"]=="reported_failure");
        foreach(string text in new[]{"private traceback",prefix+"secret|ImportError\n",prefix+"service_import|PrivateClass\n",
            prefix+"service_import|ImportError\nextra",prefix+"service_import|ImportError\n"+prefix+"ready_send|OSError\n",
            prefix+"service_import|ImportError",prefix+"service_import|ImportError|extra\n",new string('x',257),"\u00e9\n"})
        {
            var report=Capture(text);Check(report["diagnostic_stage"]==null);Check(report["diagnostic_error_type"]==null);
            Check((string)report["diagnostic_state"]=="invalid");
        }
        var pending=Capture(prefix+"service_import|ImportError\n",false);
        Check(pending["diagnostic_stage"]==null);Check(false.Equals(pending["stderr_capture_complete"]));
        Check((string)pending["diagnostic_state"]=="pending");
        var broken=Capture(prefix+"request_sync|OSError\n",true,true);
        Check(broken["diagnostic_stage"]==null);Check((string)broken["diagnostic_state"]=="capture_failed");
        var empty=Capture("");Check(0.Equals(empty["stderr_bytes_observed"]));Check(true.Equals(empty["stderr_capture_complete"]));
        var absent=new WorkerStartupCapture().Snapshot("not_created",null);
        Check(absent["stderr_bytes_observed"]==null);Check(absent["exit_code_hex"]==null);Check(false.Equals(absent["stderr_capture_complete"]));
        var afterStop=Capture(prefix+"request_sync|OSError\n");Check((string)afterStop["exit_code_hex"]=="0x00000003");
        var active=new WorkerStartupCapture().Snapshot("running",null);Check(active["exit_code_hex"]==null);
        Check(BridgeChannel.Category(new AggregateException(new EndOfStreamException()))=="eof");
        Check(BridgeChannel.Category(new AggregateException(new IOException(),new IOException()))=="multiple_failures");
        Check(BridgeChannel.Category(new Exception("secret"))=="operation_failed");
        Check(BridgeChannel.Category(new StartupFailure("secret"))=="operation_failed");
        ChannelFailure(new MemoryStream(),"eof");
        ChannelFailure(new MemoryStream(new byte[]{1,0}),"eof");
        ChannelFailure(new MemoryStream(new byte[]{0,0,0,0}),"bridge_frame_size");
        ChannelFailure(new MemoryStream(new byte[]{1,0,0,0,255}),"invalid_utf8");
        ChannelFailure(new MemoryStream(new byte[]{1,0,0,0,120}),"bridge_json_invalid");
        ChannelFailure(new FailureStream(),"io_error");
        using(var stream=new WaitingStream())
        using(var channel=new BridgeChannel(stream,new MemoryStream()))
        {
            try{channel.Read(10);Check(false);}catch(StartupFailure e){Check(e.Message=="bridge_channel_failed");}
            finally{stream.Release.Set();}
            Check(channel.FailureCategory=="bridge_channel_timeout");
        }
        Console.WriteLine(checks+" inert startup reporting checks passed");return 0;
    }
}
