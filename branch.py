import os
from commit import compare_staged_committree, print_tree
from objects import objectRead
from ref import get_head_ref, get_ref_sha
from repository import repo_find
from tree import deserialize_tree
from utility.filehandling import repo_dir, repo_file


def create_branch(repo, name, sha=None):
    if name in list_branches(repo):
        print("branch name already exists")
        return
    if sha is None:
        ref_path = get_head_ref(repo)
        sha=get_ref_sha(repo,ref_path)

    path = repo_file(repo, f"refs/heads/{name}")
    with open(path, "w") as f:
        f.write(sha + "\n")
    print(f"Created branch {name} pointing to {sha}")




def checkout_branch(repo, name):
    ref_path_curr = get_head_ref(repo)
    commit_sha_curr=get_ref_sha(repo,ref_path_curr)
    commit_obj_curr=objectRead(repo,commit_sha_curr)
    path = f"refs/heads/{name}"
    if not os.path.isfile(repo_file(repo,path,mkdir=False)):
        raise Exception(f"Branch {name} does not exist")
    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write(f"ref: {path}")
    ref_path = get_head_ref(repo)
    commit_sha=get_ref_sha(repo,ref_path)
    commit_obj=objectRead(repo,commit_sha)
    writefileChanges(commit_obj.kv["tree"],commit_obj_curr.kv["tree"])
    print(f"Switched to branch {name}")

def list_branches(repo):
    heads_dir = repo_dir(repo, "refs/heads")
    return os.listdir(heads_dir)

def cmd_list_branch(args):
    repo=repo_find()
    branchlist=list_branches(repo)
    currentBranch= get_head_ref(repo).split("/")[-1]
    for branch in branchlist:
        if branch==currentBranch:
            print("* "+branch)
        else:
            print(branch)
def cmd_create_branch(args):
    repo=repo_find()
    create_branch(repo,args.name)

def cmd_change_branch(args):
    repo=repo_find()
    checkout_branch(repo,args.branchname)

import os
def write_index(repo, index):
    index_path = os.path.join(repo.gitdir, "index")
    with open(index_path, "w") as f:
        for path, sha in sorted(index.items()):
            f.write(f"{path} {sha}\n")

def read_index(repo):
    index_path = os.path.join(repo.gitdir, "index")
    index = {}

    if not os.path.exists(index_path):
        return index  # No index yet

    with open(index_path, "r") as f:
        for line in f:
            path, sha = line.strip().split(" ", 1)
            index[path] = sha

    return index

def writefileChanges(target_branch_tree_sha, current_branch_tree_sha):
    repo = repo_find()

    # Deserialize trees
    target_tree_obj = objectRead(repo, target_branch_tree_sha)
    tree_obj_target = deserialize_tree(target_tree_obj, repo)
    tree_dic_target = print_tree(tree_obj_target, {})

    current_tree_obj = objectRead(repo, current_branch_tree_sha)
    tree_obj_current = deserialize_tree(current_tree_obj, repo)
    tree_dic_current = print_tree(tree_obj_current, {})

    # Compare trees
    added, deleted, modified = compare_staged_committree(tree_dic_target, tree_dic_current)

    # Read current index
    index = read_index(repo)

    # 1. Delete removed files and update index
    for file_path in deleted:
        abs_path = os.path.join(repo.workingtree, file_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
            print(f"Deleted: {file_path}")
        if file_path in index:
            del index[file_path]

    # 2. Add new files and update index
    for file_path in added:
        sha = tree_dic_target[file_path]
        obj = objectRead(repo, sha)
        abs_path = os.path.join(repo.workingtree, file_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(obj.blobdata)
        index[file_path] = sha
        print(f"Added: {file_path}")

    # 3. Overwrite modified files and update index
    for file_path in modified:
        sha = tree_dic_target[file_path]
        obj = objectRead(repo, sha)
        abs_path = os.path.join(repo.workingtree, file_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(obj.blobdata)
        index[file_path] = sha
        print(f"Updated: {file_path}")

    # 4. Write updated index back to file
    write_index(repo, index)

    
def write_tree_filesys(tree):
    pass