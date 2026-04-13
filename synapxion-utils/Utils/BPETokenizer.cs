using System;
using System.Buffers;
using System.Collections.Generic;

namespace Rudwolf.Utils
{
    /// <summary>
    /// BPE optimizado sobre INT (token IDs)
    /// - Sin strings
    /// - Sin GC pressure
    /// - ArrayPool
    /// - Listo para datasets grandes
    /// </summary>
    public sealed class BpeTokenizer
    {
        /// <summary>
        /// Regla BPE: (left, right) -> merged
        /// </summary>
        public readonly struct BpeRule
        {
            public readonly int Left;
            public readonly int Right;
            public readonly int Merged;

            public BpeRule(int left, int right, int merged)
            {
                Left = left;
                Right = right;
                Merged = merged;
            }
        }

        private readonly BpeRule[] _rules;

        public BpeTokenizer(IEnumerable<BpeRule>? rules)
        {
            if (rules == null)
            {
                _rules = Array.Empty<BpeRule>();
                return;
            }

            _rules = rules as BpeRule[] ?? new List<BpeRule>(rules).ToArray();
        }

        // =========================
        // 🔹 APPLY (LIST)
        // =========================
        public List<int> Apply(List<int> tokens)
        {
            if (_rules.Length == 0 || tokens.Count == 0)
                return tokens;

            var pool = ArrayPool<int>.Shared;

            int[] current = pool.Rent(tokens.Count);
            int currentLen = tokens.Count;

            for (int i = 0; i < tokens.Count; i++)
                current[i] = tokens[i];

            int[] next = pool.Rent(tokens.Count);

            try
            {
                foreach (var rule in _rules)
                {
                    int write = 0;
                    int read = 0;

                    while (read < currentLen)
                    {
                        if (read < currentLen - 1 &&
                            current[read] == rule.Left &&
                            current[read + 1] == rule.Right)
                        {
                            next[write++] = rule.Merged;
                            read += 2;
                        }
                        else
                        {
                            next[write++] = current[read++];
                        }
                    }

                    // swap buffers
                    var tmp = current;
                    current = next;
                    next = tmp;

                    currentLen = write;
                }

                var result = new List<int>(currentLen);
                for (int i = 0; i < currentLen; i++)
                    result.Add(current[i]);

                return result;
            }
            finally
            {
                pool.Return(current, clearArray: false);
                pool.Return(next, clearArray: false);
            }
        }

        // =========================
        // 🔹 STREAMING (🔥 IMPORTANTE)
        // =========================
        public void ApplyToStream(
            ReadOnlySpan<int> tokens,
            Action<int> emit)
        {
            if (_rules.Length == 0 || tokens.Length == 0)
            {
                for (int i = 0; i < tokens.Length; i++)
                    emit(tokens[i]);
                return;
            }

            var pool = ArrayPool<int>.Shared;

            int[] current = pool.Rent(tokens.Length);
            int currentLen = tokens.Length;

            for (int i = 0; i < tokens.Length; i++)
                current[i] = tokens[i];

            int[] next = pool.Rent(tokens.Length);

            try
            {
                foreach (var rule in _rules)
                {
                    int write = 0;
                    int read = 0;

                    while (read < currentLen)
                    {
                        if (read < currentLen - 1 &&
                            current[read] == rule.Left &&
                            current[read + 1] == rule.Right)
                        {
                            next[write++] = rule.Merged;
                            read += 2;
                        }
                        else
                        {
                            next[write++] = current[read++];
                        }
                    }

                    var tmp = current;
                    current = next;
                    next = tmp;

                    currentLen = write;
                }

                for (int i = 0; i < currentLen; i++)
                    emit(current[i]);
            }
            finally
            {
                pool.Return(current, false);
                pool.Return(next, false);
            }
        }
    }
}