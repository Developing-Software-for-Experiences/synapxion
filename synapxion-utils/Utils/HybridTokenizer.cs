using System;
using System.Collections.Generic;
using System.Text;

namespace Rudwolf.Utils
{
    public class HybridTokenizer : ITokenizer
    {
        private readonly SyllableTokenizer _syllable;
        private readonly BpeTokenizer _bpe;

        private readonly Dictionary<string, int> _tokenToId;
        private readonly Dictionary<int, string> _idToToken;

        public int PadTokenId { get; }
        public int BosTokenId { get; }
        public int EosTokenId { get; }
        public int UnkTokenId { get; }

        public HybridTokenizer(
            SyllableTokenizer syllableTokenizer,
            BpeTokenizer bpeTokenizer,
            Dictionary<string, int> vocab)
        {
            _syllable = syllableTokenizer;
            _bpe = bpeTokenizer;

            _tokenToId = vocab;
            _idToToken = new Dictionary<int, string>();

            foreach (var kv in vocab)
                _idToToken[kv.Value] = kv.Key;

            PadTokenId = _tokenToId["<PAD>"];
            BosTokenId = _tokenToId["<BOS>"];
            EosTokenId = _tokenToId["<EOS>"];
            UnkTokenId = _tokenToId["<UNK>"];
        }

        // =========================
        // 🔹 ENCODE
        // =========================
        public List<int> Encode(string text)
        {
            var result = new List<int>(128);
            EncodeToStream(text.AsSpan(), result.Add);
            return result;
        }

        // =========================
        // 🔹 STREAMING (CLAVE)
        // =========================
        public void EncodeToStream(ReadOnlySpan<char> text, Action<int> emit)
        {
            emit(BosTokenId);

            var buffer = new List<int>(32);

            void Flush()
            {
                if (buffer.Count == 0)
                    return;

                var merged = _bpe.Apply(buffer);

                foreach (var t in merged)
                    emit(t);

                buffer.Clear();
            }

            void HandleToken(int tid)
            {
                var tok = _syllable.IdToToken(tid);

                if (tok.StartsWith("<") && tok.EndsWith(">"))
                {
                    Flush();
                    emit(_tokenToId.TryGetValue(tok, out var id) ? id : UnkTokenId);
                    return;
                }

                buffer.Add(tid);

                if (buffer.Count >= 32)
                    Flush();
            }

            _syllable.EncodeToStream(text, HandleToken);

            Flush();
            emit(EosTokenId);
        }

        // =========================
        // 🔹 DECODE
        // =========================
        public string Decode(IEnumerable<int> tokens)
        {
            var sb = new StringBuilder();

            foreach (var id in tokens)
            {
                if (id == BosTokenId || id == EosTokenId || id == PadTokenId)
                    continue;

                if (_idToToken.TryGetValue(id, out var tok))
                {
                    switch (tok)
                    {
                        case "<SPACE>": sb.Append(" "); break;
                        case "<NEWLINE>": sb.Append("\n"); break;
                        case "<TAB>": sb.Append("\t"); break;
                        default:
                            if (!tok.StartsWith("<"))
                                sb.Append(tok);
                            break;
                    }
                }
            }

            return sb.ToString();
        }

        public int TokenToId(string token)
        {
            return _tokenToId.TryGetValue(token, out var id) ? id : UnkTokenId;
        }
    }
}