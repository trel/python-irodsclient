#!/usr/bin/env python3

import click
import json
import os
import ssl
import sys
from click_aliases import ClickAliasedGroup
from irods.session import iRODSSession
import irods.exception
from irods.path import iRODSPath


def get_irods_cwd_file():
    short_cwdfile = "~/.irods/.irods_environment.json.{}".format(os.getppid())
    cwdfile = os.path.expanduser(short_cwdfile)
    return cwdfile


def get_full_logical_path(session, logical_path):
    if logical_path.startswith("/"):
        full_logical_path = logical_path
    else:
        full_logical_path = iRODSPath(
            "{}/{}".format(get_irods_pwd(session), logical_path)
        )
    return full_logical_path


def get_irods_session():
    try:
        env_file = os.environ["IRODS_ENVIRONMENT_FILE"]
    except KeyError:
        env_file = os.path.expanduser("~/.irods/irods_environment.json")
    ssl_settings = {}
    session = iRODSSession(irods_env_file=env_file, **ssl_settings)
    return session


def get_irods_home_collection(session):
    return iRODSPath("/{}/home/{}".format(session.zone, session.username))


def get_irods_pwd(session):
    try:
        with open(get_irods_cwd_file(), "r") as f:
            data = json.loads(f.read())
        # uses irods_cwd (same as iCommands)
        if data["irods_cwd"]:
            pwd = data["irods_cwd"]
        else:
            pwd = get_irods_home_collection(session)
    except json.decoder.JSONDecodeError as e:
        pwd = get_irods_home_collection(session)
    except FileNotFoundError as e:
        pwd = get_irods_home_collection(session)
    return pwd


######################################################################

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
PARAM_DECLS_VERSION = ("-v", "--version")


@click.group(context_settings=CONTEXT_SETTINGS, cls=ClickAliasedGroup)
@click.version_option(irods.__version__, *PARAM_DECLS_VERSION)
def cli():
    """The iRODS CLI"""
    pass


######################################################################


@cli.group(cls=ClickAliasedGroup, aliases=["d"])
def data():
    """The data operations"""
    pass


@data.command()
def calculate_checksum():
    pass


@data.command()
@click.argument("collection", required=False)
def cd(collection):
    """Changes present working directory/collection."""
    session = get_irods_session()
    try:
        irods_cwd_file = get_irods_cwd_file()
        if not collection:
            # remove irods_cwd file
            try:
                os.remove(irods_cwd_file)
            except OSError:
                pass
            sys.exit(0)
        # resolve full collection path
        logical_path = get_full_logical_path(session, collection)
        # if the logical_path exists, save it
        if session.collections.exists(logical_path):
            # save the collection to irods_cwd
            with open(irods_cwd_file, "w") as f:
                f.write(json.dumps({"irods_cwd": logical_path}))
        else:
            click.echo("No such collection: {}".format(logical_path))
            sys.exit(1)

    except (irods.exception.iRODSException, irods.exception.NetworkException) as e:
        print(e)
        sys.exit(1)


@data.command(aliases=["cp"])
def copy():
    pass


@data.command(aliases=["ls"])
@click.argument("logical_path", required=False)
@click.option("-v", "--verbose", is_flag=True, help="Show IDs")
@click.option("--acls", is_flag=True, help="Show ACLs")
@click.option("--metadata", is_flag=True, help="Show metadata (AVUs)")
@click.option("--replicas", is_flag=True, help="Show replica information")
def list(logical_path, verbose, acls, metadata, replicas):
    """List information in a collection or about a data object."""
    session = get_irods_session()

    if not logical_path:
        logical_path = get_irods_pwd(session)
    logical_path = get_full_logical_path(session, logical_path)
    try:
        # subcollections
        if session.collections.exists(logical_path):
            output = {"collections": {}, "data_objects": {}}
            for x in session.collections.get(logical_path).subcollections:
                if verbose:
                    output["collections"].update({x.name: {"id": x.id}})
                else:
                    output["collections"].update({x.name: {}})
                if acls:
                    acls = []
                    for a in session.acls.get(x):
                        acls.append(
                            {
                                "access_name": a.access_name,
                                "user_name": a.user_name,
                                "user_zone": a.user_zone,
                            }
                        )
                        output["collections"][x.name]["acls"] = acls
                if metadata:
                    avus = []
                    for a in x.metadata.items():
                        avus.append(
                            {
                                "attribute": a.name,
                                "value": a.value,
                                "unit": a.units,
                            }
                        )
                        output["collections"][x.name]["metadata"] = avus

        # data object(s)
        if session.collections.exists(logical_path):
            data_objects = session.collections.get(logical_path).data_objects
        elif session.data_objects.exists(logical_path):
            output = {"data_objects": {}}
            data_objects = [session.data_objects.get(logical_path)]
        else:
            print("bad logical path")
            sys.exit(1)
        for x in data_objects:
            if verbose:
                output["data_objects"].update({x.name: {"size": x.size, "id": x.id}})
            else:
                output["data_objects"].update({x.name: {"size": x.size}})
            if acls:
                acls = []
                for a in session.acls.get(x):
                    acls.append(
                        {
                            "access_name": a.access_name,
                            "user_name": a.user_name,
                            "user_zone": a.user_zone,
                        }
                    )
                    output["data_objects"][x.name]["acls"] = acls
            if metadata:
                avus = []
                for a in x.metadata.items():
                    avus.append(
                        {
                            "attribute": a.name,
                            "value": a.value,
                            "unit": a.units,
                        }
                    )
                    output["data_objects"][x.name]["metadata"] = avus
            if replicas:
                reps = []
                for r in x.replicas:
                    reps.append(
                        {
                            "number": r.number,
                            "status": r.status,
                            "size": r.size,
                            "physical_path": r.path,
                            "resc_hier": r.resc_hier,
                            "resource_name": r.resource_name,
                            "modify_time": str(r.modify_time),
                            "create_time": str(r.create_time),
                            "checksum": r.checksum,
                        }
                    )
                output["data_objects"][x.name]["replicas"] = reps
    except (irods.exception.iRODSException, irods.exception.NetworkException) as e:
        print(e)
        sys.exit(1)
    click.echo(json.dumps(output))


@data.command()
def mkdir():
    pass


@data.command()
def modify_metadata():
    pass


@data.command()
def modify_permissions():
    pass


@data.command()
def modify_replica():
    pass


@data.command()
def pwd():
    """Displays present working directory/collection."""
    session = get_irods_session()
    pwd = get_irods_pwd(session)
    click.echo(pwd)


@data.command(aliases=["get"])
def read():
    pass


@data.command()
def register():
    pass


@data.command(aliases=["rm"])
@click.argument("logical_path")
@click.option("-r", "--recursive", is_flag=True, help="Remove collections recursively")
@click.option("-f", "--force", is_flag=True, help="Delete, and skip the trash")
def remove(logical_path, recursive, force):
    """Removes a data object or collection."""
    session = get_irods_session()
    logical_path = get_full_logical_path(session, logical_path)
    options = {}
    if force:
        options["force"] = force
    try:
        if session.collections.exists(logical_path):
            # collection
            options["recurse"] = recursive
            session.collections.remove(logical_path, **options)
        else:
            # data object
            session.data_objects.unlink(logical_path, **options)
    except (irods.exception.iRODSException, irods.exception.NetworkException) as e:
        print(e)
        sys.exit(1)


@data.command(aliases=["move", "mv"])
@click.argument("source")
@click.argument("destination")
def rename(source, destination):
    """Renames a data object or collection."""
    session = get_irods_session()
    source = get_full_logical_path(session, source)
    destination = get_full_logical_path(session, destination)
    try:
        if session.collections.exists(source):
            # collection
            session.collections.move(source, destination)
        else:
            # data object
            session.data_objects.move(source, destination)

    except (irods.exception.iRODSException, irods.exception.NetworkException) as e:
        print(e)
        sys.exit(1)


@data.command(aliases=["repl"])
def replicate():
    pass


@data.command()
def set_inheritance():
    pass


@data.command()
def set_permission():
    pass


@data.command()
def sync():
    pass


@data.command()
def tree():
    pass


@data.command()
def unregister():
    pass


@data.command()
@click.argument("logical_path")
@click.option(
    "--seconds-since-epoch",
    type=int,
    help='The number of seconds since epoch representing the new mtime. Cannot be used with "--reference".',
)
@click.option(
    "--reference",
    help='Use the mtime of the logical path to the data object or collection identified by this option. Cannot be used with "--seconds-since-epoch".',
)
@click.option(
    "--leaf-resource-name",
    help='The name of the leaf resource containing the replica to update. If the object identified by the "logical_path" parameter does not exist and this parameter holds a valid resource, the data object will be created at the specified resource. Cannot be used with "--replica-number".',
)
@click.option(
    "--replica-number",
    type=int,
    help='The replica number of the replica to update. Replica numbers cannot be used to create data objects or additional replicas. Cannot be used with "--leaf-resource-name".',
)
def touch(
    logical_path, seconds_since_epoch, reference, leaf_resource_name, replica_number
):
    """Updates the mtime of a data object or collection."""
    if reference and seconds_since_epoch:
        click.echo("--seconds-since-epoch and --reference are mutually exclusive.")
        sys.exit(1)
    if leaf_resource_name and (replica_number or replica_number == 0):
        click.echo("--leaf-resource-name and --replica-number are mutually exclusive.")
        sys.exit(1)
    session = get_irods_session()
    logical_path = get_full_logical_path(session, logical_path)
    options = {}
    if reference:
        reference = get_full_logical_path(session, reference)
        options["reference"] = reference
    if seconds_since_epoch:
        options["seconds_since_epoch"] = seconds_since_epoch
    if leaf_resource_name:
        options["leaf_resource_name"] = leaf_resource_name
    if replica_number or replica_number == 0:
        options["replica_number"] = replica_number
    try:
        if session.collections.exists(logical_path):
            # collection
            session.collections.touch(
                logical_path,
                **options,
            )
        else:
            # data object
            session.data_objects.touch(
                logical_path,
                **options,
            )
    except (irods.exception.iRODSException, irods.exception.NetworkException) as e:
        print(e)
        sys.exit(1)


@data.command()
def trim():
    pass


@data.command()
def verify_checksum():
    pass


@data.command(aliases=["put"])
def write():
    pass


######################################################################


@cli.group(cls=ClickAliasedGroup, aliases=["g"])
def group():
    """The group operations"""
    pass


@group.command()
def create():
    pass


@group.command()
def list():
    pass


@group.command()
def modify_metadata():
    pass


@group.command(aliases=["delete", "rm"])
def remove():
    pass


######################################################################


@cli.group(cls=ClickAliasedGroup, aliases=["q"])
def query():
    """The query operations"""
    pass


@query.command(aliases=["asq"])
def add_specific_query():
    pass


@query.command()
@click.argument("querystring")
@click.option(
    "--sql-only",
    is_flag=True,
    help="Print the SQL generated by the parser. The generated SQL will not be executed.",
)
@click.option(
    "-z",
    "--zone",
    help="The name of the zone to run the query against. Defaults to the local zone.",
)
def execute_general_query(querystring, sql_only, zone):
    """Query the iRODS Catalog using GenQuery2"""
    session = get_irods_session()
    if zone is None:
        # default is the local zone
        zone = session.zone
    try:
        if sql_only:
            q = session.genquery2_object()
            result = q.get_sql(querystring, zone=zone)
        else:
            q = session.genquery2_object()
            result = q.execute(querystring, zone=zone)
    except irods.exception.SYS_INVALID_INPUT_PARAM as e:
        print("ERROR: irods.exception.SYS_INVALID_INPUT_PARAM")
        sys.exit(1)
    except irods.exception.SYS_LIBRARY_ERROR as e:
        print("bad querystring")
        sys.exit(1)
    except (irods.exception.iRODSException, irods.exception.NetworkException) as e:
        print(e)
        sys.exit(1)
    click.echo(json.dumps(result))


@query.command()
def execute_specific_query():
    pass


@query.command()
@click.option(
    "-z",
    "--zone",
    help="The name of the zone to run the query against. Defaults to the local zone.",
)
def list_columns(zone):
    """List columns supported by GenQuery2"""
    session = get_irods_session()
    if zone is None:
        # default is the local zone
        zone = session.zone
    try:
        q = session.genquery2_object()
        result = q.get_column_mappings()
    except (irods.exception.iRODSException, irods.exception.NetworkException) as e:
        print(e)
        sys.exit(1)
    #    click.echo(dir(self))
    click.echo(json.dumps(result))


@query.command(aliases=["rsq"])
def remove_specific_query():
    pass


######################################################################


@cli.group(cls=ClickAliasedGroup, aliases=["re"])
def resource():
    """The resource operations"""
    pass


@resource.command()
def add_child():
    pass


@resource.command()
def create():
    pass


@resource.command()
def list():
    pass


@resource.command()
def modify():
    pass


@resource.command()
def modify_metadata():
    pass


@resource.command()
def rebalance():
    pass


@resource.command()
def remove():
    pass


@resource.command()
def remove_child():
    pass


######################################################################


@cli.group(cls=ClickAliasedGroup, aliases=["ru"])
def rule():
    """The rule operations"""
    pass


@rule.command()
def execute():
    pass


@rule.command()
def list_delay_rules():
    pass


@rule.command()
def list_rule_engines():
    pass


@rule.command()
def remove_delay_rule():
    pass


######################################################################


@cli.group(cls=ClickAliasedGroup, aliases=["t"])
def ticket():
    """The ticket operations"""
    pass


@ticket.command()
def create():
    pass


@ticket.command()
def list():
    pass


@ticket.command()
def modify():
    pass


@ticket.command()
def remove():
    pass


######################################################################


@cli.group(cls=ClickAliasedGroup, aliases=["u"])
def user():
    """The user operations"""
    pass


@user.command()
def add_to_group():
    pass


@user.command()
def authenticate():
    pass


@user.command()
def create():
    pass


@user.command()
def is_member_of_group():
    pass


@user.command()
def list():
    pass


@user.command()
def modify_metadata():
    pass


@user.command()
def remove():
    pass


@user.command()
def remove_from_group():
    pass


@user.command()
def set_password():
    pass


@user.command()
def set_user_type():
    pass


######################################################################


@cli.group(cls=ClickAliasedGroup, aliases=["z"])
def zone():
    """The zone operations"""
    pass


@zone.command()
def create():
    pass


@zone.command()
def get_grid_configuration():
    pass


@zone.command()
def list():
    pass


@zone.command()
def modify():
    pass


@zone.command()
def remove():
    pass


@zone.command()
def report():
    pass


@zone.command()
def set_grid_configuration():
    pass


######################################################################


def the_cli():
    cli()


if __name__ == "__main__":
    the_cli()
