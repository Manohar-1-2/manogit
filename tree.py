

from objects import GitObject, GitTree, object_hash, object_write, objectRead

from repository import repo_find
from utility.filehandling import repo_file,repo_dir
import os
from repository import repo_find
from utility.filehandling import repo_file

class TreeNode:
    def __init__(self, isfile=True, name=None, sha=None, subtree=None):
        self.isfile = isfile
        self.name = name
        self.sha = sha  # Only for files
        self.subtree = subtree  # Only for directories

class Tree:
    def __init__(self, name=""):
        self.name = name
        self.files = []  # List of TreeNode
        self.dirs = []   # List of TreeNode

    def add_file(self, filename, sha):
        self.files.append(TreeNode(isfile=True, name=filename, sha=sha))

    def add_dir(self, dir_name):
        subtree = Tree(name=dir_name)
        self.dirs.append(TreeNode(isfile=False, name=dir_name, subtree=subtree))
        return subtree

    def get_subtree(self, dir_name):
        for node in self.dirs:
            if node.name == dir_name:
                return node.subtree
        return None

def insert_into_tree(tree, dir_parts, sha):
    """Recursively inserts a file path and its SHA into the correct tree structure."""
    if len(dir_parts) == 1:
        tree.add_file(dir_parts[0], sha)
        return

    dirname = dir_parts[0]
    rest = dir_parts[1:]

    # Get or create subtree
    subtree = tree.get_subtree(dirname)
    if subtree is None:
        subtree = tree.add_dir(dirname)

    insert_into_tree(subtree, rest, sha)

def create_tree_from_index():
    """Reads the index and builds the nested Tree structure."""
    repo = repo_find()
    index_path = repo_file(repo, "index")

    if not os.path.exists(index_path):
        raise Exception("No index file found")

    with open(index_path, "r") as f:
        lines = f.readlines()

    root_tree = Tree(name="")

    for line in lines:
        path, sha = line.strip().split(" ")
        parts = path.split(os.sep)  # Cross-platform safe
        insert_into_tree(root_tree, parts, sha)

    return root_tree

def print_tree(tree, dir=""):
    for file_node in tree.files:
        print(os.path.join(dir, file_node.name,file_node.sha))
    
    for dir_node in tree.dirs:
        print_tree(dir_node.subtree, os.path.join(dir, dir_node.name))
def write_tree(tree, dir=""):
    for file_node in tree.files:
        # os.path.join(dir, file_node.name),
        print(file_node.name,file_node.sha,type(file_node))
    
    for dir_node in tree.dirs:
        write_tree(dir_node.subtree, os.path.join(dir, dir_node.name))
        

def serialize_tree(tree, repo):
    entries = []

    # First add all file entries
    for file in tree.files:
        entries.append(("100644", file.name, file.sha))
    # Then recursively serialize subdirectories
    for dir_node in tree.dirs:
        subtree = dir_node.subtree
        sha = serialize_tree(subtree, repo)
        entries.append(("40000", dir_node.name, sha))

    git_tree = GitTree(entries,isDeserialized=True)
    return object_write(git_tree, repo)
def deserialize_tree(git_tree, repo, name=""):
    tree = Tree(name=name)

    for mode, name, sha in git_tree.entries:
        if mode == "100644":
            # It's a file, directly add
            tree.add_file(name, sha)
        elif mode == "40000":
            # It's a directory, load its tree object recursively
            subtree_obj = objectRead(repo, sha)
            if not isinstance(subtree_obj, GitTree):
                raise Exception(f"Expected GitTree, got {type(subtree_obj)}")
            subtree = deserialize_tree(subtree_obj, repo, name=name)
            tree.dirs.append(TreeNode(isfile=False, name=name, subtree=subtree))

    return tree




    

