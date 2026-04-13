using System;
using System.Runtime.CompilerServices;

namespace Rudwolf.Utils
{
    public static class SilabificadorFast
    {
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static bool IsVowel(char c)
            => c switch
            {
                'a' or 'e' or 'i' or 'o' or 'u' or
                'á' or 'é' or 'í' or 'ó' or 'ú' or 'ü' => true,
                _ => false
            };

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static bool IsStrong(char c)
            => c is 'a' or 'á' or 'e' or 'é' or 'o' or 'ó';

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static bool IsWeak(char c)
            => c is 'i' or 'í' or 'u' or 'ú' or 'ü';

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static bool HasAccent(char c)
            => c is 'á' or 'é' or 'í' or 'ó' or 'ú';

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static bool IsInseparable(char c1, char c2)
            => (c1, c2) switch
            {
                ('b', 'r') or ('b', 'l') or
                ('c', 'r') or ('c', 'l') or
                ('d', 'r') or
                ('f', 'r') or ('f', 'l') or
                ('g', 'r') or ('g', 'l') or
                ('p', 'r') or ('p', 'l') or
                ('t', 'r') => true,
                _ => false
            };

        // 🔥 CORE: sin listas, sin strings intermedios
        public static void SplitIntoSyllables(
            ReadOnlySpan<char> word,
            Action<ReadOnlySpan<char>> onSyllable)
        {
            int start = 0;

            for (int i = 0; i < word.Length; i++)
            {
                char c = word[i];
                char cLower = char.ToLowerInvariant(c);

                if (!IsVowel(cLower))
                    continue;

                int next = i + 1;

                // Diptongo / hiato
                if (next < word.Length)
                {
                    char v1 = cLower;
                    char v2 = char.ToLowerInvariant(word[next]);

                    if (IsVowel(v2))
                    {
                        bool hiato =
                            (IsStrong(v1) && IsStrong(v2)) ||
                            (IsStrong(v1) && IsWeak(v2) && HasAccent(v2)) ||
                            (IsWeak(v1) && IsStrong(v2) && HasAccent(v1));

                        if (!hiato)
                            i++; // saltar
                    }
                }

                int consonants = 0;
                int j = i + 1;

                while (j < word.Length && !IsVowel(char.ToLowerInvariant(word[j])))
                {
                    consonants++;
                    j++;
                }

                if (consonants == 1)
                {
                    Emit(word, start, i, onSyllable);
                    start = i + 1;
                }
                else if (consonants == 2)
                {
                    char c1 = char.ToLowerInvariant(word[i + 1]);
                    char c2 = char.ToLowerInvariant(word[i + 2]);

                    if (IsInseparable(c1, c2))
                    {
                        Emit(word, start, i, onSyllable);
                        start = i + 1;
                    }
                    else
                    {
                        Emit(word, start, i + 1, onSyllable);
                        start = i + 2;
                        i++;
                    }
                }
                else if (consonants > 2)
                {
                    Emit(word, start, i + 1, onSyllable);
                    start = i + 2;
                    i++;
                }
            }

            if (start < word.Length)
                onSyllable(word[start..]);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static void Emit(
            ReadOnlySpan<char> word,
            int start,
            int end,
            Action<ReadOnlySpan<char>> output)
        {
            output(word.Slice(start, end - start + 1));
        }
    }
}