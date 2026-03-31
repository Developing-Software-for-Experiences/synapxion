// DataProcessor.cs
using System.Text;
namespace Rudwolf.Utils
{
    public class DataProcessor
    {
        private readonly ITokenizer _tokenizer;

        public DataProcessor(ITokenizer tokenizer)
        {
            _tokenizer = tokenizer;
        }

        public void ProcessToBinary(string inputPath, string outputBin, string outputIdx)
        {
            using var binWriter = new BinaryWriter(File.Open(outputBin, FileMode.Create));
            using var idxWriter = new BinaryWriter(File.Open(outputIdx, FileMode.Create));

            long currentOffset = 0;

            foreach (var text in LoadAndFormat(inputPath))
            {
                // Guardar offset
                idxWriter.Write(currentOffset);

                // Tokenizar
                var tokens = _tokenizer.Encode(text);

                // Escribir tokens
                foreach (var token in tokens)
                {
                    binWriter.Write(token);
                }

                currentOffset += tokens.Count;
            }
        }

        private IEnumerable<string> LoadAndFormat(string filePath)
        {
            var ext = Path.GetExtension(filePath).ToLower();

            if (ext == ".txt")
            {
                yield return File.ReadAllText(filePath, Encoding.UTF8);
                yield break;
            }

            // Para CSV/TSV simple (sin librerías externas)
            var separator = ext == ".tsv" ? '\t' : ',';

            using var reader = new StreamReader(filePath, Encoding.UTF8);

            string? headerLine = reader.ReadLine();
            if (headerLine == null) yield break;

            var headers = headerLine.Split(separator);

            int qIdx = Array.IndexOf(headers, "question");
            int tIdx = Array.IndexOf(headers, "think");
            int aIdx = Array.IndexOf(headers, "answer");

            while (!reader.EndOfStream)
            {
                var line = reader.ReadLine();
                if (string.IsNullOrWhiteSpace(line)) continue;

                var cols = line.Split(separator);

                var parts = new List<string>();

                if (qIdx >= 0 && qIdx < cols.Length)
                    parts.Add("<PROMPT> " + cols[qIdx]);

                if (tIdx >= 0 && tIdx < cols.Length)
                    parts.Add("<THINK> " + cols[tIdx]);

                if (aIdx >= 0 && aIdx < cols.Length)
                    parts.Add("<ANSWER> " + cols[aIdx]);

                var finalText = string.Join(" ", parts) + " <EOS> <NEWLINE>";

                yield return finalText;
            }
        }
    }
}