import argparse
import sys
import os
import configparser

argparser = argparse.ArgumentParser(description="Shitty git")

argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True

argsp = argsubparsers.add_parser("init", help="Initialize a new, empty repository.")
argsp.add_argument(
    "path",
    metavar="directory",
    nargs="?",
    default=".",
    help="Where to create the repository.",
)


def cmd_init(args):
    repo_create(args.path)


def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)
    match args.command:
        case "add":
            cmd_add(args)
        case "cat-file":
            cmd_cat_file(args)
        case "check-ignore":
            cmd_check_ignore(args)
        case "checkout":
            cmd_checkout(args)
        case "commit":
            cmd_commit(args)
        case "hash-object":
            cmd_hash_object(args)
        case "init":
            cmd_init(args)
        case "log":
            cmd_log(args)
        case "ls-files":
            cmd_ls_files(args)
        case "ls-tree":
            cmd_ls_tree(args)
        case "rev-parse":
            cmd_rev_parse(args)
        case "rm":
            cmd_rm(args)
        case "show-ref":
            cmd_show_ref(args)
        case "status":
            cmd_status(args)
        case "tag":
            cmd_tag(args)
        case _:
            print("Bad command")


class GitRepository(object):
    """Git repo"""

    worktree = None
    gitdir = None
    conf = None

    def __init__(self, path, force=False) -> None:
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")

        if not (force or os.path.isdir(self.gitdir)):
            raise Exception(f"Not a git repository {path}")

        self.conf = configparser.ConfigParser()
        cf = repo_path(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Config file missing")

        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception(f"Unsupported repositoryformatversion: {vers}")


def repo_path(repo: GitRepository, *path: str):
    # This should not happen
    if not repo.gitdir:
        return None
    return os.path.join(repo.gitdir, *path)


def repo_file(repo: GitRepository, *path: str, mkdir=False):
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)


def repo_dir(repo: GitRepository, *path: str, mkdir=False):

    p = repo_path(repo, *path)

    if p and os.path.exists(p):
        if os.path.isdir(p):
            return p
        else:
            raise Exception(f"Not a directory {p}")

    if p and mkdir:
        os.makedirs(p)
        return p
    else:
        return None


def repo_create(path: str):

    repo = GitRepository(path, True)
    # If we're initializing repo, We should have a worktree

    # This should never happen
    assert repo and repo.worktree, "This shouldn't have happened"
    assert repo.gitdir, "This is weird"

    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception(f"{path} is not a directory")
        if os.path.exists(repo.gitdir) and os.listdir(repo.gitdir):
            raise Exception(f"{path} is not empty")

    else:
        os.makedirs(repo.worktree)

    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    description = repo_file(repo, "description")
    assert description, "This should not happen"

    with open(description, "w") as f:
        f.write(
            "Unnamed repository; edit this file 'discription' to name the repository.\n"
        )

    head_file = repo_file(repo, "HEAD")
    assert head_file, "This should not happen"

    with open(head_file, "w") as f:
        f.write("ref: refs/heads/master\n")

    config_file = repo_file(repo, "config")
    assert config_file, "This should not happen"

    with open(config_file, "w") as f:
        config = repo_default_config()
        config.write(f)


def repo_default_config():
    ret = configparser.ConfigParser()

    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret
