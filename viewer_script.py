#! /usr/bin/python

# import scikit, pandas, and/or oranges

def io_mode(args):
	command = ''
	while (command != 'q'):
		command = command.lower()
		
		if command == 'h':
			
			print "h - help"
			print "q - quit"
			print "t - list tables" # options, rpnode__puzzle, sqlite_sequence, rprp_puzzle_ranks
			print "c [table] - list columns in table"
			print "e [command] - execute command"
		
		if command == 't':
			c.execute('''SELECT name from sqlite_master where type = 'table'; ''')
			for t in c.fetchall():
				print t[0]
				
		if command.startswith("c "):
			table = command[2:]
			try:
				c.execute('''SELECT * from %s;''' % table)
				for info in c.description:
					print info[0]
			except:
				print("Invalid table name")
				
		if command.startswith("e "):
			com = command[2:]
			c.execute(com) # TODO test, I don't know if string formatting is okay
			print(c.fetchall())
		
		print "Enter command (h for help): "
		command = raw_input()
	print("Goodbye")

if __name__ == "__main__":
	import argparse
	prog_desc = "Foldit view options analysis."
	parser = argparse.ArgumentParser(description=prog_desc)
	parser.add_argument('-execute', default="", help="Query to input.")
	args = parser.parse_args()
	
	import sqlite3
	conn = sqlite3.connect('folditx.db')
	c = conn.cursor()
	
	# if we specify a command from terminal, retrieve and quit
	# otherwise enter I/O mode of entering commands
	if args.execute != "":
		c.execute(args.execute) # TODO test, I don't know if string formatting is okay
		print(c.fetchall())
	else:
		io_mode(args)



