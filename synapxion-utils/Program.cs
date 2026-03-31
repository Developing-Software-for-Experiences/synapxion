using Rudwolf.Utils;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;

class Program
{
    static void Main()
    {
        string baseDir = AppDomain.CurrentDomain.BaseDirectory;

        string dataDir = Path.Combine(baseDir, "DataSets");
        string outputDir = Path.Combine(baseDir, "Resultados");
        string vocabPath = Path.Combine(baseDir, "Resultados/vocab.json");

        Directory.CreateDirectory(dataDir);
        Directory.CreateDirectory(outputDir);

        Console.WriteLine("=== Generador de Dataset (.bin) ===\n");

        var files = Directory.GetFiles(dataDir)
            .Where(f => f.EndsWith(".csv") || f.EndsWith(".tsv") || f.EndsWith(".txt"))
            .ToList();

        if (files.Count == 0)
        {
            Console.WriteLine("No hay archivos en /DataSets/");
            return;
        }

        Console.WriteLine("Archivos disponibles:\n");

        for (int i = 0; i < files.Count; i++)
        {
            Console.WriteLine($"[{i}] {Path.GetFileName(files[i])}");
        }

        Console.WriteLine("\nSelecciona archivos (ej: 0,1,2) o escribe 'all': ");
        string? input = Console.ReadLine();

        List<string> selectedFiles = new();

        if (input?.ToLower() == "all")
        {
            selectedFiles = files;
        }
        else
        {
            var indexes = input.Split(',', StringSplitOptions.RemoveEmptyEntries);

            foreach (var idx in indexes)
            {
                if (int.TryParse(idx.Trim(), out int i) && i >= 0 && i < files.Count)
                {
                    selectedFiles.Add(files[i]);
                }
            }
        }

        if (selectedFiles.Count == 0)
        {
            Console.WriteLine("Selección inválida.");
            return;
        }

        Console.WriteLine("\nConstruyendo vocabulario...");

        var tokenizer = new SyllableTokenizer();

        Console.WriteLine("\nConstruyendo vocabulario (modo streaming)...");

        IEnumerable<string> StreamAllText()
        {
            foreach (var file in selectedFiles)
            {
                foreach (var text in LoadFormattedText(file))
                {
                    yield return text;
                }
            }
        }

        tokenizer.BuildVocab(StreamAllText());
        tokenizer.SaveVocab(vocabPath);

        Console.WriteLine("vocab.json generado");

        var builder = new BinDatasetBuilder(tokenizer);

        foreach (var file in selectedFiles)
        {
            string name = Path.GetFileNameWithoutExtension(file);

            string outBin = Path.Combine(outputDir, name + ".bin");
            string outIdx = Path.Combine(outputDir, name + ".idx");

            Console.WriteLine($"\nProcesando: {name}");

            builder.Build(file, outBin, outIdx);

            Console.WriteLine($"✔ Generado: {name}.bin / {name}.idx");
        }

        Console.WriteLine("\n✔ Todo terminado.");
        Console.WriteLine("Presiona una tecla para salir...");
        Console.ReadKey();
    }

    // 🔹 Reutilizamos misma lógica que tu builder
    static IEnumerable<string> LoadFormattedText(string path)
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