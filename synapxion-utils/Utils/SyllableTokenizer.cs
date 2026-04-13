using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.IO;
using System.Text;
using System.Globalization;
using System.Linq;
using Newtonsoft.Json;

namespace Rudwolf.Utils
{
    public class SyllableTokenizer : ITokenizer
    {
        // ------------------------
        // SPECIAL TOKENS
        // ------------------------
        private readonly List<string> specialTokens = new()
        {
            "<PAD>", "<UNK>", "<BOS>", "<EOS>", "<NUM>",

            "<SPACE>", "<NEWLINE>", "<TAB>",

            "<PROMPT>", "<THINK>", "<ANSWER>", "<OUTPUT>",
            "<MEMORY>", "</MEMORY>", // ✅ faltaban

            "<COMA>", "<PUNTO>",
            "<INTERROGACION_ABRE>", "<INTERROGACION_CIERRA>",
            "<ADMIRACION_ABRE>", "<ADMIRACION_CIERRA>",
            "<DOS_PUNTOS>", "<PUNTO_Y_COMA>",

            "<GUION>", "<GUION_LARGO>",

            "<COMILLA_SIMPLE>", "<COMILLA_DOBLE>",
            "<PARENTESIS_ABRE>", "<PARENTESIS_CIERRA>",
            "<CORCHETE_ABRE>", "<CORCHETE_CIERRA>",
            "<LLAVE_ABRE>", "<LLAVE_CIERRA>",

            "<SLASH>", "<BACKSLASH>",
            "<IGUAL>", "<MENOR>", "<MAYOR>", "<PIPE>",

            "<PORCENTAJE>", "<DOLAR>", "<AMPERSAND>",
            "<CIRCUNFLEJO>", "<TILDE>", "<BACKTICK>",
            "<GRADO>", "<NEGACION>", "<ASTERISCO>",
            "<ACENTO_AGUDO>",

            "0","1","2","3","4","5","6","7","8","9"
        };

        private List<string> vocab;
        private Dictionary<string, int> stoi;
        private Dictionary<int, string> itos;

        public int PadTokenId { get; private set; }
        public int UnkTokenId { get; private set; }
        public int BosTokenId { get; private set; }
        public int EosTokenId { get; private set; }

        private readonly ConcurrentDictionary<string, int[]> wordCache = new();
        private readonly ConcurrentDictionary<string, string[]> syllableCache = new();

        public bool AllowWholeWordTokens { get; set; } = true;

        // ------------------------
        public SyllableTokenizer(List<string>? initialVocab = null)
        {
            vocab = new List<string>(specialTokens);

            if (initialVocab != null)
                vocab.AddRange(initialVocab);

            RebuildMappings();
        }

        private void RebuildMappings()
        {
            stoi = new(vocab.Count);
            itos = new(vocab.Count);

            for (int i = 0; i < vocab.Count; i++)
            {
                stoi[vocab[i]] = i;
                itos[i] = vocab[i];
            }

            PadTokenId = stoi["<PAD>"];
            UnkTokenId = stoi["<UNK>"];
            BosTokenId = stoi["<BOS>"];
            EosTokenId = stoi["<EOS>"];
        }

        // ------------------------
        // ENCODE
        // ------------------------
        public List<int> Encode(string text)
        {
            var result = new List<int>(text.Length);
            EncodeToStream(text.AsSpan(), result.Add);
            return result;
        }

        public void EncodeToStream(ReadOnlySpan<char> input, Action<int> emit)
        {
            // ✅ EXACTAMENTE como Python (NFKC)
            string normalized = input.ToString().Normalize(NormalizationForm.FormKC);
            var text = normalized.AsSpan();

            emit(BosTokenId);

            Span<char> buffer = stackalloc char[256];
            int len = 0;

            for (int i = 0; i < text.Length; i++)
            {
                char c = text[i];

                // =========================
                // 🔥 STRICT SPECIAL TOKENS
                // =========================
                if (c == '<')
                {
                    FlushWord(buffer, ref len, emit);

                    int j = i + 1;
                    while (j < text.Length && text[j] != '>')
                        j++;

                    if (j < text.Length)
                    {
                        string candidate = text.Slice(i, j - i + 1).ToString();

                        if (stoi.TryGetValue(candidate, out int specialId))
                        {
                            emit(specialId);
                            i = j;
                            continue;
                        }
                    }
                }

                // =========================
                // NORMAL FLOW
                // =========================
                if (!IsValidChar(c))
                {
                    FlushWord(buffer, ref len, emit);
                    if (!char.IsDigit(c))
                        emit(UnkTokenId);
                    continue;
                }

                if (IsWordChar(c) && !char.IsDigit(c))
                {
                    if (len < buffer.Length)
                        buffer[len++] = c;
                    continue;
                }

                FlushWord(buffer, ref len, emit);

                // Dígitos
                if (char.IsDigit(c))
                {
                    emit(stoi[c.ToString()]);
                    continue;
                }

                // Espacios
                if (char.IsWhiteSpace(c))
                {
                    EmitSpecial(c, emit);
                    continue;
                }

                // Puntuación
                if (IsPunctuation(c))
                {
                    EmitSpecial(c, emit);
                    continue;
                }
            }

            FlushWord(buffer, ref len, emit);
            emit(EosTokenId);
        }

        private void FlushWord(Span<char> buffer, ref int len, Action<int> emit)
        {
            if (len == 0) return;
            ProcessWord(buffer[..len], emit);
            len = 0;
        }

        // ------------------------
        // WORD PROCESS
        // ------------------------
        private void ProcessWord(ReadOnlySpan<char> word, Action<int> emit)
        {
            string key = new string(word);

            if (wordCache.TryGetValue(key, out var cached))
            {
                foreach (var t in cached)
                    emit(t);
                return;
            }

            List<int> tokens = new();

            if (AllowWholeWordTokens && stoi.TryGetValue(key, out int tokenId))
            {
                tokens.Add(tokenId);
                emit(tokenId);
            }
            else
            {
                var sylls = syllableCache.GetOrAdd(key, k =>
                {
                    var list = new List<string>();
                    SilabificadorFast.SplitIntoSyllables(k.AsSpan(), s => list.Add(s.ToString()));
                    return list.ToArray();
                });

                foreach (var s in sylls)
                {
                    int sid = stoi.ContainsKey(s) ? stoi[s] : UnkTokenId;
                    tokens.Add(sid);
                    emit(sid);
                }
            }

            wordCache[key] = tokens.ToArray();
        }

        // ------------------------
        // HELPERS
        // ------------------------
        private bool IsWordChar(char c)
        {
            return char.IsLetter(c) || c == '_';
        }

        private bool IsValidChar(char c)
        {
            return char.IsLetterOrDigit(c)
                || char.IsWhiteSpace(c)
                || IsPunctuation(c)
                || c < 256; // ✅ clave
        }

        private bool IsPunctuation(char c)
        {
            return char.IsPunctuation(c) || char.IsSymbol(c) || c == '´';
        }

        private void EmitSpecial(char c, Action<int> emit)
        {
            string? token = c switch
            {
                ' ' => "<SPACE>",
                '\n' => "<NEWLINE>",
                '\t' => "<TAB>",
                ',' => "<COMA>",
                '.' => "<PUNTO>",
                '?' => "<INTERROGACION_CIERRA>",
                '¿' => "<INTERROGACION_ABRE>",
                '!' => "<ADMIRACION_CIERRA>",
                '¡' => "<ADMIRACION_ABRE>",
                ':' => "<DOS_PUNTOS>",
                ';' => "<PUNTO_Y_COMA>",
                '-' => "<GUION>",
                '—' => "<GUION_LARGO>",
                '\'' => "<COMILLA_SIMPLE>",
                '"' => "<COMILLA_DOBLE>",
                '(' => "<PARENTESIS_ABRE>",
                ')' => "<PARENTESIS_CIERRA>",
                '[' => "<CORCHETE_ABRE>",
                ']' => "<CORCHETE_CIERRA>",
                '{' => "<LLAVE_ABRE>",
                '}' => "<LLAVE_CIERRA>",
                '/' => "<SLASH>",
                '\\' => "<BACKSLASH>",
                '=' => "<IGUAL>",
                '<' => "<MENOR>",
                '>' => "<MAYOR>",
                '|' => "<PIPE>",
                '%' => "<PORCENTAJE>",
                '$' => "<DOLAR>",
                '&' => "<AMPERSAND>",
                '^' => "<CIRCUNFLEJO>",
                '~' => "<TILDE>",
                '`' => "<BACKTICK>",
                '°' => "<GRADO>",
                '¬' => "<NEGACION>",
                '*' => "<ASTERISCO>",
                '´' => "<ACENTO_AGUDO>",
                '+' => "<MAS>",
                _ => null
            };

            if (token != null)
                emit(stoi.GetValueOrDefault(token, UnkTokenId));
        }

        // ------------------------
        // DECODE
        // ------------------------
        public string Decode(IEnumerable<int> tokens)
        {
            var sb = new StringBuilder();
            bool lastWasDigit = false;

            foreach (var id in tokens)
            {
                if (!itos.TryGetValue(id, out var tok))
                    continue;

                if (tok.Length == 1 && char.IsDigit(tok[0]))
                {
                    sb.Append(tok);
                    lastWasDigit = true;
                }
                else
                {
                    if (lastWasDigit)
                        lastWasDigit = false;

                    switch (tok)
                    {
                        case "<SPACE>": sb.Append(" "); break;
                        case "<NEWLINE>": sb.Append("\n"); break;
                        case "<TAB>": sb.Append("\t"); break;
                        case "<COMA>": sb.Append(","); break;
                        case "<PUNTO>": sb.Append("."); break;
                        case "<INTERROGACION_CIERRA>": sb.Append("?"); break;
                        case "<INTERROGACION_ABRE>": sb.Append("¿"); break;
                        case "<ADMIRACION_CIERRA>": sb.Append("!"); break;
                        case "<ADMIRACION_ABRE>": sb.Append("¡"); break;
                        case "<DOS_PUNTOS>": sb.Append(":"); break;
                        case "<PUNTO_Y_COMA>": sb.Append(";"); break;
                        case "<GUION>": sb.Append("-"); break;
                        case "<GUION_LARGO>": sb.Append("—"); break;
                        case "<COMILLA_SIMPLE>": sb.Append("'"); break;
                        case "<COMILLA_DOBLE>": sb.Append("\""); break;
                        case "<PARENTESIS_ABRE>": sb.Append("("); break;
                        case "<PARENTESIS_CIERRA>": sb.Append(")"); break;
                        case "<CORCHETE_ABRE>": sb.Append("["); break;
                        case "<CORCHETE_CIERRA>": sb.Append("]"); break;
                        case "<LLAVE_ABRE>": sb.Append("{"); break;
                        case "<LLAVE_CIERRA>": sb.Append("}"); break;
                        case "<SLASH>": sb.Append("/"); break;
                        case "<BACKSLASH>": sb.Append("\\"); break;
                        case "<IGUAL>": sb.Append("="); break;
                        case "<MENOR>": sb.Append("<"); break;
                        case "<MAYOR>": sb.Append(">"); break;
                        case "<PIPE>": sb.Append("|"); break;
                        case "<PORCENTAJE>": sb.Append("%"); break;
                        case "<DOLAR>": sb.Append("$"); break;
                        case "<AMPERSAND>": sb.Append("&"); break;
                        case "<CIRCUNFLEJO>": sb.Append("^"); break;
                        case "<TILDE>": sb.Append("~"); break;
                        case "<BACKTICK>": sb.Append("`"); break;
                        case "<GRADO>": sb.Append("°"); break;
                        case "<NEGACION>": sb.Append("¬"); break;
                        case "<ASTERISCO>": sb.Append("*"); break;
                        case "<ACENTO_AGUDO>": sb.Append("´"); break;
                        case "<MAS>": sb.Append("+"); break;
                        default:
                            if (!tok.StartsWith("<"))
                                sb.Append(tok);
                            break;
                    }
                }
            }

            return sb.ToString();
        }

        // ------------------------
        // SAVE / LOAD
        // ------------------------
        public void SaveVocabHybrid(string path)
        {
            // Diccionario index -> token (C# style)
            var indexedDict = vocab.Select((tok, i) => new { i, tok })
                                   .ToDictionary(x => x.i.ToString(), x => x.tok);

            // Objeto final con keys + lista
            var hybrid = new
            {
                // vocab = vocab,      // Para Python
                indexed = indexedDict  // Para C#
            };

            File.WriteAllText(
                path,
                JsonConvert.SerializeObject(hybrid, Formatting.Indented),
                new UTF8Encoding(false)
            );
        }

        public void LoadVocab(string path)
        {
            var json = File.ReadAllText(path, Encoding.UTF8);
            var data = JsonConvert.DeserializeObject<Dictionary<string, object>>(json);

            if (data.ContainsKey("vocab"))
            {
                // Formato híbrido o Python puro
                var vocabList = data["vocab"] as Newtonsoft.Json.Linq.JArray;
                vocab = vocabList.Select(t => t.ToString()).ToList();
            }
            else if (data.ContainsKey("indexed"))
            {
                // Formato híbrido o C# puro
                var indexedDict = data["indexed"] as Newtonsoft.Json.Linq.JObject;
                vocab = indexedDict.Properties()
                                     .OrderBy(p => int.Parse(p.Name))
                                     .Select(p => p.Value.ToString())
                                     .ToList();
            }
            else if (data.Keys.All(k => int.TryParse(k, out _)))
            {
                // Formato C# puro (solo keys numéricas)
                vocab = data.OrderBy(kv => int.Parse(kv.Key))
                            .Select(kv => kv.Value.ToString())
                            .ToList();
            }
            else
            {
                throw new Exception("Formato de vocab desconocido");
            }

            RebuildMappings();
            wordCache.Clear();
            syllableCache.Clear();
        }

        // ------------------------
        // BUILD VOCAB
        // ------------------------
        public int MaxVocabSize { get; set; } = 200_000;

        public void BuildVocab(IEnumerable<string> texts)
        {
            Console.WriteLine("🔥 Construyendo vocabulario (streaming)...");

            var freq = new Dictionary<string, int>(capacity: 100_000);
            int lineCount = 0;

            foreach (var text in texts)
            {
                if (string.IsNullOrEmpty(text))
                    continue;

                ProcessLineForVocab(text.AsSpan(), freq);
                lineCount++;

                if (lineCount % 100_000 == 0 && freq.Count > MaxVocabSize * 2)
                    TrimFrequency(freq);
            }

            var sorted = freq
                .OrderByDescending(x => x.Value)
                .Take(MaxVocabSize)
                .Select(x => x.Key)
                .ToList();

            vocab = new List<string>(specialTokens);
            vocab.AddRange(sorted);

            RebuildMappings();

            Console.WriteLine($"✅ Vocab final: {vocab.Count:N0}");
        }

        private void ProcessLineForVocab(ReadOnlySpan<char> span, Dictionary<string, int> freq)
        {
            Span<char> buffer = stackalloc char[128];
            int len = 0;

            for (int i = 0; i < span.Length; i++)
            {
                char c = span[i];

                if (!IsValidChar(c))
                    continue;

                if (IsWordChar(c))
                {
                    if (len < buffer.Length)
                        buffer[len++] = c;
                }
                else
                {
                    FlushWordForVocab(buffer, ref len, freq);
                }
            }

            FlushWordForVocab(buffer, ref len, freq);
        }

        private void FlushWordForVocab(Span<char> buffer, ref int len, Dictionary<string, int> freq)
        {
            if (len == 0) return;
            CountWord(buffer[..len], freq);
            len = 0;
        }

        private void CountWord(ReadOnlySpan<char> word, Dictionary<string, int> freq)
        {
            if (word.Length > 64) return;

            string w = new string(word);

            var sylls = syllableCache.GetOrAdd(w, k =>
            {
                var list = new List<string>();
                SilabificadorFast.SplitIntoSyllables(k.AsSpan(), s => list.Add(s.ToString()));
                return list.ToArray();
            });

            foreach (var s in sylls)
            {
                if (s.Length > 32) continue;
                freq[s] = freq.GetValueOrDefault(s) + 1;
            }
        }

        private void TrimFrequency(Dictionary<string, int> freq)
        {
            var trimmed = freq
                .OrderByDescending(x => x.Value)
                .Take(MaxVocabSize)
                .ToDictionary(x => x.Key, x => x.Value);

            freq.Clear();
            foreach (var kv in trimmed)
                freq[kv.Key] = kv.Value;
        }

        public int TokenToId(string token)
        {
            if (stoi.TryGetValue(token, out int id))
                return id;

            return stoi.ContainsKey("<UNK>") ? stoi["<UNK>"] : 0;
        }

        public string IdToToken(int id)
        {
            if (itos.TryGetValue(id, out var token))
                return token;

            return "<UNK>";
        }

        public Dictionary<string, int> GetVocab()
        {
            return new Dictionary<string, int>(stoi);
        }

        public List<string> TokenizeToSyllables(string text)
        {
            var result = new List<string>();
            TokenizeToSyllablesStream(text.AsSpan(), result.Add);
            return result;
        }

        public void TokenizeToSyllablesStream(ReadOnlySpan<char> text, Action<string> emit)
        {
            Span<char> buffer = stackalloc char[256];
            int len = 0;

            for (int i = 0; i < text.Length; i++)
            {
                char c = text[i];

                if (c == '<')
                {
                    FlushWordToSyllables(buffer, ref len, emit);

                    int j = i + 1;
                    while (j < text.Length && text[j] != '>') j++;

                    if (j < text.Length)
                    {
                        var span = text.Slice(i, j - i + 1);
                        string candidate = span.ToString();

                        if (stoi.ContainsKey(candidate))
                        {
                            emit(candidate);
                            i = j;
                            continue;
                        }
                    }
                }

                if (!IsValidChar(c))
                {
                    FlushWordToSyllables(buffer, ref len, emit);
                    continue;
                }

                if (IsWordChar(c) && !char.IsDigit(c))
                {
                    if (len < buffer.Length)
                        buffer[len++] = c;
                    continue;
                }

                FlushWordToSyllables(buffer, ref len, emit);

                if (char.IsDigit(c))
                {
                    emit(c.ToString());
                    continue;
                }

                if (char.IsWhiteSpace(c) || IsPunctuation(c))
                {
                    var token = MapCharToSpecialToken(c);
                    if (token != null)
                        emit(token);
                }
            }

            FlushWordToSyllables(buffer, ref len, emit);
        }

        private void FlushWordToSyllables(Span<char> buffer, ref int len, Action<string> emit)
        {
            if (len == 0) return;

            string word = new string(buffer[..len]);

            var sylls = syllableCache.GetOrAdd(word, k =>
            {
                var list = new List<string>();
                SilabificadorFast.SplitIntoSyllables(k.AsSpan(), s => list.Add(s.ToString()));
                return list.ToArray();
            });

            foreach (var s in sylls)
                emit(s);

            len = 0;
        }

        private string? MapCharToSpecialToken(char c)
        {
            return c switch
            {
                ' ' => "<SPACE>",
                '\n' => "<NEWLINE>",
                '\t' => "<TAB>",
                ',' => "<COMA>",
                '.' => "<PUNTO>",
                '?' => "<INTERROGACION_CIERRA>",
                '¿' => "<INTERROGACION_ABRE>",
                '!' => "<ADMIRACION_CIERRA>",
                '¡' => "<ADMIRACION_ABRE>",
                ':' => "<DOS_PUNTOS>",
                ';' => "<PUNTO_Y_COMA>",
                '-' => "<GUION>",
                '—' => "<GUION_LARGO>",
                _ => null
            };
        }
    }
}