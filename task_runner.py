#!/usr/bin/env python3

import sys, os, argparse
import subprocess
import yaml


# concat user + '@' + host + ':' + path
def create_path(params):
    host = ''
    if params['host'] is not None:
        host = params['host'] + ':'

    user = ''
    if params['user'] is not None:
        user = params['user'] + '@'

    path = ''
    if params['path'] is not None:
        path = params['path']

    result = user + host + path

    return result


# exec command
def run_command(params, dry_run, verbose):

    src = create_path(params['src'])
    dst = create_path(params['dst'])

    if verbose:
        print([params['cmd'], src, dst] + params['flags'])

    if not dry_run:
        print([params['cmd'], src, dst] + params['flags'])
        # subprocess.run([params['cmd'], src, dst] + params['flags'])


# use parent task host user and path
def inherit_path(task, key, params):
    if key in task.keys():
        if isinstance(task[key], dict):
            # accept given or use parent's target
            if 'host' in task[key].keys():
                params[key]['host'] = task[key]['host']

            if 'user' in task[key].keys():
                params[key]['user'] = task[key]['user']

            if 'path' in task[key].keys():
                params[key]['path'] = task[key]['path']

        # if isinstance(task['dst'], list):
        if isinstance(task[key], str):
            params[key]['path'] = task[key]


# use parent task parameters if current are empty
def init_task_params(parent_params, task):
    params = parent_params

    # accept given or use parent's src
    inherit_path(task, 'src', params)

    # accept given or use parent's dst
    inherit_path(task, 'dst', params)

    # accept given or use parent's run
    if 'prog' in task.keys():
        # accept given or use parent's cmd
        if 'cmd' in task['prog'].keys():
            params['cmd'] = task['prog']['cmd']
        # accept given or use parent's flags
        if 'flags' in task['prog'].keys():
            params['flags'] = task['prog']['flags']

    return params


class Task:

    # create default
    def __init__(self, task):
        self.task = task

    @classmethod
    def default(cls):
        params_default = {
            'cmd': None,
            'flags': None,
            'src': {
                'host': None,
                'user': None,
                'path': None,
            },
            'dst': {
                'host': None,
                'user': None,
                'path': None,
            },
        }
        return cls(params_default)



    # read tasks from YAML file
    @classmethod
    def read_from_yaml(cls, tasks_filename):
        # open tasks yml file
        with tasks_filename as f:
            task = yaml.load(f, Loader=yaml.FullLoader)
            return cls(task)

    def print(self):
        print(self.task)

    # function for recursive use of task parameters
    #
    # Parameters:
    #  parent_params: dict contains inherited params
    #  task: dict contains current task
    #  dry_run (bool): do not run, just simulate
    #  verbose (bool): verbose output
    #
    def run(self, parent_task, dry_run, verbose):
        # init params using current and parent task
        current_task = init_task_params(parent_task, self.task)

        # run if all required params are given
        if current_task['cmd'] is not None:
            if current_task['flags'] is not None:
                if current_task['src']['path'] is not None:
                    if current_task['dst']['path'] is not None:
                        run_command(current_task, dry_run, verbose)

        # if child tasks are existing
        if 'tasks' in self.task.keys():
            tasks = self.task['tasks']

            # recursive run for each child task
            for task in self.task['tasks']:
                task.run(current_task, dry_run, verbose)




# create CLI arguments
def create_args():
    parser = argparse.ArgumentParser(
                        prog='task runner, command wrapper',
                        description='use tasks file',
                        epilog='')
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
                        # default='tasks.yml'
                        # nargs='?',
                        # default=sys.stdin
                        # type=string

    return parser


# use CLI arguments
def use_args(args):
    if args.verbose:
        print(f'reading tasks file {args.tasks.name} ...')

    task = Task.read_from_yaml(args.tasks)
    #task.print()

    params_default = Task.default()
    #params_default.print()

    task.run(params_default.task, args.dry_run, args.verbose)
    # run_task(params_default, data, args.dry_run, args.verbose)



# main
if __name__ == '__main__':
    parser = create_args()
    args = parser.parse_args()
    use_args(args)
