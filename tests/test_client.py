import pytest
from unittest.mock import patch
from seiws.client import SeiClient, InvalidAmbienteError


# Sample response for mocking
mock_response = [{"unit": "Unit1"}, {"unit": "Unit2"}]


@pytest.fixture
def mock_zeep_client():
    with patch("seiws.client.Client") as MockClient:
        mock_client_instance = MockClient.return_value
        mock_client_instance.service.listarUnidades.return_value = mock_response
        yield MockClient


def test_listar_unidades_valid(mock_zeep_client):
    client = SeiClient(ambiente="homologação", chave_api="test_key")
    response = client.listar_unidades(
        id_tipo_procedimento="123", tipo_de_documento="456"
    )
    assert response == mock_response


def test_invalid_ambiente():
    with pytest.raises(InvalidAmbienteError):
        SeiClient(ambiente="invalid")


def test_listar_unidades_exception(mock_zeep_client):
    mock_zeep_client.return_value.service.listarUnidades.side_effect = Exception(
        "SOAP Error"
    )
    client = SeiClient(ambiente="homologação", chave_api="test_key")
    with pytest.raises(Exception):
        client.listar_unidades()


def test_listar_unidades_edge_cases(mock_zeep_client):
    client = SeiClient(ambiente="homologação", chave_api="test_key")

    # Edge case: empty strings
    response = client.listar_unidades(id_tipo_procedimento="", tipo_de_documento="")
    assert response == mock_response

    # Edge case: very long strings
    long_string = "x" * 1000
    response = client.listar_unidades(
        id_tipo_procedimento=long_string, tipo_de_documento=long_string
    )
    assert response == mock_response
