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
        string vocabPath = Path.Combine(outputDir, "vocab.json");

        Directory.CreateDirectory(dataDir);
        Directory.CreateDirectory(outputDir);

        Console.Write("Modo (normal/debug): ");
        var mode = Console.ReadLine()?.ToLower();

        if (mode == "debug")
        {
            Rudwolf.Debug.DebugProgram.Run();
            return;
        }

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
            Console.WriteLine($"[{i}] {Path.GetFileName(files[i])}");

        Console.WriteLine("\nSelecciona archivos (ej: 0,1,2) o escribe 'all': ");
        string? input = Console.ReadLine();

        List<string> selectedFiles = new();

        if (input?.ToLower() == "all")
        {
            selectedFiles = files;
        }
        else
        {
            var indexes = input?.Split(',', StringSplitOptions.RemoveEmptyEntries);

            if (indexes != null)
            {
                foreach (var idx in indexes)
                {
                    if (int.TryParse(idx.Trim(), out int i) && i >= 0 && i < files.Count)
                        selectedFiles.Add(files[i]);
                }
            }
        }

        if (selectedFiles.Count == 0)
        {
            Console.WriteLine("Selección inválida.");
            return;
        }

        // =========================
        // 🔹 SYLLABLE TOKENIZER
        // =========================
        var syllableTokenizer = new SyllableTokenizer();

        if (File.Exists(vocabPath))
        {
            Console.WriteLine("\nCargando vocabulario existente...");
            syllableTokenizer.LoadVocab(vocabPath);
            Console.WriteLine("✔ vocab.json cargado");
        }
        else
        {
            Console.WriteLine("\nConstruyendo vocabulario...");

            IEnumerable<string> StreamAllText()
            {
                foreach (var file in selectedFiles)
                {
                    var ext = Path.GetExtension(file).ToLower();

                    if (ext == ".txt")
                    {
                        using var reader = new StreamReader(file, Encoding.UTF8);
                        string? line;

                        while ((line = reader.ReadLine()) != null)
                        {
                            if (!string.IsNullOrWhiteSpace(line))
                                yield return line + " <EOS> <NEWLINE>";
                        }
                    }
                    else if (ext == ".csv" || ext == ".tsv")
                    {
                        var separator = ext == ".tsv" ? '\t' : ',';
                        using var reader = new StreamReader(file, Encoding.UTF8);

                        reader.ReadLine(); // header

                        string? line;
                        while ((line = reader.ReadLine()) != null)
                        {
                            if (!string.IsNullOrWhiteSpace(line))
                                yield return line + " <EOS> <NEWLINE>";
                        }
                    }
                }
            }

            var allText = StreamAllText();
            syllableTokenizer.BuildVocab(allText);

            syllableTokenizer.SaveVocabHybrid(vocabPath);
            Console.WriteLine("✔ vocab.json generado");
        }

        // 🔥 IMPORTANTE
        syllableTokenizer.AllowWholeWordTokens = false;

        // =========================
        // 🔹 BPE (INT BASED)
        // =========================
        var bpeRules = new List<BpeTokenizer.BpeRule>();
        var bpe = new BpeTokenizer(bpeRules);

        // =========================
        // 🔹 HYBRID TOKENIZER
        // =========================
        var tokenizer = new HybridTokenizer(
            syllableTokenizer,
            bpe,
            syllableTokenizer.GetVocab()
        );

        // =========================
        // 🔹 BUILDER
        // =========================
        var builder = new BinDatasetBuilder(tokenizer);

        foreach (var file in selectedFiles)
        {
            string name = Path.GetFileNameWithoutExtension(file);
            string outBin = Path.Combine(outputDir, name + ".bin");
            string outIdx = Path.Combine(outputDir, name + ".idx");

            Console.WriteLine("\n¿Usar Streaming? (s/n): ");
            string? streams = Console.ReadLine();

            Console.WriteLine($"\nProcesando: {name}");

            bool useStreaming = streams?.ToLower() == "s";

            builder.Build(file, outBin, outIdx, useStreaming);

            Console.WriteLine($"✔ Generado: {name}.bin / {name}.idx");
        }

        Console.WriteLine("\n✔ Todo terminado.");
        Console.WriteLine("Presiona una tecla para salir...");
        Console.ReadKey();
    }
}