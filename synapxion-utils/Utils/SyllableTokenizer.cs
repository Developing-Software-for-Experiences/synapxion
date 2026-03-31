// SyllableTokenizer.cs (OPTIMIZADO)
using System.Text;
using System.Text.RegularExpressions;
using Newtonsoft.Json;


namespace Rudwolf.Utils
{
    public class SyllableTokenizer : ITokenizer
    {
        private static readonly Regex CleanRegex = new(
            @"[^a-záéíóúüñ¿?¡!.,;:—""' \n]",
            RegexOptions.Compiled
        );

        private readonly Dictionary<string, string> replacements = new()
    {
        {"á","a"}, {"é","e"}, {"í","i"},
        {"ó","o"}, {"ú","u"}, {"ü","u"}, {"ñ","n"}
    };

        private readonly List<string> specialTokens = new()
    {
        "<PAD>", "<UNK>", "<BOS>", "<EOS>", "<SEP>",
        "<CLS>", "<MASK>", "<PROMPT>", "<RESPONSE>",
        "<THINK>", "<ANSWER>", "<SYS>", "<USR>", "<BOT>",
        "<COMA>", "<PUNTO>",
        "<INTERROGACION_ABRE>", "<INTERROGACION_CIERRA>",
        "<ADMIRACION_ABRE>", "<ADMIRACION_CIERRA>",
        "<PUNTO_Y_COMA>", "<DOS_PUNTOS>",
        "<GUION>", "<GUION_LARGO>",
        "<COMILLAS_ABRE>", "<COMILLAS_CIERRA>",
        "<COMILLAS_SIMPLES_ABRE>", "<COMILLAS_SIMPLES_CIERRA>",
        "<SPACE>", "<NEWLINE>", "<TAB>"
    };

        private List<string> vocab;
        private Dictionary<string, int> stoi;
        private Dictionary<int, string> itos;

        // 🔥 CACHE (clave del rendimiento)
        private readonly Dictionary<string, List<int>> wordCache = new();
        private readonly Dictionary<string, List<string>> syllableCache = new();

        public int PadTokenId { get; private set; }
        public int UnkTokenId { get; private set; }
        public int BosTokenId { get; private set; }
        public int EosTokenId { get; private set; }

        public SyllableTokenizer(List<string>? initialVocab = null)
        {
            vocab = new List<string>(specialTokens);

            if (initialVocab != null)
                vocab.AddRange(initialVocab);

            RebuildMappings();
        }

        private void RebuildMappings()
        {
            stoi = new Dictionary<string, int>(vocab.Count);
            itos = new Dictionary<int, string>(vocab.Count);

            for (int i = 0; i < vocab.Count; i++)
            {
                stoi[vocab[i]] = i;
                itos[i] = vocab[i];
            }

            PadTokenId = stoi.GetValueOrDefault("<PAD>", 0);
            UnkTokenId = stoi.GetValueOrDefault("<UNK>", 1);
            BosTokenId = stoi.GetValueOrDefault("<BOS>", 2);
            EosTokenId = stoi.GetValueOrDefault("<EOS>", 3);
        }

        // ------------------------
        // CLEAN
        // ------------------------
        private string CleanText(string text)
        {
            if (text == null) return "";
            text = text.ToLowerInvariant();
            return CleanRegex.Replace(text, " ");
        }

        private string ApplyReplacements(string text)
        {
            foreach (var kv in replacements)
                text = text.Replace(kv.Key, kv.Value);

            return text;
        }

        private string TextToTokenMarkers(string text)
        {
            return text
                .Replace(",", " <COMA> ")
                .Replace(".", " <PUNTO> ")
                .Replace(";", " <PUNTO_Y_COMA> ")
                .Replace(":", " <DOS_PUNTOS> ")
                .Replace("-", " <GUION> ")
                .Replace("—", " <GUION_LARGO> ")
                .Replace("\"", " <COMILLAS_ABRE> ")
                .Replace("'", " <COMILLAS_SIMPLES_ABRE> ")
                .Replace("?", " <INTERROGACION_CIERRA> ")
                .Replace("¿", " <INTERROGACION_ABRE> ")
                .Replace("!", " <ADMIRACION_CIERRA> ")
                .Replace("¡", " <ADMIRACION_ABRE> ")
                .Replace(" ", " <SPACE> ")
                .Replace("\n", " <NEWLINE> ");
        }

        // ------------------------
        // ENCODE (OPTIMIZADO)
        // ------------------------
        public List<int> Encode(string text)
        {
            var tokens = new List<int>(256); // tamaño inicial evita realloc

            tokens.Add(BosTokenId);

            text = CleanText(text);
            text = TextToTokenMarkers(text);
            text = ApplyReplacements(text);

            foreach (var word in text.Split(' ', StringSplitOptions.RemoveEmptyEntries))
            {
                // 🔥 CACHE HIT
                if (wordCache.TryGetValue(word, out var cached))
                {
                    tokens.AddRange(cached);
                    continue;
                }

                List<int> encodedWord;

                if (stoi.TryGetValue(word, out int id))
                {
                    encodedWord = new List<int> { id };
                }
                else
                {
                    // 🔥 CACHE de sílabas
                    if (!syllableCache.TryGetValue(word, out var sylls))
                    {
                        try
                        {
                            sylls = Silabificador.SplitIntoSyllables(word);
                        }
                        catch
                        {
                            sylls = new List<string> { word };
                        }

                        syllableCache[word] = sylls;
                    }

                    encodedWord = new List<int>(sylls.Count);

                    foreach (var s in sylls)
                    {
                        if (stoi.TryGetValue(s, out int sid))
                            encodedWord.Add(sid);
                        else
                            encodedWord.Add(UnkTokenId);
                    }
                }

                // Guardar en cache
                wordCache[word] = encodedWord;
                tokens.AddRange(encodedWord);
            }

            tokens.Add(EosTokenId);

            return tokens;
        }

        // ------------------------
        // DECODE
        // ------------------------
        public string Decode(IEnumerable<int> tokenIds)
        {
            var sb = new StringBuilder();

            foreach (var id in tokenIds)
            {
                if (!itos.TryGetValue(id, out var tok))
                    tok = "<UNK>";

                switch (tok)
                {
                    case "<COMA>": sb.Append(","); break;
                    case "<PUNTO>": sb.Append("."); break;
                    case "<SPACE>": sb.Append(" "); break;
                    case "<NEWLINE>": sb.Append("\n"); break;
                    default:
                        if (!tok.StartsWith("<"))
                            sb.Append(tok);
                        break;
                }
            }

            return sb.ToString();
        }

        // ------------------------
        // SAVE / LOAD
        // ------------------------
        public void SaveVocab(string path)
        {
            // Serializar directamente como lista (más limpio para Python)
            var json = JsonConvert.SerializeObject(vocab, Formatting.None);

            // UTF-8 SIN BOM
            var utf8NoBom = new UTF8Encoding(encoderShouldEmitUTF8Identifier: false);

            File.WriteAllText(path, json, utf8NoBom);

            // 🔍 Verificación
            if (!File.Exists(path))
                throw new Exception("El archivo no fue creado.");

            // Leer bytes para verificar BOM
            var bytes = File.ReadAllBytes(path);

            if (bytes.Length >= 3 &&
                bytes[0] == 0xEF &&
                bytes[1] == 0xBB &&
                bytes[2] == 0xBF)
            {
                throw new Exception("El archivo contiene BOM. Falló la escritura sin BOM.");
            }

            // Verificar que el JSON sea válido
            try
            {
                var readJson = File.ReadAllText(path, Encoding.UTF8);
                var test = JsonConvert.DeserializeObject<List<string>>(readJson);

                if (test == null || test.Count == 0)
                    throw new Exception("El JSON se guardó pero está vacío o inválido.");
            }
            catch (Exception ex)
            {
                throw new Exception("El archivo se guardó pero no es JSON válido: " + ex.Message);
            }
        }

        public void LoadVocab(string path)
        {
            if (!File.Exists(path))
                throw new FileNotFoundException("No se encontró el vocabulario.", path);

            var json = File.ReadAllText(path, Encoding.UTF8);

            var data = JsonConvert.DeserializeObject<List<string>>(json);

            if (data == null || data.Count == 0)
                throw new Exception("El vocabulario está vacío o corrupto.");

            vocab = data;

            RebuildMappings();

            // Limpiar caches
            wordCache.Clear();
            syllableCache.Clear();
        }
        public void BuildVocab(IEnumerable<string> texts)
        {
            var unique = new HashSet<string>();

            foreach (var text in texts)
            {
                var clean = CleanText(text);
                clean = TextToTokenMarkers(clean);
                clean = ApplyReplacements(clean);

                foreach (var word in clean.Split(' ', StringSplitOptions.RemoveEmptyEntries))
                {
                    if (word.StartsWith("<") && word.EndsWith(">"))
                    {
                        unique.Add(word);
                    }
                    else
                    {
                        if (!syllableCache.TryGetValue(word, out var sylls))
                        {
                            try
                            {
                                sylls = Silabificador.SplitIntoSyllables(word);
                            }
                            catch
                            {
                                sylls = new List<string> { word };
                            }

                            syllableCache[word] = sylls;
                        }

                        foreach (var s in sylls)
                            unique.Add(s);
                    }
                }
            }

            var sorted = unique.ToList();
            sorted.Sort();

            vocab = new List<string>(specialTokens);
            vocab.AddRange(sorted);

            RebuildMappings();
        }
    }
}
