import typer

from loyverse_sdk.cli.commands.analytics import analytics_app
from loyverse_sdk.cli.commands.create import create_resource
from loyverse_sdk.cli.commands.delete import delete_resource
from loyverse_sdk.cli.commands.endpoints import endpoints
from loyverse_sdk.cli.commands.export_ import export_resources
from loyverse_sdk.cli.commands.get import get_resource
from loyverse_sdk.cli.commands.init import init
from loyverse_sdk.cli.commands.list import list_resources
from loyverse_sdk.cli.commands.update import update_resource

app = typer.Typer(
    name="loyverse",
    help="Loyverse SDK CLI — interact with the Loyverse API",
    no_args_is_help=True,
)

# Setup command
app.command()(init)

# API-related commands (subgroup)
api_app = typer.Typer(
    name="api",
    help="Send API requests to the Loyverse server",
    no_args_is_help=True,
)

api_app.command(
    name="list",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)(list_resources)

api_app.command(
    name="create",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)(create_resource)

api_app.command(
    name="update",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)(update_resource)

api_app.command(name="delete")(delete_resource)

api_app.command(name="get")(get_resource)

api_app.command(name="endpoints")(endpoints)

app.add_typer(api_app)

# Export commands
app.command(name="export")(export_resources)

# Analytics commands
app.add_typer(analytics_app)
