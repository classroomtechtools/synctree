"""
An alternative way to do subprocesses
"""

import pexpect

class CLIImporter:
	def __init__(self):
		pass

	def run(self, command):
		sub = '/bin/bash -c "{}"'.format(command)
		child_process = pexpect.spawn(sub)
		child_process.expect(pexpect.EOF)
		return child_process.before

if __name__ == "__main__":

	cli = CLIImporter()
	stdout = cli.run("ls /Users/")
	print(stdout)