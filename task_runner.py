#!/usr/bin/env python3

import sys, os, argparse
import subprocess
import yaml

# CLI consts
PROGRAM_NAME = 'task runner, command wrapper'
PROGRAM_DESCRIPTION = 'use tasks file'
PROGRAM_EPILOG = ''
TASKS_FILE_DEFAULT = 'tasks.yml'

# YAML task file consts
USER_KEY = 'user'
HOST_KEY = 'host'
PATH_KEY = 'path'
SRC_KEY = 'src'
DST_KEY = 'dst'
PROG_KEY = 'prog'
CMD_KEY = 'cmd'
FLAGS_KEY = 'flags'
TASKS_KEY = 'tasks'


# concat user + '@' + host + ':' + path
def create_path(params):
    host = ''
    if params[HOST_KEY] is not None:
        host = params[HOST_KEY] + ':'

    user = ''
    if params[USER_KEY] is not None:
        user = params[USER_KEY] + '@'

    path = ''
    if params[PATH_KEY] is not None:
        path = params[PATH_KEY]

    result = user + host + path

    return result


# exec command
def run_command(params, dry_run, verbose):

    src = create_path(params[SRC_KEY])
    dst = create_path(params[DST_KEY])

    if verbose:
        print([params[CMD_KEY], src, dst] + params[FLAGS_KEY])

    if not dry_run:
        subprocess.run([params[CMD_KEY], src, dst] + params[FLAGS_KEY])


# use parent task host user and path
def inherit_path(task, key, params):
    if key in task.keys():
        if isinstance(task[key], dict):
            # accept given or use parent's target
            if HOST_KEY in task[key].keys():
                params[key][HOST_KEY] = task[key][HOST_KEY]

            if USER_KEY in task[key].keys():
                params[key][USER_KEY] = task[key][USER_KEY]

            if PATH_KEY in task[key].keys():
                params[key][PATH_KEY] = task[key][PATH_KEY]

        # if isinstance(task[DST_KEY], list):
        if isinstance(task[key], str):
            params[key][PATH_KEY] = task[key]


# use parent task parameters if current are empty
def init_task_params(parent_params, task):
    params = parent_params

    # accept given or use parent's src
    inherit_path(task, SRC_KEY, params)

    # accept given or use parent's dst
    inherit_path(task, DST_KEY, params)

    # accept given or use parent's run
    if PROG_KEY in task.keys():
        # accept given or use parent's cmd
        if CMD_KEY in task[PROG_KEY].keys():
            params[CMD_KEY] = task[PROG_KEY][CMD_KEY]
        # accept given or use parent's flags
        if FLAGS_KEY in task[PROG_KEY].keys():
            params[FLAGS_KEY] = task[PROG_KEY][FLAGS_KEY]

    return params


# function for recursive use of task parameters
#
# Parameters:
#  parent_params: dict contains inherited params
#  task: dict contains current task
#  dry_run (bool): do not run, just simulate
#  verbose (bool): verbose output
#
def run_task(parent_params, task, dry_run, verbose):
    # init params using current and parent task
    params = init_task_params(parent_params, task)

    # run if all required params are given
    if params[CMD_KEY] is not None:
        if params[FLAGS_KEY] is not None:
            if params[SRC_KEY][PATH_KEY] is not None:
                if params[DST_KEY][PATH_KEY] is not None:
                    run_command(params, dry_run, verbose)

    # if child tasks are existing
    if TASKS_KEY in task.keys():
        tasks = task[TASKS_KEY]

        # recursive run for each child task
        for task in task[TASKS_KEY]:
            run_task(params, task, dry_run, verbose)


# read tasks
def read_tasks_file(tasks_filename):
    # open tasks yml file
    with tasks_filename as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        return data


# create CLI arguments
def create_args():
    parser = argparse.ArgumentParser(
                        prog=PROGRAM_NAME,
                        description=PROGRAM_DESCRIPTION,
                        epilog=PROGRAM_EPILOG)
    # print tasks
    # parser.add_argument('-p',
                        # '--print-tasks',
                        # action='store_true')

    # verbose
    parser.add_argument('-u',
                        '--dry-run',
                        action='store_true')

    # verbose
    parser.add_argument('-v',
                        '--verbose',
                        action='store_true')
    # tasks file
    parser.add_argument('tasks',
                        type=argparse.FileType('r'),
                        help='tasks file (default: tasks.yml)')
                        # default=TASKS_FILE_DEFAULT
                        # nargs='?',
                        # default=sys.stdin
                        # type=string

    return parser


# use CLI arguments
def use_args(args):
    if args.verbose:
        print(f'reading tasks file {args.tasks.name} ...')

    data = read_tasks_file(args.tasks)

    params_default = {
        CMD_KEY: None,
        FLAGS_KEY: None,
        SRC_KEY: {
            HOST_KEY: None,
            USER_KEY: None,
            PATH_KEY: None,
        },
        DST_KEY: {
            HOST_KEY: None,
            USER_KEY: None,
            PATH_KEY: None,
        },
    }

    run_task(params_default, data, args.dry_run, args.verbose)



# main
if __name__ == '__main__':
    parser = create_args()
    args = parser.parse_args()
    use_args(args)
