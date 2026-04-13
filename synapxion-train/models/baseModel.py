import torch
import torch.nn as nn

class BaseModel(nn.Module):
    def __init__(self):
        super().__init__()

    # 🔹 Forward: entrenamiento puro
    def forward(self, *args, **kwargs):
        raise NotImplementedError("Forward no implementado")

    # 🔹 Construcción de entrada (prompt + contexto)
    def build_input(
        self,
        prompt=None,
        tokenizer=None,
        memory_context=None,
        system_context=None,
        **kwargs
    ):
        """
        Construye la entrada final que el modelo procesará.
        Cada modelo decide cómo estructurar su contexto.
        """
        raise NotImplementedError("build_input no implementado")

    # 🔹 Generación principal (inferencia)
    def generate(
        self,
        prompt=None,
        input_ids=None,
        tokenizer=None,
        max_new_tokens=50,
        temperature=1.0,
        top_k=0,
        top_p=0.0,
        memory_context=None,
        system_context=None,
        device="cpu",
        **kwargs
    ):
        """
        Método estándar de generación.
        Cada modelo puede sobrescribirlo completamente si lo necesita.
        """
        raise NotImplementedError("generate no implementado")

    # 🔹 Hook opcional: actualización de memoria post-respuesta
    def update_memory(self, memory_manager, input_text, output_text):
        """
        Permite que el modelo sugiera cambios en memoria.
        (Monrix decidirá si acepta o no)
        """
        pass