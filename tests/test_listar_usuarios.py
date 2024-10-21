import os

import pytest
from seiws.client import SeiClient
from tests.constants import UNIDADES_BLOQUEIO, USUARIOS


class TestListarUsuarios:
    @pytest.mark.parametrize("id_unidade", [d["IdUnidade"] for d in UNIDADES_BLOQUEIO])
    def test_listar_usuarios_hm_bloqueio(self, id_unidade):
        client = SeiClient(
            sigla_sistema=os.getenv("SIGLA_SISTEMA"),
            chave_api=os.getenv("SEI_HM_API_KEY_BLOQUEIO"),
        )
        usuarios = client.listar_usuarios(id_unidade=id_unidade)
        assert isinstance(usuarios, list)
        assert set(usuario["IdUsuario"] for usuario in usuarios).issubset(
            usuario["IdUsuario"] for usuario in USUARIOS
        )
