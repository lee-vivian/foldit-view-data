#! /usr/bin/python
from __future__ import division
import math, operator, csv
from collections import defaultdict

# import scikit, pandas, and/or oranges

"""
VIEW (conceptual struct):

	Metadata
	
		RPRP_PUZZLE_RANKS
			type - 1=soloist, 2=evolver
			pid - puzzle
			uid - user
			best_score - note: scores are in rosetta energy, so lower is better
			cur_score
			gid - group id

		RPNODE__PUZZLE
			nid - puzzle id
			vid - version id
			title		
		
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

MIN_HIGHSCORES_PER_EXPERT = 3
FREQ_COUNT_QUERY = '''select %s, count(%s) from options group by %s;'''
PIDS_BY_CAT = {}

BINARY_OPTIONS = [
	"advanced_mode",
	"electron_density_panel__backface_culling", 
	"music", 
	"puzzle_dialog__show_beginner", 
	"puzzle_dialog__show_old", 
	"rank_popups", 
	"reduce_bandwidth", 
	"render__option__shader_outline", 
	"selection_mode", 
	"selection_mode__show_notes", 
	"sound", 
	"switch_middle_right_click", 
	"switch_residue_colors", 
	"tooltips", 
	"view_options__dark_background", 
	"view_options__gui_fade", 
	"view_options__guide_pulse", 
	"view_options__relative_score_coloring", 
	"view_options__show_backbone_issues", 
	"view_options__show_bondable_atoms", 
	"view_options__show_buried_polars", 
	"view_options__show_clashes", 
	"view_options__show_contact_map_geoms", 
	"view_options__show_hbonds", 
	"view_options__show_helix_hbonds", 
	"view_options__show_issues", 
	"view_options__show_non_protein_hbonds", 
	"view_options__show_other_hbonds", 
	"view_options__show_outlines", 
	"view_options__show_residue_burial", 
	"view_options__show_sidechain_hbonds", 
	"view_options__show_sidechains_with_issues", 
	"view_options__show_voids", 
	"view_options__sym_chain_colors", 
	"view_options__sym_chain_visible", 
	"view_options__working_pulse_style", 
]

CAT_OPTIONS = [
	"update_group", 
	"view_options__current_visor", 
	"view_options__render_style", 
	"view_options__sidechain_mode", 
]

FULL_OPTIONS_LIST = [
	"advanced_mode",
	"autoshow_chat__global",
	"autoshow_chat__group",
	"autoshow_chat__puzzle",
	"autoshow_chat__veteran",
	"autoshow_notifications",	"chat__auto_reconnect",	"chat__disable_non_group",	"chat_enable_public_profainty_filter", 
	"cleanup_temp_files", 	"electron_density_panel__alpha", 
	"electron_density_panel__backface_culling", 
	"electron_density_panel__color", 
	"electron_density_panel__threshold", 
	"electron_density_panel__visualization", 
	"graph_options__graph_length_value", 
	"graph_options__graph_memory_value", 
	"gui__desired_fps", 
	"gui__desired_window_height", 
	"gui__desired_window_width", 
	"gui__file_dir", 
	"gui__image_dir", 
	"login_dialog__disable_timeouts", 
	"login_dialog__player", 
	"login_dialog__proxy", 
	"login_dialog__use_proxy", 
	"music", 
	"puzzle_dialog__show_beginner", 
	"puzzle_dialog__show_old", 
	"rank_popups", 
	"reduce_bandwidth", 
	"render__option__shader_outline", 
	"selection_mode", 
	"selection_mode__show_notes", 
	"sound", 
	"switch_middle_right_click", 
	"switch_residue_colors", 
	"tooltips", 
	"update_group", 
	"view_options__current_visor", 
	"view_options__dark_background", 
	"view_options__gui_fade", 
	"view_options__guide_pulse", 
	"view_options__relative_score_coloring", 
	"view_options__render_style", 
	"view_options__show_backbone_issues", 
	"view_options__show_bondable_atoms", 
	"view_options__show_buried_polars", 
	"view_options__show_clashes", 
	"view_options__show_contact_map_geoms", 
	"view_options__show_hbonds", 
	"view_options__show_helix_hbonds", 
	"view_options__show_issues", 
	"view_options__show_non_protein_hbonds", 
	"view_options__show_other_hbonds", 
	"view_options__show_outlines", 
	"view_options__show_residue_burial", 
	"view_options__show_sidechain_hbonds", 
	"view_options__show_sidechains_with_issues", 
	"view_options__show_voids", 
	"view_options__sidechain_mode", 
	"view_options__sym_chain_colors", 
	"view_options__sym_chain_visible", 
	"view_options__working_pulse_style", 
]

# Returns true iff score is <= 5% of best scores for this puzzle
def is_highscore(pid, score):
	c.execute('''select distinct uid, best_score from rprp_puzzle_ranks where pid=%d group by uid order by best_score asc;''' % pid)
	# count entries, get the entry that's exactly 95th percentile, check our score vs that
	results = c.fetchall()
	num_scores = len(results)
	index = int(math.ceil(num_scores*0.05))
	min_score = results[index][1]
	return score <= min_score
	
# Returns true iff expert has achieved a high score in MIN_HIGHSCORES_PER_EXPERT distinct puzzles
def is_expert(uid):
	# get list of their best scores for each puzzle
	# count is_highscore
	c.execute('''select pid, best_score from rprp_puzzle_ranks where uid=\"%s\" order by best_score asc;''' % uid)
	results = c.fetchall()
	num_highscores = 0
	for result in results:
		if is_highscore(result[0], result[1]):
			num_highscores += 1
	return num_highscores >= MIN_HIGHSCORES_PER_EXPERT
	
def get_all_experts():
	pass # TODO
	
# returns the entropy for a binary var
def entropy(count_0, count_1):
	p = count_1 / (count_0 + count_1)
	return -(p * math.log(p,2)) - (1 - p) * math.log(1-p,2)

def get_all_entropies():
	ent_dict = defaultdict(float)
	for o in BINARY_OPTIONS:
		try:
			c.execute(FREQ_COUNT_QUERY % (o,o,o))
			results = c.fetchall()
			# note that it returns (None,0) as result 0, I haven't figured out how to silence that
			count_0 = results[1][1]
			count_1 = results[2][1]
			ent_dict[o] = entropy(count_0, count_1)
		except Exception as e:
			print("Invalid option: " + str(o))
	sorted_dict = sorted(ent_dict.items(), key=operator.itemgetter(1), reverse=True)
	for option, en in sorted_dict:
		print(option + ": " + str(en))
	
def freq_all():
	for o in FULL_OPTIONS_LIST:
		try:
			c.execute(FREQ_COUNT_QUERY % (o,o,o))
			print(o.upper())
			print(c.fetchall())
		except Exception as e:
			print("Invalid option: " + str(o))
		

def clean_db():
	pass
	#for o in FULL_OPTIONS_LIST:
		# c.execute( # TODO, remove unicode
		
def import_categories():
	global PIDS_BY_CAT
	with open('puzzle_categories.csv', 'r') as cat_file:
		reader = csv.reader(cat_file)
		for row in reader:
			pid = row[0]
			for cat in row[1:]:
				if cat == "NULL":
					continue
				if cat not in PIDS_BY_CAT.keys():
					PIDS_BY_CAT[cat] = []
				PIDS_BY_CAT[cat].append(pid)
	print("Imported puzzle categories.")
	for cat in PIDS_BY_CAT.keys():
		num_puz = len(PIDS_BY_CAT[cat])
		if args.debug:
			print("    " + cat + ": " + str(num_puz) + " puzzles")
		if num_puz < 10:
			if args.debug:
				print("    INFO: Dropping " + cat + " (too few puzzles)")
			PIDS_BY_CAT.pop(cat, None)
		
		
# place to run tests
def test(args):
	print("Beginning Tests...")
	# Tests go here
	
	print("Done.")

def io_mode(args):	
	import_categories()
	single_query = args.execute != '' or args.quick != ''
	command = ''
	if args.execute:
		command = "e " + args.execute
	if args.quick:
		command = args.quick
	while (command != 'q' and command != 'exit'):
		command = command.lower()
		
		if command == 'h':
			
			print "h - help"
			print "q - quit"
			print "t - list tables" # options, rpnode__puzzle, sqlite_sequence, rprp_puzzle_ranks
			print "c [table] - list columns in table"
			print "e [command] - execute command"
			print "freq [option] - count values of an option (or 'all')"
			print "ent [option] - get entropy of option (or 'all')"
			print "experts - count and list all experts"
		
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
				print("Invalid table name: " + str(table))
				
		if command == "experts":
			get_all_experts()
			
		if command == "freq all":
			freq_all()
		elif command.startswith("freq "):
			option = command[5:]
			try:
				c.execute(FREQ_COUNT_QUERY % (option,option,option))
				print(c.fetchall())
			except Exception as e:
				print("Invalid option: " + str(option))
				
		if command == "ent all":
			get_all_entropies()
		elif command.startswith("ent "):
			option = command[4:]
			try:
				c.execute(FREQ_COUNT_QUERY % (option,option,option))
				results = c.fetchall()
				# note that it returns (None,0) as result 0, I don't know why
				count_0 = results[1][1]
				count_1 = results[2][1]
				print(entropy(count_0, count_1))
			except Exception as e:
				print("Invalid option: " + str(option))
				
		if command.startswith("e "):
			com = command[2:]
			if not com.endswith(";"): # be nice to user, append ; if need be
				com = com + ";"
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
	parser.add_argument('-debug', action='store_true', help="Print debug info.")
	parser.add_argument('--test', action='store_true', help="Run test suite instead of I/O operations.")
	parser.add_argument('--quick', default="", help="Quick I/O command, e.g. 't' to list tables.")
	parser.add_argument('--execute', default="", help="Query to input.")
	args = parser.parse_args()
	
	import sqlite3
	conn = sqlite3.connect('folditx.db')
	c = conn.cursor()
	if args.test:
		test(args)
	else:
		io_mode(args)



