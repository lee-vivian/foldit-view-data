#! /usr/bin/python

# import scikit, pandas, and/or oranges

"""
VIEW (conceptual struct):

	Metadata
	
		RPRP_PUZZLE_RANKS
			type - 1=soloist, 2=evolver
			pid - puzzle
			uid - user
			best_score
			cur_score
			gid - group id

		RPNODE__PUZZLE
			nid - puzzle id
			vid - ??
			type
		
	View Data

	OPTIONS
	(basically everything except maybe timestamp and error flag)


	
QUERY EXAMPLES

Count values of an option:
    select advanced_mode, count(advanced_mode) from options group by advanced_mode
	
	
USEFUL CODE TIDBITS

Convert unicode back into normal string:
	my_unicode_string.encode('ascii','ignore')

"""

def io_mode(args):
	command = args.execute
	single_query = False
	if command != '':
		single_query = True
		command = "e " + command
	while (command != 'q' and command != 'exit'):
		command = command.lower()
		
		if command == 'h':
			
			print "h - help"
			print "q - quit"
			print "t - list tables" # options, rpnode__puzzle, sqlite_sequence, rprp_puzzle_ranks
			print "c [table] - list columns in table"
			print "freq [option] - count values of an option"
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
				
		if command.startswith("freq "):
			option = command[5:]
			try:
				c.execute('''select %s, count(%s) from options group by %s;''' % (option,option,option))
				print(c.fetchall())
			except Exception as e:
				print("Invalid option")
				print(e) # TEST
				
		if command.startswith("e "):
			com = command[2:]
			try:
				c.execute(com)
				print(c.fetchall())
			except sqlite3.OperationalError as e:
				print("ERR: unable to perform operation")
				print("INFO: " + str(e))
				
		if not single_query:
			print "Enter command (h for help): "
			command = raw_input("> ")
		else:
			command = 'q'
	if not single_query:
		print("Goodbye")

if __name__ == "__main__":
	import argparse
	prog_desc = "Foldit view options analysis."
	parser = argparse.ArgumentParser(description=prog_desc)
	parser.add_argument('--execute', default="", help="Query to input.")
	args = parser.parse_args()
	
	import sqlite3
	conn = sqlite3.connect('folditx.db')
	c = conn.cursor()
	io_mode(args)



