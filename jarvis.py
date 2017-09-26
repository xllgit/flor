#!/usr/bin/env python3
import os, sys, git, subprocess, csv, inspect
from graphviz import Digraph
from shutil import copyfile

def __run_proc__(bashCommand):
	process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
	output, error = process.communicate()
	return str(output, 'UTF-8')

def func(f):
	def wrapped_func(in_artifacts, out_artifacts):
		f(in_artifacts, out_artifacts)
		return inspect.getsourcefile(f).split('/')[-1]
	return wrapped_func

class Artifact:

	# loc: location
	# parent: each artifact is produced by 1 action
	def __init__(self, loc, parent):
		self.loc = loc
		self.dir = "artifacts.d"
		self.parent = parent

		# Now we bind the artifact to its parent
		self.parent.out_artifacts.append(self)

	def pull(self):
		loclist = [self.loc,]
		self.parent.__run__(loclist)

		# get the script names
		scriptNames = ['driver.py',]
		self.parent.__scriptNameWalk__(scriptNames)

		# Now the artifact exists, do git
		# We resolve the directory name by loc
		dir_name = self.dir
		# If the directory not exists, need to init repo
		if not os.path.exists(dir_name):
			os.makedirs(dir_name)
			# Move new files to the artifacts repo
			for loc in loclist:
				os.rename(loc, dir_name + "/" + loc)
			for script in scriptNames:
				copyfile(script, dir_name + "/" + script)
			os.chdir(dir_name)
			repo = git.Repo.init(os.getcwd())
			with open('.gitignore', 'w') as f:
				f.write('.jarvis\n')
			repo.index.add(loclist + scriptNames)
			repo.index.commit("initial commit")
			tree = repo.tree()
			with open('.jarvis', 'w') as f:
				for obj in tree:
					commithash = __run_proc__("git log " + obj.path).replace('\n', ' ').split()[1]
					f.write(obj.path + " " + commithash + "\n")
			os.chdir('../')
		else:
			for loc in loclist:
				os.rename(loc, dir_name + "/" + loc)
			for script in scriptNames:
				copyfile(script, dir_name + "/" + script)
			os.chdir(dir_name)
			repo = git.Repo(os.getcwd())
			repo.index.add(loclist + scriptNames)
			repo.index.commit("incremental commit")
			tree = repo.tree()
			with open('.jarvis', 'w') as f:
				for obj in tree:
					commithash = __run_proc__("git log " + obj.path).replace('\n', ' ').split()[1]
					f.write(obj.path + " " + commithash + "\n")
			os.chdir('../')
			
	def plot(self, rankdir=None):
		# WARNING: can't plot before pulling.
		# Prep globals, passed through arguments
		dot = Digraph()
		diagram = {"dot": dot, "counter": 0, "sha": {}}

		with open('artifacts.d/.jarvis') as csvfile:
			reader = csv.reader(csvfile, delimiter=' ')
			for row in reader:
				ob, sha = row
				diagram["sha"][ob] = sha

		self.parent.__plotWalk__(diagram)
		
		dot.format = 'png'
		if rankdir == 'LR':
			dot.attr(rankdir='LR')
		dot.render('driver.gv', view=True)
		
		

	def getLocation(self):
		return self.loc

	def hasChanged(self):
		pass

	"""
	We will want to check the loc prefix to decide where to look
	for existence e.g. http, s3, sftp, etc.
	No pre-defined prefix, assume local filesystem.
	"""
	def exists(self):
		if not os.path.isfile(self.loc):
			print(self.loc + " not found.")
			sys.exit(1)

	"""
	We assume an open-ended Integrity predicate on each artifact. 
	The design of this predicate language is TBD
	"""
	def isLegal(self):
		pass

	def stat(self):
		pass


class Action:

	def __init__(self, func, in_artifacts=None):
		self.func = func
		self.out_artifacts = []
		self.in_artifacts = in_artifacts


	def __run__(self, loclist):
		if self.in_artifacts:
			for artifact in self.in_artifacts:
				loclist.append(artifact.loc)
				artifact.parent.__run__(loclist)
		self.script = self.func(self.in_artifacts, self.out_artifacts)

	def produce(self, loc):
		return Artifact(loc, self)

	def __scriptNameWalk__(self, scriptNames):
		scriptNames.append(self.script)
		if self.in_artifacts:
			for artifact in self.in_artifacts:
				artifact.parent.__scriptNameWalk__(scriptNames)
				
	def __plotWalk__(self, diagram):
		dot = diagram["dot"]
		
		# Create nodes for the children
		
		to_list = []
		
		# Prepare the children nodes
		for child in self.out_artifacts:
			node_diagram_id = str(diagram["counter"])
			dot.node(node_diagram_id, child.loc + "\n" + diagram["sha"][child.loc][0:6] + "...", shape="box")
			to_list.append(node_diagram_id)
			diagram["counter"] += 1
		
		# Prepare this node
		node_diagram_id = str(diagram["counter"])
		dot.node(node_diagram_id, self.script + "\n" + diagram["sha"][self.script][0:6] + "...", shape="ellipse")
		diagram["counter"] += 1
		
		for to_node in to_list:
			dot.edge(node_diagram_id, to_node)
		
		if self.in_artifacts:
			for artifact in self.in_artifacts:
				from_nodes = artifact.parent.__plotWalk__(diagram)
				for from_node in from_nodes:
					dot.edge(from_node, node_diagram_id)
		
		return to_list
