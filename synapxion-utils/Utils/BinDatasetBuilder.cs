// BinDatasetBuilder.cs
using System.Text;

namespace Rudwolf.Utils
{
    public class BinDatasetBuilder
    {
        private readonly ITokenizer _tokenizer;

        public BinDatasetBuilder(ITokenizer tokenizer)
        {
            _tokenizer = tokenizer;
        }

        public void Build(string inputPath, string outputBin, string outputIdx)
        {
            using var binWriter = new BinaryWriter(File.Open(outputBin, FileMode.Create));
            using var idxWriter = new BinaryWriter(File.Open(outputIdx, FileMode.Create));

            long offset = 0;

            foreach (var text in LoadFormattedText(inputPath))
            {
                // Guardar offset
                idxWriter.Write(offset);

                // 🔥 Tokenizar UNA sola vez
                var tokens = _tokenizer.Encode(text);

                // 🔥 Escribir directo a binario
                foreach (var t in tokens)
                    binWriter.Write(t);

                offset += tokens.Count;
            }
        }

        // ------------------------
        // FORMATEO (igual que tu Python original)
        // ------------------------
        private IEnumerable<string> LoadFormattedText(string path)
        {
            var ext = Path.GetExtension(path).ToLower();

            if (ext == ".txt")
            {
                yield return File.ReadAllText(path, Encoding.UTF8);
                yield break;
            }

            var separator = ext == ".tsv" ? '\t' : ',';

            using var reader = new StreamReader(path, Encoding.UTF8);

            var header = reader.ReadLine();
            if (header == null) yield break;

            var columns = header.Split(separator);

            int q = Array.IndexOf(columns, "question");
            int t = Array.IndexOf(columns, "think");
            int a = Array.IndexOf(columns, "answer");

            while (!reader.EndOfStream)
            {
                var line = reader.ReadLine();
                if (string.IsNullOrWhiteSpace(line)) continue;

                var cols = line.Split(separator);

                var parts = new List<string>();

                if (q >= 0 && q < cols.Length)
                    parts.Add("<PROMPT> " + cols[q]);

                if (t >= 0 && t < cols.Length)
                    parts.Add("<THINK> " + cols[t]);

                if (a >= 0 && a < cols.Length)
                    parts.Add("<ANSWER> " + cols[a]);

                var finalText = string.Join(" ", parts) + " <EOS> <NEWLINE>";

                yield return finalText;
            }
        }
    }
}
