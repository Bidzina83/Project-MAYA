using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Windows.Forms;

namespace ProjectMaya.WindowsRuntime
{
    internal sealed class ResetTcpControl : IDisposable
    {
        readonly TcpClient client = new TcpClient(AddressFamily.InterNetwork);
        readonly string attempt;
        readonly NetworkStream stream;

        internal ResetTcpControl(string attempt)
        {
            this.attempt = attempt;
            try
            {
                var connect = client.ConnectAsync("100.127.155.29", 49187);
                if (!connect.Wait(5000)) throw new TimeoutException("reset_tcp_control_connect");
                stream = client.GetStream();
                stream.WriteTimeout = 5000;
                byte[] start = Encoding.ASCII.GetBytes("START " + attempt + "\n");
                stream.Write(start, 0, start.Length);
                if (ReadLine() != "START " + attempt)
                    throw new IOException("reset_tcp_control_start");
            }
            catch { client.Close(); throw; }
        }

        string ReadLine()
        {
            var clock = System.Diagnostics.Stopwatch.StartNew();
            var line = new StringBuilder();
            while (line.Length < 96)
            {
                int left = 5000 - (int)clock.ElapsedMilliseconds;
                if (left <= 0) throw new TimeoutException("reset_tcp_control_read");
                stream.ReadTimeout = left;
                int value = stream.ReadByte();
                if (value == 10) return line.ToString();
                if (value < 32 || value > 126) break;
                line.Append((char)value);
            }
            throw new IOException("reset_tcp_control_frame");
        }

        internal int Finish()
        {
            byte[] stop = Encoding.ASCII.GetBytes("STOP " + attempt + "\n");
            stream.Write(stop, 0, stop.Length);
            string reply = ReadLine(), prefix = "CLOSED " + attempt + " ";
            int count;
            if (!reply.StartsWith(prefix, StringComparison.Ordinal) ||
                !Int32.TryParse(reply.Substring(prefix.Length), NumberStyles.None, CultureInfo.InvariantCulture, out count) ||
                count < 1 || count > 64)
                throw new IOException("reset_tcp_control_close");
            return count - 1;
        }

        public void Dispose() { client.Close(); }
    }

    internal static class ResetPrivateExchange
    {
        internal const string Destination = "synthetic:local-fixture";
        internal const string Answer = "Payment is due within 30 days of invoice.";
        const string Payload = "{\"messages\":[{\"role\":\"system\",\"content\":\"Answer using only the synthetic document provided.\"},{\"role\":\"user\",\"content\":\"Acme purchase order 1042 specifies payment within 30 days of invoice.\\n\\nWhat are Acme's payment terms?\"}],\"model\":\"maya-reset-fixture\",\"max_tokens\":32,\"stream\":false}";

        internal static bool Review(string destination, string payload)
        {
            using (var form = new Form { Text = "Maya Reset: Approve Synthetic Request", Width = 680, Height = 360 })
            using (var timer = new Timer { Interval = 60000 })
            {
                var body = new TextBox { Multiline = true, ReadOnly = true, Dock = DockStyle.Fill,
                    ScrollBars = ScrollBars.Vertical, Text = destination + "\r\n\r\n" + payload };
                var buttons = new FlowLayoutPanel { Dock = DockStyle.Bottom, AutoSize = true };
                var deny = new Button { Text = "Deny", DialogResult = DialogResult.No };
                var allow = new Button { Text = "Approve", DialogResult = DialogResult.Yes };
                buttons.Controls.AddRange(new Control[] { deny, allow });
                form.Controls.Add(body);
                form.Controls.Add(buttons);
                form.CancelButton = deny;
                form.Shown += delegate { deny.Focus(); timer.Start(); };
                timer.Tick += delegate { timer.Stop(); form.DialogResult = DialogResult.No; form.Close(); };
                return form.ShowDialog() == DialogResult.Yes;
            }
        }

        static bool Field(Dictionary<string, object> record, string key, string expected)
        {
            object value;
            return record.TryGetValue(key, out value) &&
                (expected == null ? value == null : String.Equals(value as string, expected, StringComparison.Ordinal));
        }

        // The coordinator owns the verified child and must stop its job on any failure.
        internal static bool RunChild(WindowsIsolation child, Func<string, string, bool> review)
        {
            using (var channel = new BridgeChannel(child.BridgeOutput, child.BridgeInput))
            {
                try
                {
                    child.ResumeBridge();
                    bool approved = Run(channel, review);
                    child.CloseBridgeInput();
                    channel.Eof(10000);
                    child.WaitBridge(10000);
                    return approved;
                }
                catch
                {
                    child.CloseBridgeInput();
                    child.Stop();
                    throw;
                }
            }
        }

        internal static bool Run(BridgeChannel channel, Func<string, string, bool> review)
        {
            var request = channel.Read(60000);
            if (request.Count != 2 || !Field(request, "kind", "request") || !Field(request, "payload", Payload))
                throw new StartupFailure("reset_private_request_rejected");

            bool approved = review(Destination, Payload);
            string answer = approved ? Answer : null;
            channel.Write(new Dictionary<string, object> { { "kind", "decision" }, { "answer", answer } }, 5000);
            var completion = channel.Read(10000);
            if (completion.Count != 2 || !Field(completion, "kind", "complete") || !Field(completion, "answer", answer))
                throw new StartupFailure("reset_private_completion_rejected");
            return approved;
        }
    }
}
