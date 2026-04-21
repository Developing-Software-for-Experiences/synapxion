using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

public class OllamaService
{
    private readonly HttpClient _http;

    public OllamaService()
    {
        _http = new HttpClient
        {
            BaseAddress = new Uri("http://localhost:11434")
        };
    }

    public async Task<string> EnviarMensajeAsync(string mensajeUsuario)
    {
        try
        {
            var requestBody = new
            {
                model = "llama3", // puedes cambiarlo (mistral, phi3, etc.)
                prompt = mensajeUsuario,
                stream = false
            };

            string json = JsonSerializer.Serialize(requestBody);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await _http.PostAsync("/api/generate", content);
            response.EnsureSuccessStatusCode();

            string responseJson = await response.Content.ReadAsStringAsync();

            using var doc = JsonDocument.Parse(responseJson);
            string result = doc.RootElement.GetProperty("response").GetString();

            return result ?? "";
        }
        catch (Exception ex)
        {
            return $"Error: {ex.Message}";
        }
    }
}