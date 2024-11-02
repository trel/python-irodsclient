import unittest
from click.testing import CliRunner
from irods.irods_cli import cli
import time


class TestCLI(unittest.TestCase):

    def print_result(self, result):
        print("-------")
        assert result.stdout == result.output
        print("result.stdout", "[{}]".format(result.stdout))
        print("result.return_value", result.return_value)
        print("result.exit_code", result.exit_code)
        print("result.exc_info", result.exc_info)
        print("result.exception", result.exception)
        print("-------")

    def test_query_execute_general_query_bad_querystring(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["query", "execute-general-query", "nopes"])
        assert result.return_value is None
        assert (
            result.output.strip() == "bad querystring"
        )  # genquery2 issue https://github.com/irods/irods/issues/8094
        assert result.exit_code == 1

    def test_query_execute_general_query_list_columns(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["query", "list-columns"])
        # self.print_result(result)
        assert result.return_value is None
        assert '"USER_ID": {"R_USER_MAIN": "user_id"}' in result.stdout
        assert result.exit_code == 0

    def test_query_execute_general_query_sql_only(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, ["query", "execute-general-query", "--sql-only", "select USER_NAME"]
        )
        #        self.print_result(result)
        assert result.return_value is None
        assert (
            result.output.strip()
            == '"select distinct t0.user_name from R_USER_MAIN t0 fetch first 256 rows only"'
        )
        assert result.exit_code == 0

    def test_query_execute_general_query(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, ["query", "execute-general-query", "select USER_NAME"]
        )
        #        self.print_result(result)
        assert "rods" in result.output
        assert result.exit_code == 0
        result = runner.invoke(
            cli, ["query", "execute-general-query", "select bad_column"]
        )
        #        self.print_result(result)
        assert result.output.strip() == "ERROR: irods.exception.SYS_INVALID_INPUT_PARAM"
        assert result.exit_code == 1

    def test_data_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["data", "list"])
        assert "collection" in result.output
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "list", "nopes"])
        assert "bad logical path" in result.output
        assert result.exit_code == 1
        result = runner.invoke(cli, ["data", "list", "sample.json"])
        assert "size" in result.output
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "list", "-v"])
        #        self.print_result(result)
        assert "id" in result.output
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "list", "--acls"])
        #        self.print_result(result)
        assert "access_name" in result.output
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "list", "--replicas"])
        #        self.print_result(result)
        assert "physical_path" in result.output
        assert result.exit_code == 0

    def test_data_touch(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["data", "touch", "/tempZone/home/rods/newfile"])
        assert result.output.strip() == ""
        assert result.exit_code == 0
        time.sleep(1.1)
        result = runner.invoke(cli, ["data", "touch", "newfile"])
        assert result.output.strip() == ""
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "touch", "/tempZone/home/rods/one"])
        assert result.output.strip() == ""
        assert result.exit_code == 0
        time.sleep(1.1)
        result = runner.invoke(cli, ["data", "touch", "one"])
        assert result.output.strip() == ""
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "touch", "/notallowed"])
        #        self.print_result(result)
        assert "SYS_INVALID_ZONE_NAME" in result.output
        assert result.exit_code == 1
        result = runner.invoke(cli, ["data", "touch", "/tempZone/nopes/nopes/nopes"])
        #        self.print_result(result)
        assert "collection '/tempZone/nopes/nopes' is unknown" in result.output
        assert result.exit_code == 1
        result = runner.invoke(
            cli,
            [
                "data",
                "touch",
                "one",
                "--reference",
                "newfile",
                "--seconds-since-epoch",
                4,
            ],
        )
        assert (
            result.output.strip()
            == "--seconds-since-epoch and --reference are mutually exclusive."
        )
        assert result.exit_code == 1
        result = runner.invoke(
            cli,
            [
                "data",
                "touch",
                "newfile",
                "--leaf-resource-name",
                "one",
                "--replica-number",
                0,
            ],
        )
        assert (
            result.output.strip()
            == "--leaf-resource-name and --replica-number are mutually exclusive."
        )
        assert result.exit_code == 1
        result = runner.invoke(
            cli, ["data", "touch", "newfile", "--seconds-since-epoch", "345"]
        )
        assert result.output.strip() == ""
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "touch", "newfile", "--reference", "one"])
        assert result.output.strip() == ""
        assert result.exit_code == 0
        result = runner.invoke(
            cli, ["data", "touch", "newfile", "--leaf-resource-name", "demoResc"]
        )
        assert result.output.strip() == ""
        assert result.exit_code == 0
        result = runner.invoke(
            cli, ["data", "touch", "newfile", "--replica-number", "0"]
        )
        assert result.output.strip() == ""
        assert result.exit_code == 0

    def test_data_rename(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["data", "touch", "a"])
        result = runner.invoke(cli, ["data", "touch", "b"])
        result = runner.invoke(cli, ["data", "rename", "a", "b"])
        #        assert result.output.strip() == ""
        # PRC bug - should return an error message
        assert result.exit_code == 1
        result = runner.invoke(cli, ["data", "rename", "a", "c"])
        #        assert result.output.strip() == ""
        # PRC bug - should return an error message
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "rename", "a", "one"])
        #        assert result.output.strip() == ""
        # PRC bug - should be allowed?
        #        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "rename", "one", "one"])
        #        assert result.output.strip() == ""
        # PRC bug - should return an error message
        assert result.exit_code == 1
        result = runner.invoke(cli, ["data", "rename", "one", "two"])
        assert result.output.strip() == ""
        assert result.exit_code == 0

    def test_data_remove(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["data", "remove", "doesnotexist"])
        #        self.print_result(result)
        assert (
            result.output.strip()
            == "path does not point to a data object: SYS_INVALID_INPUT_PARAM"
        )
        assert result.exit_code == 1
        result = runner.invoke(cli, ["data", "touch", "newfile"])
        result = runner.invoke(cli, ["data", "remove", "newfile"])
        #        self.print_result(result)
        assert result.output.strip() == ""
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "touch", "one/2"])
        result = runner.invoke(cli, ["data", "remove", "one"])
        #        self.print_result(result)
        assert (
            result.output.strip() == "None"
        )  # PRC bug - should say irods.exception.CAT_COLLECTION_NOT_EMPTY
        assert result.exit_code == 1

    def test_data_cd_and_pwd(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["data", "cd", "/tempZone/home"])
        assert result.output.strip() == ""
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "cd"])
        assert result.output.strip() == ""
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "cd", "nopes"])
        #        self.print_result(result)
        assert result.output.strip() == "No such collection: /tempZone/home/rods/nopes"
        assert result.exit_code == 1
        result = runner.invoke(cli, ["data", "cd", "one"])
        #        self.print_result(result)
        assert result.output.strip() == ""
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "pwd"])
        # self.print_result(result)
        assert result.output.strip() == "/tempZone/home/rods/one"
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "cd"])
        assert result.output.strip() == ""
        assert result.exit_code == 0
        result = runner.invoke(cli, ["data", "pwd"])
        assert result.output.strip() == "/tempZone/home/rods"
        assert result.exit_code == 0


if __name__ == "__main__":
    unittest.main()
