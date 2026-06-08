
import pytest
import typer

from loyverse_sdk.cli._async import run_async
from loyverse_sdk.exceptions import ConfigurationError


class TestRunAsync:
    def test_runs_coroutine_with_client(self):
        received_client = []

        async def _work(client):
            received_client.append(client)

        run_async(_work)
        assert len(received_client) == 1
        assert received_client[0].__class__.__name__ == "LoyverseClient"

    def test_returns_typer_exit_on_config_error(self, mocker):
        mocker.patch(
            "loyverse_sdk.cli._async.LoyverseClient",
            side_effect=ConfigurationError("no token"),
        )

        async def _work(client):
            pass

        with pytest.raises(typer.Exit) as exc:
            run_async(_work)
        assert exc.value.exit_code == 1
