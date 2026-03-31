// Silabificador.cs
using System.Text;

namespace Rudwolf.Utils
{
    public static class Silabificador
    {
        private static readonly HashSet<char> Vowels = new("aeiouáéíóúü".ToCharArray());
        private static readonly HashSet<char> StrongVowels = new("aáeéoó".ToCharArray());
        private static readonly HashSet<char> WeakVowels = new("iíuúü".ToCharArray());

        private static readonly HashSet<string> InseparableGroups = new()
    {
        "br","bl","cr","cl","dr","fr","fl","gr","gl","pr","pl","tr"
    };

        public static bool IsVowel(char c) => Vowels.Contains(c);
        public static bool IsStrong(char c) => StrongVowels.Contains(c);
        public static bool IsWeak(char c) => WeakVowels.Contains(c);
        public static bool HasAccent(char c) => "áéíóú".Contains(c);

        public static List<string> SplitIntoSyllables(string word)
        {
            var syllables = new List<string>();
            var current = new StringBuilder();

            word = word.ToLowerInvariant();
            int i = 0;

            while (i < word.Length)
            {
                current.Append(word[i]);

                if (IsVowel(word[i]))
                {
                    int nextIdx = i + 1;

                    // Detectar hiato / diptongo
                    if (nextIdx < word.Length && IsVowel(word[nextIdx]))
                    {
                        char v1 = word[i];
                        char v2 = word[nextIdx];

                        bool hiato =
                            (IsStrong(v1) && IsStrong(v2)) ||
                            (IsStrong(v1) && IsWeak(v2) && HasAccent(v2)) ||
                            (IsWeak(v1) && IsStrong(v2) && HasAccent(v1));

                        if (!hiato)
                        {
                            // Diptongo → no cortar
                            current.Append(word[nextIdx]);
                            i++;
                        }
                    }

                    // Contar consonantes siguientes
                    int consonantCount = 0;
                    int j = i + 1;

                    while (j < word.Length && !IsVowel(word[j]))
                    {
                        consonantCount++;
                        j++;
                    }

                    if (consonantCount == 1)
                    {
                        syllables.Add(current.ToString());
                        current.Clear();
                    }
                    else if (consonantCount == 2)
                    {
                        string group = word.Substring(i + 1, Math.Min(2, word.Length - (i + 1)));

                        if (InseparableGroups.Contains(group))
                        {
                            syllables.Add(current.ToString());
                            current.Clear();
                        }
                        else
                        {
                            current.Append(word[i + 1]);
                            syllables.Add(current.ToString());
                            current.Clear();
                            i++;
                        }
                    }
                    else if (consonantCount > 2)
                    {
                        current.Append(word[i + 1]);
                        syllables.Add(current.ToString());
                        current.Clear();
                        i++;
                    }
                }

                i++;
            }

            if (current.Length > 0)
                syllables.Add(current.ToString());

            return syllables;
        }

        public static string JoinSyllables(List<string> syllables)
        {
            return syllables == null || syllables.Count == 0
                ? string.Empty
                : string.Concat(syllables);
        }
    }
}
