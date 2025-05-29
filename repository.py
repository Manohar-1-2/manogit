import os
import configparser
from fnmatch import fnmatch

from utility.filehandling import repo_file,repo_dir

class ManoGitRepo:
    gitdir=None
    workingtree=None
    def __init__(self,path,force=False):
        self.workingtree=path
        self.gitdir=os.path.join(path,".manogit")
        if not (force or os.path.isdir(self.gitdir)):
            raise Exception(f"Not git repository{path}")
        self.configparser=configparser.ConfigParser()
        
        configFile=repo_file(self,"config")
        
        if configFile and os.path.exists(configFile):
            self.configparser.read(configFile)
        elif not force:
            raise Exception("config file not found")
        
        if not force:
            ver=int(self.configparser.get("core", "repositoryformatversion"))
            if ver!=0:
                raise Exception("unsupported version")
def repo_default_config():
    ret = configparser.ConfigParser()

    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret

def init_repo(path):
    repo=ManoGitRepo(path,True)
    
    repo_dir(repo,"objects",mkdir=True)
    repo_dir(repo,"refs","tags",mkdir=True)
    repo_dir(repo,"refs","heads",mkdir=True)
    repo_file(repo,"refs","heads","master")

    with open(repo_file(repo, "description"), "w") as f:
        f.write("Unnamed repository; edit this file 'description' to name the repository.\n")

    with open(repo_file(repo,"refs","heads","master"), "w") as f:
        f.write("")

    # .git/HEAD
    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")
    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)

    return repo
    
def repo_find(path=".", required=True):
    path = os.path.realpath(path)

    if os.path.isdir(os.path.join(path, ".manogit")):
        return ManoGitRepo(path)

    # If we haven't returned, recurse in parent, if w
    parent = os.path.realpath(os.path.join(path, ".."))

    if parent == path:
        # Bottom case
        # os.path.join("/", "..") == "/":
        # If parent==path, then path is root.
        if required:
            raise Exception("No git directory.")
        else:
            return None

    # Recursive case
    return repo_find(parent, required)