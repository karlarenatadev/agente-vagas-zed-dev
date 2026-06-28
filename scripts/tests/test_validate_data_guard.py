from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "validate_data_guard.py"


class DataGuardCliTests(unittest.TestCase):
    def run_guard(self, files: dict[str, str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            subprocess.run(
                ["git", "init", "-q"],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for relative_path, content in files.items():
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            subprocess.run(
                ["git", "add", "-f", "--", "."],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return subprocess.run(
                [sys.executable, str(SCRIPT), "--repo-root", str(root)],
                cwd=root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

    def assert_blocked(
        self,
        files: dict[str, str],
        expected_path: str,
    ) -> str:
        result = self.run_guard(files)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(expected_path, result.stdout)
        return result.stdout

    def test_permite_readme_exemplo_sanitizado_e_arquivo_normal(self):
        result = self.run_guard(
            {
                "data/README.md": "# Dados locais\n",
                "data/perfil.example.md": "Nome: Pessoa Exemplo\nToken: [redacted]\n",
                "backend/.env.example": "OPENAI_API_KEY=replace-with-openai-api-key\n",
                "docs/info.md": "API keys devem vir de variaveis de ambiente.\n",
            }
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Data Guard: OK", result.stdout)

    def test_bloqueia_qualquer_arquivo_em_data_sessions(self):
        output = self.assert_blocked(
            {
                "data/README.md": "# Dados\n",
                "data/sessions/exemplo/user-profile.md": "Nome: Pessoa Real\n",
            },
            "data/sessions/exemplo/user-profile.md",
        )

        self.assertIn("data/sessions/", output)

    def test_bloqueia_arquivo_real_fora_da_allowlist_de_data(self):
        output = self.assert_blocked(
            {"data/arquivo-real.md": "Nome: Pessoa Real\n"},
            "data/arquivo-real.md",
        )

        self.assertIn("fora da allowlist", output)

    def test_bloqueia_env_e_variacoes_perigosas(self):
        for path in (
            ".env",
            ".env.local",
            "backend/settings.env",
            "backend/settings.env.local",
            ".envrc",
        ):
            with self.subTest(path=path):
                output = self.assert_blocked(
                    {path: "MODE=local\n"},
                    path,
                )
                self.assertIn("arquivo de ambiente", output)

    def test_bloqueia_atribuicao_de_api_key_em_texto_claro(self):
        secret = "live_" + ("A" * 32)
        output = self.assert_blocked(
            {"config.txt": f"SERVICE_API_KEY={secret}\n"},
            "config.txt",
        )

        self.assertIn("credencial em texto claro", output)

    def test_bloqueia_segredo_dentro_de_example_que_deveria_ser_sanitizado(self):
        secret = "live_" + ("C" * 32)
        output = self.assert_blocked(
            {"data/perfil.example.md": f"API_KEY={secret}\n"},
            "data/perfil.example.md",
        )

        self.assertIn("credencial em texto claro", output)

    def test_bloqueia_bearer_token_e_aponta_arquivo(self):
        token = "B" * 32
        output = self.assert_blocked(
            {"docs/credencial.txt": f"Authorization: Bearer {token}\n"},
            "docs/credencial.txt",
        )

        self.assertIn("bearer token", output)
        self.assertIn("linha 1", output)

    def test_bloqueia_private_key(self):
        private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
        output = self.assert_blocked(
            {"certs/private.pem": f"{private_key_marker}\nconteudo\n"},
            "certs/private.pem",
        )

        self.assertIn("chave privada", output)


if __name__ == "__main__":
    unittest.main()
