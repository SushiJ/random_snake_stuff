import argparse
from io import BufferedReader
import sys
import os
import configparser

import zlib
import hashlib

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

argsp = argsubparsers.add_parser(
    "cat-file", help="Provide content of repository objects"
)
argsp.add_argument(
    "type",
    metavar="type",
    choices=["blob", "tree", "commit", "tag"],
    help="Specify the type",
)
argsp.add_argument("object", metavar="object", help="The object to display")

argsp = argsubparsers.add_parser(
    "hash-object", help="Compute object ID and optionally creates a blob from a file"
)
argsp.add_argument(
    "-t",
    metavar="type",
    choices=["blob", "tree", "commit", "tag"],
    default="blob",
    help="Specify the type",
)
argsp.add_argument(
    "-w", dest="write", action="store_true", help="Write the object into database."
)
argsp.add_argument("path", help="Read object from <file>")


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


def repo_find(path=".", required=True):
    path = os.path.realpath(path)

    if os.path.isdir(os.path.join(path, ".git")):
        return GitRepository(path)

    parent = os.path.realpath(os.path.join(path, ".."))

    # if parent == "/" ( os.path.join("/", "..") == "/" )
    if parent == path:
        if required:
            raise Exception("Not git dir")
        else:
            return None

    return repo_find(parent, required)


class GitObject(object):

    def __init__(self, data=None) -> None:
        if data != None:
            self.deserialize(data)
        else:
            self.init()

    def serialize(self, repo: GitRepository):
        raise Exception("unimplemented")

    def deserialize(self, data):
        raise Exception("unimplemented")

    def init(self):
        pass


def read_object(repo, sha):
    path = repo_file(repo, "objects", sha[0:2], sha[2:])

    if not path or not os.path.isfile(path):
        return None

    with open(path, "rb") as f:
        raw = zlib.decompress(f.read())

        x = raw.find(b" ")  # read object type
        fmt = raw[0:x]

        y = raw.find(b"x00", x)  # Read and validate object size
        size = int(raw[x:y].decode("ascii"))

        if size != len(raw) - y - 1:
            raise Exception(f"Malformed object {sha}: bad length")

        match fmt:
            case b"commit":
                c = GitCommit
            case b"tree":
                c = GitTree
            case b"tag":
                c = GitTag
            case b"blob":
                c = GitBlob
            case _:
                raise Exception(f"Unknown type {fmt.decode('ascii')} for object {sha}")

        return c(raw[y + 1 :])


def write_object(obj: GitObject, repo=None):
    data = obj.serialize

    result = obj.fmt + b" " + str(len(data)).encode() + b"\x00" + data

    sha = hashlib.sha1(result).hexdigest()

    if repo:
        path = repo_file(repo, "objects", sha[0:2], sha[2:], mkdir=True)

        assert path, "Write object path should exist"
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(zlib.compress(result))

    return sha


class GitBlob(GitObject):
    fmt = b"blob"

    def serialize(self):
        return self.blobdata

    def deserialize(self, data):
        self.blobdata = data


def cmd_cat_file(args):
    repo = repo_find()

    assert repo, "There exists a repo"
    cat_file(repo, args.object, fmt=args.type.encode())


def cat_file(repo: GitRepository, obj, fmt=None):
    obj = read_object(repo, find_object(repo, obj, fmt=fmt))
    sys.stdout.buffer.write(obj.serialize())


def find_object(repo: GitRepository, name, fmt=None, follow=True):
    return name  # placeholder till we get more stuff done


def cmd_hash_object(args):

    if args.write:
        repo = repo_find()
    else:
        repo = None

    with open(args.path, "rb") as fd:
        sha = hash_object(fd, args.type.encode(), repo)
        print(sha)


def hash_object(fd: BufferedReader, fmt, repo=None):
    data = fd.read()

    match fmt:
        case b"commit":
            obj = GitCommit(data)
        case b"tree":
            obj = GitTree(data)
        case b"tag":
            obj = GitTag(data)
        case b"blob":
            obj = GitBlob(data)
        case _:
            raise Exception(f"Unknown type {fmt}")

    return write_object(obj, repo)


def rec_parse(raw, start=0, dct=None):
    if not dct:
        dct = dict()

    spc = raw.find(b" ", start)
    nl = raw.find(b"\n", start)

    # if spc = -1, it's a blank line, meaning it's the message
    if (spc < 0) or (nl < spc):
        assert nl == start
        dct[None] = raw[start + 1 :]
        return dct

    key = raw[start:spc]

    end = start
    while True:
        end = raw.find(b"\n", end + 1)  # find end
        if raw[end + 1] != ord(" "):
            break

    value = raw[spc + 1 : end].replace(b"\n ", b"\n")

    if key in dct:
        if type(dct[key]) == list:
            dct[key].append(value)
        else:
            dct[key] = [dct[key], value]

    else:
        dct[key] = value

    return rec_parse(raw, start=end + 1, dct=dct)


def serialize(kv):
    ret = b""

    for k in kv.keys():
        if k == None:
            continue  # We don't care about the message
        val = kv[k]

        # Normalise it
        if type(val) != list:
            val = [val]

        for v in val:
            ret += k + b"" + (v.replace(b"\n", b"\n ")) + b"\n"

    ret += b"\n" + kv[None]  # append the message

    return ret


class GitCommit(GitObject):
    fmt = b"commit"

    def deserialize(self, data):
        self.kv = rec_parse(data)

    def serialize(self):
        serialize(self.kv)
