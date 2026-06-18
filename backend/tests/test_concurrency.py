import asyncio
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient, Response

import config
from main import app


@pytest.mark.asyncio
async def test_concurrent_writes_to_applications(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        async def make_request(index: int) -> Response:
            return await client.post(
                "/api/applications/",
                json={
                    "titulo": f"Vaga {index}",
                    "empresa": "Empresa Teste",
                    "localizacao": "Remoto",
                    "link": f"https://example.com/vagas/{index}",
                    "status": "aplicada",
                },
                headers={"X-Session-Id": "sessao_de_teste_123"},
            )

        responses = await asyncio.gather(*(make_request(index) for index in range(50)))

    errors = [response.text for response in responses if response.status_code not in {200, 201}]
    assert not errors, f"Falhas encontradas no stress test: {errors[:3]}"
