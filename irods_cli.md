# irods

A Python iRODS Command Line Interface (CLI), part of `python-irodsclient`.

```
pip install python-irodsclient
```

```
$ irods
Usage: irods [OPTIONS] COMMAND [ARGS]...

  The iRODS CLI

Options:
  -v, --version  Show the version and exit.
  -h, --help     Show this message and exit.

Commands:
  data (d)       The data operations
  group (g)      The group operations
  query (q)      The query operations
  resource (re)  The resource operations
  rule (ru)      The rule operations
  ticket (t)     The ticket operations
  user (u)       The user operations
  zone (z)       The zone operations
```

## autocompletion

Shell autocompletion is available for `bash`, `zsh`, and `fish`.

Activate `zsh` or `fish` by replacing `bash_source` in the following examples.

```
eval $(_IRODS_COMPLETE=bash_source irods)
```
or
```
_IRODS_COMPLETE=bash_source irods > ~/.irods-complete.bash
source ~/.irods-complete.bash
```
or
```
_IRODS_COMPLETE=bash_source irods > ~/.irods-complete.bash
echo "source ~/.irods-complete.bash" >> ~/.bashrc
```


## testing

Run the entire test suite
```
python3 test_irods_cli.py
```
Generate a coverage report
```
pip install pytest pytest-cov
pytest test_irods_cli.py --cov && coverage html
```
Run tests matching a regex (could be a single test)
```
pytest test_irods_cli.py --cov -k <regex_in_test_name>
```

## commands

### authenticate

| command           | admin_only |
|-------------------| --- |
| initialize / init |  |
| exit              |  |

or

| command           | admin_only |
|-------------------| --- |
| initialize / init |  |
| edit              |  |
| reset             |  |

### data

| command            | data_object | collection | admin_only |
|--------------------| --- | --- | --- |
| calculate_checksum | x | x | |
| cd                 | x | x | |
| copy               | x | x | |
| list / show / stat | x | x | |
| mkdir / create     | | x | |
| modify-metadata    | x | x | |
| modify-permissions | x | x | |
| modify-replica     | x | | yes |
| pwd                | x | x | |
| read / get         | x | x | |
| register           | x | x | |
| remove / delete    | x | x | |
| rename / move      | x | x | |
| replicate          | x | x | |
| set-inheritance    | | x | |
| set-permission     | x | x | |
| sync               | x | x | |
| touch              | x | x | |
| tree               | | x | |
| trim               | x | x | |
| unregister         | x | x | |
| verify-checksum    | x | x | |
| write / put        | x | x | |

### group

| command         | admin_only |
|-----------------| --- |
| create          | groupadmin |
| list / show     | yes? or just a genquery? |
| modify-metadata | yes |
| remove / delete | yes |

### query

| command                | admin_only |
|------------------------| --- |
| add-specific-query     | yes |
| execute-general-query  | |
| execute-specific-query | |
| list-columns           | |
| remove-specific-query  | yes |

### resource

| command            | admin_only |
|--------------------| --- |
| add-child          | yes |
| create             | yes |
| list / show / stat | |
| modify             | yes |
| modify-metadata    | yes |
| rebalance          | yes |
| remove / delete    | yes |
| remove-child       | yes |

### rule

| command           | admin_only |
|-------------------| --- |
| execute           | |
| list-delay-rules  | just a genquery? |
| list-rule-engines | |
| remove-delay-rule | |

### ticket

| command         | admin_only |
|-----------------| --- |
| create          | |
| list / show     | yes |
| modify          | |
| remove / delete | yes |


### user

| command            | admin_only |
|--------------------| --- |
| add-to-group       | groupadmin |
| authenticate       | |
| create             | groupadmin |
| is-member-of-group | groupadmin? |
| list / show        | yes? or just a genquery? |
| modify-metadata    | yes |
| remove / delete    | yes |
| remove-from-group  | groupadmin |
| set-password       | yes |
| set-user-type      | yes |

### zone

| command                | admin_only |
|------------------------| --- |
| create / add           | yes |
| get-grid-configuration | yes |
| list / show            | |
| modify                 | yes |
| remove / delete        | yes |
| report                 | yes |
| set-grid-configuration | yes |

## other...

- fsck - checks local things against catalog
- scan - checks local things against catalog
- rmtrash - just a path remove?

## discussion


every command can return json output

 - but `--json` should be the default? or is that weird?
 - human should be the first class consumer, then machine/json

async

 - cli could use new async things
   - use tokens
   - local daemon doing actual work
   - cli submitting/checking work to local daemon
 - a local application has a footprint
   - runs longer than a single API call
   - can keep track of stuff
   - multiple threads puts/gets
   - iDrop did this (java, local client, windowed, sync-manager)
     - could close laptop, walk around, re-open, keep going
 - async + status check (via async token)
   - put
   - get
   - sync
   - mv
   - cp
   - repl
   - trim
   - rm
   - register
   - unregister
   - rebalance
 - don't forget about blackboard
   - in server-only experimental recursive functions
   - https://github.com/irods/irods/blob/main/plugins/experimental/include/irods/private/parallel_filesystem_operation.hpp
