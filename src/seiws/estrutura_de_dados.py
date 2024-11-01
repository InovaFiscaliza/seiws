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
    """
    Essa classe representa a estrutura Documento do Sei Web Service 4.1

    Attributes:
        Tipo (str): G = documento gerado | R = documento recebido (externo) .
        ProtocoloProcedimento (Optional[str]): Número do processo onde o documento deve ser inserido, visível para o usuário,
                                               ex: 12.1.000000077-4. Opcional se IdProcedimento informado.
        IdProcedimento (Optional[str]):  Identificador do processo onde o documento deve ser inserido, passar null
                                         quando na mesma operação estiver sendo gerado o processo. Opcional se
                                         ProtocoloProcedimento for informado .
        IdSerie (str): The series ID of the document.
        Numero (Optional[str]): Número do documento. Para documentos gerados com numeração informada passar o número.
                                Passar null para documentos gerados com numeração controlada pelo SEI.
                                Para documentos externos informar o número (o SEI não controla numeração de documentos externos) .
        NomeArvore: (Optional[str]): Nome complementar a ser exibido na árvore de documentos do processo
        Descricao (str): A description of the document.
        Conteudo (str): The base64 encoded content of the document.
    """

    Tipo: Annotated[str, StringConstraints(pattern="^(R|G)$")]
    IdSerie: str
    Descricao: str
    Conteudo: str
    ProtocoloProcedimento: Optional[str] = None
    IdProcedimento: Optional[str] = None
    Numero: Optional[str] = None
    NomeArvore: Optional[str] = None

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
