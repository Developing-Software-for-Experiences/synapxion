using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;

namespace Rudwolf.Utils
{
    public enum DatasetPreset
    {
        Completion,
        Chat,
        Instruction,
        Reasoning,
        Multimodal
    }

    public class BinDatasetBuilder
    {
        private readonly ITokenizer _tokenizer;
        private readonly DatasetPreset _preset;

        private const string MAGIC = "SYNIDXv2";

        private readonly int _thinkId;
        private readonly int _answerId;
        private readonly int _outputId;

        public BinDatasetBuilder(ITokenizer tokenizer, DatasetPreset preset = DatasetPreset.Chat)
        {
            _tokenizer = tokenizer;
            _preset = preset;

            _thinkId = SafeTokenId("<THINK>");
            _answerId = SafeTokenId("<ANSWER>");
            _outputId = SafeTokenId("<OUTPUT>");
        }

        // =========================================================
        // 🔹 BUILD
        // =========================================================
        public void Build(string inputPath, string outputBin, string outputIdx, bool useStreaming = false)
        {
            string tempBin = outputBin + ".tmp";
            string tempIdx = outputIdx + ".tmp";

            long globalOffset = 0;
            int written = 0;

            using var binWriter = new BinaryWriter(File.Create(tempBin));
            using var idxWriter = new BinaryWriter(File.Create(tempIdx));

            idxWriter.Write(Encoding.ASCII.GetBytes(MAGIC));
            long countPos = idxWriter.BaseStream.Position;
            idxWriter.Write((long)0);

            foreach (var text in ReadInput(inputPath))
            {
                var formatted = FormatByPreset(text);

                if (ProcessSample(formatted, binWriter, idxWriter,
                    ref globalOffset, useStreaming))
                {
                    written++;
                }
            }

            idxWriter.BaseStream.Seek(countPos, SeekOrigin.Begin);
            idxWriter.Write((long)written);

            Replace(tempIdx, outputIdx);
            Replace(tempBin, outputBin);

            // 🔥 metadata (para python en el futuro)
            SaveMetadata(outputBin, written);

            Console.WriteLine($"✔ Samples: {written}");
            Console.WriteLine($"✔ Preset: {_preset}");
        }

        // =========================================================
        // 🔹 INPUT
        // =========================================================
        private IEnumerable<string> ReadInput(string path)
        {
            var ext = Path.GetExtension(path).ToLower();

            if (ext == ".csv" || ext == ".tsv")
                return ReadCsv(path);

            return File.ReadLines(path);
        }

        private IEnumerable<string> ReadCsv(string path)
        {
            var sep = Path.GetExtension(path).ToLower() == ".tsv" ? '\t' : ',';

            using var sr = new StreamReader(path, Encoding.UTF8);

            var headers = sr.ReadLine()?.Split(sep);
            if (headers == null) yield break;

            var roles = AskColumnRoles(headers);

            string? line;
            while ((line = sr.ReadLine()) != null)
            {
                if (string.IsNullOrWhiteSpace(line)) continue;
                yield return FormatCsvLine(line, sep, roles);
            }
        }

        // =========================================================
        // 🔹 FORMAT (🔥 CLAVE)
        // =========================================================
        private string FormatByPreset(string text)
        {
            return _preset switch
            {
                DatasetPreset.Completion =>
                    text + " <EOS>",

                DatasetPreset.Chat =>
                    $"<PROMPT> {text} <ANSWER> ",

                DatasetPreset.Instruction =>
                    $"<PROMPT> {text} <ANSWER> ",

                DatasetPreset.Reasoning =>
                    $"<PROMPT> {text} <THINK> ",

                DatasetPreset.Multimodal =>
                    $"<INPUT> {text} <OUTPUT> ",

                _ => text + " <EOS>"
            };
        }

        private string FormatCsvLine(string line, char sep, Dictionary<int, string> roles)
        {
            var cols = line.Split(sep);
            var parts = new List<string>();

            foreach (var kv in roles)
            {
                if (kv.Key >= cols.Length || kv.Value == "skip") continue;

                string prefix = kv.Value switch
                {
                    "prompt" => "<PROMPT> ",
                    "think" => "<THINK> ",
                    "answer" => "<ANSWER> ",
                    "output" => "<OUTPUT> ",
                    "input" => "<INPUT> ",
                    _ => ""
                };

                parts.Add(prefix + cols[kv.Key]);
            }

            return string.Join(" ", parts) + " <EOS>";
        }

        // =========================================================
        // 🔹 SAMPLE PROCESSING
        // =========================================================
        private bool ProcessSample(
            string text,
            BinaryWriter binWriter,
            BinaryWriter idxWriter,
            ref long offset,
            bool streaming)
        {
            var tokens = _tokenizer.Encode(text);
            if (tokens == null || tokens.Count < 2) return false;

            int targetStart = FindTargetStart(tokens);

            if (targetStart < 0 || targetStart >= tokens.Count)
                return false;

            foreach (var t in tokens)
                binWriter.Write(t);

            idxWriter.Write(offset);
            idxWriter.Write((long)tokens.Count);
            idxWriter.Write((long)targetStart);

            offset += tokens.Count;
            return true;
        }

        private int FindTargetStart(List<int> tokens)
        {
            int start = -1;

            for (int i = 0; i < tokens.Count; i++)
            {
                int t = tokens[i];

                if (_preset == DatasetPreset.Reasoning && t == _thinkId)
                    return i + 1;

                if (t == _answerId || t == _outputId)
                    start = i + 1;
            }

            return start;
        }

        // =========================================================
        // 🔹 UTILS
        // =========================================================
        private int SafeTokenId(string token)
        {
            var id = _tokenizer.TokenToId(token);
            return id == _tokenizer.UnkTokenId ? -1 : id;
        }

        private void Replace(string tmp, string final)
        {
            if (File.Exists(final)) File.Delete(final);
            File.Move(tmp, final);
        }

        private void SaveMetadata(string binPath, int count)
        {
            var meta = new
            {
                preset = _preset.ToString(),
                samples = count,
                version = "v2"
            };

            File.WriteAllText(
                Path.ChangeExtension(binPath, ".meta.json"),
                JsonSerializer.Serialize(meta, new JsonSerializerOptions { WriteIndented = true })
            );
        }

        private Dictionary<int, string> AskColumnRoles(string[] headers)
        {
            var roles = new Dictionary<int, string>();

            Console.WriteLine("\n=== CONFIGURAR COLUMNAS ===");

            for (int i = 0; i < headers.Length; i++)
            {
                Console.Write($"{headers[i]} -> ");
                var role = Console.ReadLine()?.Trim().ToLower() ?? "skip";
                roles[i] = role;
            }

            return roles;
        }
    }
}