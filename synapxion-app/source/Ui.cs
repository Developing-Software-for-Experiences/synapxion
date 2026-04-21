using Godot;
using System;

public partial class Ui : Control
{
    [Export] public TextEdit usrInput;
    [Export] public Button btnEnviar;

    private OllamaService _ollama;

    public override void _Ready()
    {
        _ollama = new OllamaService();
        btnEnviar.Pressed += OnEnviarPressed;
    }

    private async void OnEnviarPressed()
    {
        string texto = usrInput.Text.Trim();

        if (string.IsNullOrEmpty(texto))
            return;

        btnEnviar.Disabled = true;

        string respuesta = await _ollama.EnviarMensajeAsync(texto);

        GD.Print(respuesta);

        btnEnviar.Disabled = false;
        usrInput.Clear();
    }
}