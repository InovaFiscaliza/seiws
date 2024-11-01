from typing_extensions import Annotated, Self
from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator
from typing import Optional

EXTENSOES = [
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".rtf",
    ".html",
    ".htm",
    ".xml",
    ".zip",
    ".rar",
    ".7z",
    ".pdf",
    ".odt",
    ".ods",
    ".ott",
    ".csv",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".rtf",
    ".html",
    ".htm",
    ".xml",
    ".zip",
    ".rar",
    ".7z",
    ".pdf",
    ".odt",
    ".ods",
    ".ott",
    ".csv",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".rtf",
    ".html",
    ".htm",
    ".xml",
    ".zip",
    ".rar",
    ".7z",
]


class Documento(BaseModel):
    """Representa a estrutura Documento do SEI Web Service 4.1.

    Attributes:
        Tipo: Tipo do documento.
            G = documento gerado
            R = documento recebido (externo)
        IdProcedimento: Identificador do processo onde o documento deve ser inserido.
            Opcional se ProtocoloProcedimento for informado.
            Passar null quando na mesma operação estiver sendo gerado o processo.
        ProtocoloProcedimento: Número do processo onde o documento deve ser inserido.
            Visível para o usuário, ex: 12.1.000000077-4.
            Opcional se IdProcedimento informado.
        IdSerie: Identificador da série do documento.
        Numero: Número do documento.
            Para documentos gerados com numeração informada passar o número.
            Passar null para documentos gerados com numeração controlada pelo SEI.
            Para documentos externos informar o número (o SEI não controla numeração de documentos externos).
        NomeArvore: Nome complementar a ser exibido na árvore de documentos do processo.
        DinValor:  Valor monetário
            ex: 133.050,95 ou 133050,95
        Data: Data do documento.
            Obrigatório para documentos externos. ex: 01/01/20221
            Passar null para documentos gerados
        Descricao: Descrição do documento.
        Conteudo: Conteúdo do documento em base64.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    Tipo: Annotated[str, StringConstraints(pattern="^(R|G)$")]
    IdProcedimento: Optional[str] = None
    ProtocoloProcedimento: Optional[str] = None
    IdSerie: str
    Numero: Optional[str] = None
    NomeArvore: Optional[str] = None
    DinValor: Optional[str] = None
    Descricao: str
    Conteudo: str

    def __getitem__(self, key):
        return getattr(self, key)

    @model_validator(mode="after")
    def check_protocolo_or_id(self) -> Self:
        """
        Valida se ProtocoloProcedimento ou IdProcedimento foi fornecido.

        Raises:
            ValueError: Se nem ProtocoloProcedimento nem IdProcedimento foram fornecidos.
        """
        protocolo = self.ProtocoloProcedimento
        id_procedimento = self.IdProcedimento
        if not (protocolo or id_procedimento):
            raise ValueError(
                "ProtocoloProcedimento ou IdProcedimento deve ser fornecido."
            )
        return self


if __name__ == "__main__":
    import os
    from pathlib import Path
    import base64

    html_bytes = Path("C:/Users/rsilva/Code/Oficio.html").read_bytes()
    html_base64 = base64.b64encode(html_bytes).decode("utf-8")
    # Example usage
    documento_data = {
        "Tipo": "G",
        "ProtocoloProcedimento": "53500.000124/2024-04",
        "IdSerie": "11",
        "Numero": None,
        "Descricao": "Documento de Teste - InovaFiscaliza",
        "Conteudo": html_base64,  # Replace with actual base64 content
    }

    try:
        documento = Documento(**documento_data)
        print(documento)
    except Exception as e:
        print(f"Validation error: {e}")
