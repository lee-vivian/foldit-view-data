#! /usr/bin/python

# import scikit, pandas, and/or oranges

if __name__ == "__main__":
	import argparse
	prog_desc = "Foldit view options analysis."
	parser = argparse.ArgumentParser(description=prog_desc)
	#parser.add_argument('path', help="Relative path to replay directory")
	args = parser.parse_args()
	
	import sqlite3
	# Tables: options, rpnode__puzzle, sqlite_sequence, rprp_puzzle_ranks
	conn = sqlite3.connect('folditx.db')
	c = conn.cursor()
	
	command = ''
	
	while (command != 'q'):
		command = command.lower()
		
		if command == 'h':
			
			print "h - help"
			print "q - quit"
			print "t - list tables"
			print "c [table] - list columns in table"
		
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
		
		print "Enter command (h for help): "
		command = raw_input()
		
	print("Goodbye")
	
	
	
	# c.execute('''SELECT * from rpnode__puzzle;''')
	# print c.fetchone()
	# c.execute('''SELECT * from sqlite_sequence;''')
	# print c.fetchone()
	# c.execute('''SELECT * from rprp_puzzle_ranks;''')
	# print c.fetchone()



