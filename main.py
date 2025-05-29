
import argparse
from fnmatch import fnmatch
from branch import cmd_change_branch, cmd_create_branch, cmd_list_branch
from commit import cmd_create_commit, cmd_status
from log import cmd_log
from objects import cat_file, cmd_add, cmd_hash_object, object_hash
from repository import init_repo

def main():
    parser = argparse.ArgumentParser(
        prog="manogit",
        description="A simple version control system like Git"
    )

    # Subparsers are used for commands like `manogit init`, `manogit commit`, etc.
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize a new repository")
    init_parser.add_argument("path",
                   metavar="directory",
                   nargs="?",
                   default=".",
                   help="Where to create the repository.")
    # Parse args
    cat_file_parser = subparsers.add_parser("cat-file",
                                 help="Provide content of repository objects")

    cat_file_parser.add_argument("type",
                   metavar="type",
                   choices=["blob", "commit", "tag", "tree"],
                   help="Specify the type")

    cat_file_parser.add_argument("object",
                   metavar="object",
                   help="The object to display")
    hash_object_parser = subparsers.add_parser(
        "hash-object",
        help="Compute object ID and optionally creates a blob from a file")

    hash_object_parser.add_argument("-t",
                    metavar="type",
                    dest="type",
                    choices=["blob", "commit", "tag", "tree"],
                    default="blob",
                    help="Specify the type")

    hash_object_parser.add_argument("-w",
                    dest="write",
                    action="store_true",
                    help="Actually write the object into the database")

    hash_object_parser.add_argument("path",
                    help="Read object from <file>")
    
    add_parser = subparsers.add_parser(
        "add",
        help="add files to staging area")
    add_parser.add_argument("path",metavar="directory",
                   nargs="?",
                   default=".",
                   help="file to add staging area.")
    

    commit_parser = subparsers.add_parser(
        "commit",
        help="commit the code from staging area")

    commit_parser.add_argument("-m",
                    dest="message",
                    help="write message about commit")

    add_parser = subparsers.add_parser(
        "status",
        help="gives status of repo")
    
    log_parser = subparsers.add_parser(
        "log",
        help="gives status of repo")
    
    branch_parser = subparsers.add_parser(
        "branch",
        help="gives status of repo")
    
    checkout_parser = subparsers.add_parser(
        "checkout",
        help="gives status of repo")
    checkout_parser.add_argument("branchname",help="change current branch")
    
    branch_parser.add_argument(
    "name",
    nargs="?",
    help="Branch name to create"
    )

    args = parser.parse_args()

    if args.command == "init":
        init_repo(args.path)
    elif args.command=='cat-file':
        cat_file(args)
    elif args.command=="hash-object":
        cmd_hash_object(args)
    elif args.command=="add":
        cmd_add(args)
    elif args.command=="commit":
        cmd_create_commit(args)
    elif args.command=="status":
        cmd_status(args)
    elif args.command=="log":
        cmd_log(args)
    elif args.command=="branch":
        if args.name==None:
            cmd_list_branch(args)
        else:
            cmd_create_branch(args)
    elif args.command=="checkout":
        cmd_change_branch(args)

if __name__ == "__main__":
    main()
