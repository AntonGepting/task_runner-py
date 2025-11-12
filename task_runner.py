#!/usr/bin/env python3

"""
task_runner
"""


import sys, os, argparse
import subprocess
import yaml


class Task:
    """
    Task

    Attributes
    ----------

    name
    desc
    exec - Exec class
     cmd
     flags
    src - Path class
     user
     host
     path
    dst - Path class
     user
     host
     path
    tasks[] - Task classes

    """

    class Exec:
        """
        Exec parameters

        Attributes
        ----------

        cmd - program (i.e. rsync)
        flags - command line arguments (i.e. --archive)

        """

        def __init__(self):
            self.cmd = None
            self.flags = None


        def __repr__(self):
            return f"Exec {{ cmd: {self.cmd}, flags: {self.flags} }}"


        def __str__(self):
            """

            Returns
            -------

            cmd --flag0 --flag1 ...

            """

            cmd = ""
            if self.cmd is not None:
                cmd = self.cmd

            flags = ""
            if self.flags is not None:
                ' '.join(flags)

            return f"{cmd} {flags}"


        def from_yaml(self, yml):
            """
            get exec parameters from YAML str

            NOTE: previous will be overwritten, last will be accepted
            """
            for k, v in yml.items():
                if k == 'cmd':
                    self.cmd = v
                elif k == 'flags':
                    self.flags = v


        def inherit(self, parent):
            """
            inherit cmd and flags from parent, if not present
            """
            if self.cmd is None:
                self.cmd = parent.cmd
            if self.flags is None:
                self.flags = parent.flags


    #yml = yaml.safe_load("""
    #    cmd: echo
    #    flags:
    #        - a
    #        - b
    #        - c
    #""")
    #
    #e = Exec()
    #e.from_yaml(yml)
    #print(e)

    class Path:
        """
        Path parameters

        Attributes
        ----------

        user - username (for ssh)
        host - hostname (for ssh)
        path - path

        user@host:path

        """

        def __init__(self):
            self.user = None
            self.host = None
            self.path = None


        def __repr__(self):
            return f"Path {{user: {self.user}, host: {self.host}, path: {self.path}}}"


        def __str__(self):
            """
            Create full remote path from user, host and path

            used for both src or dst

            concat user + '@' + host + ':' + path

            Returns
            -------

            user@host:path
            """

            user = ""
            host = ""
            path = ""

            if self.user is not None:
                user = self.user + '@'

            if self.host is not None:
                host = self.host + ':'

            if self.path is not None:
                path = self.path

            return f"{user}{host}{path}"



        def from_yaml(self, yml):
            """
            get path parameters from YAML str

            NOTE: previous will be overwritten, last will be accepted
            """
            for k, v in yml.items():
                if k == 'user':
                    self.user = v
                elif k == 'host':
                    self.host = v
                elif k == 'path':
                    self.path = v


        def inherit(self, parent):
            """
            inherit user, host, path from parent, if not present
            """
            if self.user is None:
                self.user = parent.user
            if self.host is None:
                self.host = parent.host
            if self.path is None:
                self.path = parent.path

            #yml = yaml.safe_load("""
            #    user: a
            #    host: b
            #    path: c
            #""")
            #
            #p = Path()
            #p.from_yaml(yml)
            #print(p)


    def __init__(self):
        self.name = None
        self.desc = None
        self.exec = self.Exec()
        self.src = self.Path()
        self.dst = self.Path()
        self.tasks = []


    def __repr__(self):
        # create list of tasks
        tasks = []
        for task in self.tasks:
            tasks.append(repr(task))
        # list to str
        tasks = ','.join(tasks)

        return f"Task {{ name: {self.name}, desc: {self.desc} exec: \
{self.exec}, src: {self.src}, dst: {self.dst}, tasks: [{tasks}]}}"

    def __str__(self):
        name = ""
        if self.name is not None:
            name = self.name
        desc = ""
        if self.desc is not None:
            name = self.desc

        exec = str(self.exec)
        src = str(self.src)
        dst = str(self.dst)

        tasks = []
        l = len(self.tasks)
        for task in self.tasks:
            tasks.append(str(task))
        tasks = '\n'.join(tasks)

        return f"name: {name}\ndescription: {desc}\nexec: {exec}\n\
src: {src}\ndst: {dst}\ntasks: {l}\n{tasks}"


    def inherit(self, parent):
        """
        inherit attributes from parent, if not present

        command, flags
        src host, user, path
        dst host, user, path

        """
        self.exec.inherit(parent.exec)
        self.src.inherit(parent.src)
        self.dst.inherit(parent.dst)


    def from_yaml(self, entries):
        """
        get task from YAML str
        store keys values

        NOTE: previous will be overwritten, last will be accepted
        NOTE: first empty key will be accepted as default name
        """

        for i, (k, v) in enumerate(entries.items()):

            # only if dict
            if isinstance(v, dict):
                if k == 'exec':
                    self.exec.from_yaml(v)

                elif k == 'src':
                    self.src.from_yaml(v)

                elif k == 'dst':
                    self.dst.from_yaml(v)

            # only if list
            if isinstance(v, list):
                if k == 'tasks':
                    for item in v:
                        child = Task()
                        child.from_yaml(item)
                        self.tasks.append(child)

            # only if str
            if isinstance(v, str):
                if k == 'name':
                    self.name = v

                elif k == 'desc':
                    self.desc = v

            # if name is given direct by key name, not by name key
            if i == 0 and v is None and self.name is None:
                self.name = k



    def read_from_yaml(self, f):
        """
        read task from YAML file
        """
        entries = yaml.safe_load(f)

        self.from_yaml(entries)




    def exec_cmd(self, dry_run, verbose, debug):
        """
        exec command
        """

        # exec only if:
        #  cmd, src, dst
        if self.exec.cmd is not None:
            if self.src.path is not None:
                if self.dst.path is not None:
                    cmd = self.exec.cmd
                    flags = self.exec.flags

                    src = str(self.src)
                    dst = str(self.dst)

                    if verbose:
                        flags_str = ' '.join(flags)
                        print(f" command:     {cmd} {src} {dst} {flags_str}")

                    if not dry_run:
                        subprocess.run([cmd, src, dst] + flags)

                elif debug:
                    print("empty dst path, skipping exec")

            elif debug:
                print("empty src path, skipping exec")

        elif debug:
            print("empty command, skipping exec")


    def run(self, parent, dry_run, verbose, debug):
        """
        run task recursively

        Parameters
        ----------

        parent_params: dict contains inherited params
        task: dict contains current task
        dry_run (bool): do not run, just simulate
        verbose (bool): verbose output

        """

        if verbose:
            print("running task:")
            print(f" name:        {self.name}")
            print(f" description: {self.desc}")

        self.inherit(parent)

        if debug:
            print(self)

        # exec command
        self.exec_cmd(dry_run, verbose, debug)

        l = len(self.tasks)

        # if child tasks are existing, run them too
        if l > 0:
            if verbose:
                print("processing child tasks...")

            if debug:
                print(f"child tasks: {l}")

            # run each child task recursively
            for task in self.tasks:
                task.run(self, dry_run, verbose, debug)




def create_args():
    """
    create CLI arguments
    """

    parser = argparse.ArgumentParser(
                        prog="task_runner.py",
                        description="use tasks file",
                        epilog="")

    # print tasks
    # parser.add_argument("-p",
                        # "--print-tasks",
                        # action="store_true")

    # dry-run
    parser.add_argument("-u",
                        "--dry-run",
                        action='store_true')

    # verbose
    parser.add_argument("-v",
                        "--verbose",
                        action='store_true')

    # debug
    parser.add_argument("-g",
                        "--debug",
                        action='store_true')

    # tasks file
    parser.add_argument("task",
                        type=argparse.FileType('r'),
                        help="tasks file (example: task.yml)")
                        # default="tasks.yml"
                        # nargs='?',
                        # default=sys.stdin
                        # type=string

    # version
    parser.add_argument("-V",
                        "--version",
                        action='version',
                        version="%(prog)s 0.3")

    return parser


def use_args(args):
    """
    use CLI arguments
    """

    if args.verbose:
        print(f"reading task file: {args.task.name}")

    default = Task()
    task = Task()
    task.read_from_yaml(args.task)

    if args.debug:
        print(default)
        print(task)

    if args.verbose:
        print(f"starting with main task...")

    task.run(default, args.dry_run, args.verbose, args.debug)


# main
if __name__ == '__main__':

    # crate, parse and use command line args
    #
    parser = create_args()

    args = parser.parse_args()

    use_args(args)
