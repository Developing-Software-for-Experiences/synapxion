// ITokenizer.cs
namespace Rudwolf.Utils
{
    public interface ITokenizer
    {
        List<int> Encode(string text);
        string Decode(IEnumerable<int> tokens);

        int PadTokenId { get; }
        int BosTokenId { get; }
        int EosTokenId { get; }
    }
}
