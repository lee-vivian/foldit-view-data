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

OPTIONS_LIST = [
advanced_mode
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
	"macro__examples_loaded", 
	"macro__gui__flyout_font_size", 
	"macro__hint__block_aciton_quick_save", 
	"macro__hint__block_action_band", 
	"macro__hint__block_action_behavior", 
	"macro__hint__block_action_disable", 
	"macro__hint__block_action_enable", 
	"macro__hint__block_action_localwiggle", 
	"macro__hint__block_action_lock", 
	"macro__hint__block_action_mutate_all", 
	"macro__hint__block_action_quick_load", 
	"macro__hint__block_action_remove", 
	"macro__hint__block_action_reset_puzzle", 
	"macro__hint__block_action_reset_recent_best", 
	"macro__hint__block_action_residues_by_stride", 
	"macro__hint__block_action_restore_absolute_best", 
	"macro__hint__block_action_restore_recent_best", 
	"macro__hint__block_action_set_amino_acid", 
	"macro__hint__block_action_set_secondary_structure", 
	"macro__hint__block_action_set_strength", 
	"macro__hint__block_action_shake", 
	"macro__hint__block_action_unlock", 
	"macro__hint__block_action_wiggle", 
	"macro__hint__block_add", 
	"macro__hint__cookbook_list", 
	"macro__hint__open_cookbook", 
	"macro__hint__red_dashed_box", 
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
	"switch_residue_colors - colorblind mode", 
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

def clean_db():
	for o in OPTIONS_LIST:
		# c.execute( # TODO, remove unicode

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



