#! /usr/bin/python
from __future__ import division, print_function
from future.utils import iteritems
from collections import defaultdict

# Fix for Python 2.x
try: input = raw_input
except NameError: pass

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

MIN_HIGHSCORES_PER_EXPERT = 2
FREQ_COUNT_QUERY = '''select %s, count(%s) from options group by %s;'''
PIDS_BY_CAT = {}
ENTROPY_DICT = {}
EXPERTS = []

# For these options, there is a lot of missing data - replace missing with default value
MISSING_DEFAULTS = {
	"puzzle_dialog__show_beginner" : 0,
	"rank_popups": 1,
	"selection_mode": 0,
	"selection_mode__show_notes": 1,
	"tooltips": 1,
	"view_options__guide_pulse": 1,
	"view_options__show_backbone_issues": 0,
	"view_options__show_residue_burial": 0,
	"view_options__sym_chain_colors": 0,
}

BINARY_OPTIONS = [
	"advanced_mode",
	"electron_density_panel__backface_culling",
	"music",
	"puzzle_dialog__show_beginner",
	"puzzle_dialog__show_old",
	"rank_popups",
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
	"view_options__working_pulse_style",
]

CAT_OPTIONS = {
	"view_options__current_visor": ["AAColor", "AbegoColor", "CPK", "EnzDes", "Hydro", "Hydro/Score", "Hydro/Score+CPK", "Hydrophobic", "Ligand Specific", "Rainbow", "Score", "Score/Hydro", "Score/Hydro+CPK"],
	"view_options__render_style": ["Cartoon", "Cartoon Ligand", "Cartoon Thin", "Line", "Line+H", "Line+polarH", "Sphere", "Stick", "Stick+H", "Stick+polarH", "Trace Line", "Trace Tube"],
	"view_options__sidechain_mode": ["Don't Show (Fast)", "Show All (Slow)", "Show Stubs"]
}

FULL_OPTIONS_LIST = [
	"advanced_mode",
	"autoshow_chat__global",
	"autoshow_chat__group",
	"autoshow_chat__puzzle",
	"autoshow_chat__veteran",
	"autoshow_notifications",
	"chat__auto_reconnect",
	"chat__disable_non_group",
	"chat__enable_public_profanity_filter",
	"cleanup_temp_files",
	"electron_density_panel__alpha",
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
	"update_group",  # several options, but probably split into =="main" true or false
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
	"view_options__sym_chain_visible", # not enough valid data to make use of
	"view_options__working_pulse_style",
]

# --------------- TEST BED -------------------------
# place to run tests
def test(args):
	print("Beginning Tests...")
	# Tests go here

	#main_stats()
	#centroid_test()



	print("Done.")

# prints out number of missing entries for each option
# reads 2000 entries at a time
def count_missing():
	rows_counted = 0
	missing_dict = {}
	list_of_options = []
	for o in BINARY_OPTIONS:
		missing_dict[o] = 0
		list_of_options.append(o)
	for cat in CAT_OPTIONS:
		for o in CAT_OPTIONS[cat]:
			missing_dict[o] = 0
			list_of_options.append(o)
	views = query_to_views("limit 2000 offset " + str(rows_counted)) # whole db, iteratively
	while views is not None:
		ll = []
		for (id,view) in iteritems(views):
			ll.append(view_dict_to_list(view))
		for l in ll:
			for i in range(len(list_of_options)):
				if l[i] is None or l[i] == "None":
					missing_dict[list_of_options[i]] += 1
				if rows_counted % 2000 == 0 and l is ll[0]:
					if i == 0:
						print("\nRows counted = " + str(rows_counted))
					print(list_of_options[i] + ": " + str(missing_dict[list_of_options[i]]))
					if i >= len(list_of_options)-1:
						print("\nRows counted = " + str(rows_counted))
		rows_counted += 2000
		views = query_to_views("limit 2000 offset " + str(rows_counted)) # whole db, iteratively


def centroid_test():
	# Get total centroid
	views = query_to_views("limit 3") # whole db, TEST limit 3
	cluster = []
	for (id,view) in iteritems(views):
		cluster.append(view_dict_to_list(view))
	print("cluster:")
	print(cluster)
	print("Density stats:")
	print(density(cluster))
	print("Centroid:")
	print(list_to_view_dict(centroid(cluster)))

# ------------ END TEST BED -----------------------



# ------------ ONE TIME FUNCTIONS -----------------

# Calculate and print full report of interesting stats
def main_stats():
	pass

	# TODO apply filters

	# Cluster by expert/non, report clustering statistics

	# Cluster by high score / not, report clustering statistics

	# Cluster by puzzle category, report clustering statistics


def freq_all():
	for o in FULL_OPTIONS_LIST:
		try:
			c.execute(FREQ_COUNT_QUERY % (o,o,o))
			print(o.upper())
			print(c.fetchall())
		except Exception as e:
			print("Invalid option: " + str(o))

# Warning: This function takes 30+ minutes (haven't measured exactly, might be as much as 3 hours)
def get_all_experts():
	# get all users
	c.execute('''select distinct uid from rprp_puzzle_ranks''')
	users = c.fetchall()
	print("Identifying experts (This will take a while):")
	user_count = 0
	expert_dict = {}
	for user in users:
		user_count += 1
		num_hs = is_expert(user)
		if num_hs >= MIN_HIGHSCORES_PER_EXPERT:
			expert_dict[user[0]] = num_hs
			print('!',end='')
		if user_count % 5 == 0:
			print('.',end='')
		sys.stdout.flush()
	sorted_experts = sorted(expert_dict.items(), key=operator.itemgetter(1))
	with open('experts.csv', 'w') as expert_file:
		writer = csv.writer(expert_file)
		writer.writerows(sorted_experts)

def get_all_entropies(output=False):
	global ENTROPY_DICT
	ENTROPY_DICT = defaultdict(float)
	for o in BINARY_OPTIONS:
		try:
			c.execute(FREQ_COUNT_QUERY % (o,o,o))
			results = c.fetchall()
			# note that it returns (None,0) as result 0, I haven't figured out how to silence that
			count_0 = results[1][1]
			count_1 = results[2][1]
			ENTROPY_DICT[o] = entropy(count_0, count_1)
		except Exception as e:
			print("Invalid option: " + str(o))
	if output:
		sorted_dict = sorted(ENTROPY_DICT.items(), key=operator.itemgetter(1), reverse=True)
		for option, en in sorted_dict:
			print(option + ": " + str(en))

# ------------ CLEAN DATABASE -----------------

import datetime

def remove_error_entries():
	if args.debug:
		print("DEBUG: Removing entries with errors...")
	c.execute("select pid from options where error == 1")
	options_to_remove = [row[0] for row in c.fetchall()]
	for pid in options_to_remove:
		c.execute('''delete from options where pid == %d''' % pid)
	num_removed = len(options_to_remove)
	if args.debug:
		print("DEBUG: Removed " + str(num_removed) + " entries with errors from options")
	return num_removed


def remove_invalid_puzzle_ranks():
	if args.debug:
		print("DEBUG: Removing invalid puzzle rank entries...")
	c.execute("select pid from rprp_puzzle_ranks where is_valid == 0")
	ranks_to_remove = [row[0] for row in c.fetchall()]
	for pid in ranks_to_remove:
		c.execute('''delete from rprp_puzzle_ranks where pid == %d''' % pid)
	num_removed = len(ranks_to_remove)
	if args.debug:
		print("DEBUG: Removed " + str(num_removed) +
			  " entries from rprp_puzzle_ranks with invalid puzzle ranks")


def remove_beginner_puzzle_entries():
	if args.debug:
		print("DEBUG: Removing Beginner entries...")

	beginner_puzzles = map(int, PIDS_BY_CAT['Beginner'])

	beginner_puzzles_chunks = \
		[beginner_puzzles[i:i + 100] for i in range(0, len(beginner_puzzles), 100)]

	puzzles_to_remove = []
	ranks_to_remove = []
	options_to_remove = []

	for chunk in beginner_puzzles_chunks:

		str_chunk = str(tuple(chunk))

		c.execute('''select nid from rpnode__puzzle where nid IN %s''' % str_chunk)
		puzzles_to_remove += [row[0] for row in c.fetchall()]

		c.execute('''select pid from rprp_puzzle_ranks where pid IN %s''' % str_chunk)
		ranks_to_remove += [row[0] for row in c.fetchall()]

		c.execute('''select pid from options where pid IN %s''' % str_chunk)
		options_to_remove += [row[0] for row in c.fetchall()]

	num_puzzles_to_remove = len(puzzles_to_remove)
	num_ranks_to_remove = len(ranks_to_remove)
	num_options_to_remove = len(options_to_remove)

	puzzles_to_remove_chunks = \
		[puzzles_to_remove[i:i + 1000] for i in range(0, len(puzzles_to_remove), 1000)]

	ranks_to_remove_chunks = \
		[ranks_to_remove[i:i + 1000] for i in range(0, len(ranks_to_remove), 1000)]

	options_to_remove_chunks = \
		[options_to_remove[i:i + 1000] for i in range(0, len(options_to_remove), 1000)]

	if args.debug:
		print("DEBUG: Removing Beginner entries from rpnode__puzzle...")
	for chunk in puzzles_to_remove_chunks:
		c.execute('''delete from rpnode__puzzle where nid IN %s''' % str(tuple(chunk)))
	if args.debug:
		print("DEBUG: Removed " + str(num_puzzles_to_remove) + " entries from rpnode__puzzle for beginner puzzles")

	if args.debug:
		print("DEBUG: Removing Beginner entries from rprp_puzzle_ranks...")
	for chunk in ranks_to_remove_chunks:
		c.execute('''delete from rprp_puzzle_ranks where pid IN % s''' % str(tuple(chunk)))
	if args.debug:
		print("DEBUG: Removed " + str(num_ranks_to_remove) + " entries from rprp_puzzle_ranks for beginner puzzles")

	if args.debug:
		print("DEBUG: Removing Beginner entries from options...")
	for chunk in options_to_remove_chunks:
		c.execute('''delete from options where pid IN %s''' % str(tuple(chunk)))
	if args.debug:
		print("DEBUG: Removed " + str(num_options_to_remove) + " entries from options for beginner puzzles")

	return num_options_to_remove


def remove_intro_puzzle_entries():

	if args.debug:
		print("DEBUG: Removing Intro entries...")

	c.execute("select pid from rprp_puzzle_ranks where pid not in (select nid from rpnode__puzzle)")
	ranks_to_remove = [row[0] for row in c.fetchall()]

	c.execute("select pid from options where pid not in (select nid from rpnode__puzzle)")
	options_to_remove = [row[0] for row in c.fetchall()]

	num_ranks_to_remove = len(ranks_to_remove)
	num_options_to_remove = len(options_to_remove)

	ranks_to_remove_chunks = [ranks_to_remove[i:i + 100] for i in range(0, len(ranks_to_remove), 100)]

	options_to_remove_chunks = \
		[options_to_remove[i:i + 1000] for i in range(0, len(options_to_remove), 1000)]

	if args.debug:
		print("DEBUG: Removing Intro entries from rprp_puzzle_ranks...")
	for chunk in ranks_to_remove_chunks:
		c.execute('''delete from rprp_puzzle_ranks where pid IN %s''' % str(tuple(chunk)))

	if args.debug:
		print("DEBUG: Removing Intro entries from options...")
	for chunk in options_to_remove_chunks:
		c.execute('''delete from options where pid IN %s''' % str(tuple(chunk)))

	if args.debug:
		print("DEBUG: Removed " + str(num_ranks_to_remove) + " entries from rprp_puzzle_ranks for intro puzzles")
		print("DEBUG: Removed " + str(num_options_to_remove) + " entries from options for intro puzzles")

	return num_options_to_remove


def remove_major_missing_entries():

	if args.debug:
		print("DEBUG: Removing entries with major missing data...")

	all_options = BINARY_OPTIONS + CAT_OPTIONS.keys()
	sep = ","
	query_cols = sep.join(["uid", "pid", "time"] + all_options)

	missing_dict = {"total_entry_count": 0}

	for option in all_options:
		if option not in MISSING_DEFAULTS.keys():
			missing_dict[option] = 0

	c.execute('''select %s from options''' % query_cols)
	results = c.fetchall()

	for entry_idx in range(len(results)):

		num_major_options_missing = 0
		uid, pid, time = results[entry_idx][0:3]

		# for all options in the entry
		for o_index in range(len(results[entry_idx]) - 3):

			o_name = all_options[o_index]

			# if we expect to have data for this option but do not
			if o_name not in MISSING_DEFAULTS.keys():
				# increment counts for missing option in missing_dict
				if results[entry_idx][3 + o_index] is None:
					num_major_options_missing += 1
					missing_dict[o_name] += 1

		# remove entry from options table if it has any major options missing
		if num_major_options_missing > 0:
			missing_dict["total_entry_count"] += 1
			c.execute('''delete from options where uid = \"%s\" and pid == %d and time == %d''' % (uid, pid, time))

		return missing_dict


def replace_minor_missing_entries():

	if args.debug:
		print("DEBUG: Replacing minor missing data entries with default values...")

	replacement_dict = {"total_entry_count": 0}

	minor_options = MISSING_DEFAULTS.keys()

	for o_name in minor_options:
		replacement_dict[o_name] = 0

	sep = ","
	query_cols = sep.join(["uid", "pid", "time"] + minor_options)

	c.execute('''select %s from options''' % query_cols)
	results = c.fetchall()

	num_entries_updated = 0

	for entry_idx in range(len(results)):

		# names of minor options to update if they have missing values
		options_to_update = []

		# unique identifier cols for an entry
		uid, pid, time = results[entry_idx][0:3]

		# for all minor options in the entry
		for o_index in range(len(results[entry_idx]) - 3):
			if results[entry_idx][3 + o_index] is None:
				o_name = minor_options[o_index]
				options_to_update.append(o_name)

		# update minor options in entry is they had missing values
		if len(options_to_update) > 0:

			num_entries_updated += 1

			if num_entries_updated % 100 == 0:
				print("updated 100: " + str(datetime.datetime.now()))

			updated_options_values = [str(MISSING_DEFAULTS[o]) for o in options_to_update]

			update_query = ",".join(["=".join(a) for a in zip(options_to_update, updated_options_values)])

			c.execute('''update options set %s where uid = \"%s\" and pid == %d and time == %d'''
					  % (update_query, uid, pid, time))

	print("updated " + str(num_entries_updated) + " entries in options")
	print("end: " + str(datetime.datetime.now()))


def clean_db():
	print("INFO: Cleaning database (this may take a while)...")
	entries_removed = 0
	entries_removed += remove_error_entries()
	remove_invalid_puzzle_ranks() # doesn't remove any options entries
	entries_removed += remove_beginner_puzzle_entries()
	entries_removed += remove_intro_puzzle_entries()
	missing_dict = remove_major_missing_entries()
	entries_removed += missing_dict["total_entry_count"]
	print("INFO: Removed " + str(entries_removed) + " bad entries from options table.")
	if args.debug:
		print("DEBUG: Removed " + str(missing_dict["total_entry_count"]) + " entries with missing options data.")
		for option in missing_dict.keys():
			if option == "total_entry_count":
				continue
			print("DEBUG: Removed " + str(missing_dict[option]) + " entries because of " + str(option))
	# replace_minor_missing_entries()
	# conn.commit()
	
# ------------ END CLEAN DATABASE -----------------

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
	print("Imported " + str(len(PIDS_BY_CAT)) + " puzzle categories.")
	drop_cats = []
	for cat in PIDS_BY_CAT.keys():
		num_puz = len(PIDS_BY_CAT[cat])
		if args.debug:
			print("    " + cat + ": " + str(num_puz) + " puzzles")
		if num_puz < 10:
			if args.debug:
				print("    INFO: Dropping " + cat + " (too few puzzles)")
			drop_cats.append(cat)
	for cat in drop_cats:
		PIDS_BY_CAT.pop(cat, None)

def import_experts(recalculate=False):
	global EXPERTS
	if recalculate:
		get_all_experts()
	with open('experts.csv', 'r') as exp_file:
		reader = csv.reader(exp_file)
		for row in reader:
			EXPERTS.append(row[0])
	print("Imported " + str(len(EXPERTS)) + " experts.")

# -------- END ONE TIME FUNCTIONS -----------------




# -------- VIEW-BASED CALCULATIONS ----------------

# TODO how to deal with None data?
# Input: string of where queries for options table (e.g. "where uid=... and pid=....")
# For each result, create a view dict of bools representing each option, sorted by key
# Output: dict of views (dict of dicts, keys are unique ids = uid + pid + time (concatted))
def query_to_views(where):
	views = {} # dict of dicts, uniquely identified by uid, pid, and time
	for bin_opt in BINARY_OPTIONS:
		c.execute('''select uid, pid, time, %s from options %s''' % (bin_opt, where))
		results = c.fetchall()
		for result in results:
			unique_id = str(result[0]) + str(result[1]) + str(result[2])
			if unique_id not in views:
				views[unique_id] = {}
			view = views[unique_id]
			#if result[3] == "None" or result[3] is None: # TEST
			#	print(bin_opt)
			view[bin_opt] = result[3]
			views[unique_id] = view
	for cat_opt in CAT_OPTIONS.keys():
		c.execute('''select uid, pid, time, %s from options %s''' % (cat_opt, where))
		results = c.fetchall()
		for result in results:
			unique_id = str(result[0]) + str(result[1]) + str(result[2])
			if unique_id not in views:
				views[unique_id] = {}
			view = views[unique_id]
			for opt in CAT_OPTIONS[cat_opt]:
				if opt == result[3]:
					view[opt] = 1
				else:
					view[opt] = 0
			views[unique_id] = view
	return views

# Input: view dict from query_to_views
# Output: list of just the values in a sorted order to keep things consistent
def view_dict_to_list(view):
	list = []
	for bin_opt in BINARY_OPTIONS:
		list.append(view[bin_opt])
	for cat_opt in CAT_OPTIONS.keys():
		for opt in CAT_OPTIONS[cat_opt]:
			list.append(view[opt])
	return list

# TODO doesn't work if some of the dimensions were deleted during analysis
# The reverse of view_dict_to_list
# Input: list of just the view option values in a sorted order to keep things consistent
# Output: view dict as "option name": option value
def list_to_view_dict(list):
	view = {}
	for bin_opt in BINARY_OPTIONS:
		view[bin_opt] = list.pop(0)
	for cat_opt in CAT_OPTIONS.keys():
		for opt in CAT_OPTIONS[cat_opt]:
			view[opt] = list.pop(0)
	return view


# Returns true iff score is <= 5% of best scores for this puzzle
def is_highscore(pid, score):
	c.execute('''select distinct uid, best_score from rprp_puzzle_ranks where pid=%d group by uid order by best_score asc;''' % pid)
	# count entries, get the entry that's exactly 95th percentile, check our score vs that
	results = c.fetchall()
	num_scores = len(results)
	index = min(int(math.ceil(num_scores*0.05)), len(results)-1) # prevent index out of range error
	min_score = results[index][1]
	return score <= min_score

# Returns number of high scores in puzzles
def is_expert(uid):
	# get list of their best scores for each puzzle
	# count is_highscore
	c.execute('''select pid, best_score from rprp_puzzle_ranks where uid=\"%s\" group by pid order by best_score asc;''' % uid)
	results = c.fetchall()
	num_highscores = 0
	for result in results:
		if is_highscore(result[0], result[1]):
			num_highscores += 1
	return num_highscores # TODO change to bool


# calculates the similarity between two views - Euclidean distance
# assumes views are a vector of interval variables
def distance(view1, view2):
	dist = [(a - b)**2 for a, b in zip(view1, view2)]
	return math.sqrt(sum(dist)) # apparently this method is faster than external lib methods


# TODO
# Input: a full vector of view data that can correspond somehow to known values of entropy for each attr
# Output: the vector of data, elementwise multiplied by (1-entropy)
def apply_inverse_entropy_weighting(view):
	pass

# calculates the density of a cluster - i.e., the mean similarity between every view and every other view
# returns mean and std
# if dims option is set, calculates density only for specific dimension(s)
# O(n^2) algorithm
def density(cluster, dims=[-1]):
	distances = []
	for i in range(len(cluster)):
		for j in range(len(cluster)):
			if i != j:
				if dims == [-1]:
					distances.append(distance(cluster[i], cluster[j]))
				else:
					d_i = []
					d_j = []
					for d in dims:
						if d > len(cluster[0])-1 or d < 0:
							raise IndexError("Tried to calculate density of a cluster on an invalid dimension")
						else:
							d_i.append(cluster[i][d])
							d_j.append(cluster[j][d])
					distances.append(distance(d_i, d_j))

	mean = numpy.mean(distances)
	std = numpy.std(distances)
	return mean,std

# TODO maybe there should be some way to specify dims by human-readable option (for this and density function)
# returns the centroid of a cluster
# if dims option is set, calculates for only specific dimension(s)
def centroid(clus, dims=[-1]):
	if dims != [-1]:
		cluster = numpy.delete(clus, dims, axis=1)
	return numpy.mean(cluster)


# returns the entropy for a binary var
def entropy(count_0, count_1):
	p = count_1 / (count_0 + count_1)
	return -(p * math.log(p,2)) - (1 - p) * math.log(1-p,2)

# -------- END VIEW-BASED CALCULATIONS -------------




# ----------------- MAIN ---------------------------

def io_mode(args):
	single_query = args.execute != '' or args.quick != ''
	command = ''
	if args.execute:
		command = "e " + args.execute
	if args.quick:
		command = args.quick
	while (command != 'q' and command != 'exit'):
		command = command.lower()

		if command == 'h':

			print("h - help")
			print("q - quit")
			print("t - list tables") # options, rpnode__puzzle, sqlite_sequence, rprp_puzzle_ranks
			print("c [table] - list columns in table")
			print("e [command] - execute command")
			print("freq [option] - count values of an option (or 'all')")
			print("ent [option] - get entropy of option (or 'all')")
			print("experts - count and list all experts")

		if command == 't':
			c.execute('''SELECT name from sqlite_master where type = 'table'; ''')
			for t in c.fetchall():
				print(t[0])

		if command.startswith("c "):
			table = command[2:]
			try:
				c.execute('''SELECT * from %s;''' % table)
				for info in c.description:
					print(info[0])
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
			get_all_entropies(output=True)
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
			print("Enter command (h for help): ")
			command = input("> ")
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
	parser.add_argument('--execute', default="", help="Run a single SQL query.")
	args = parser.parse_args()

	print("Loading modules and data...")
	import math, operator, csv, sys, numpy, sqlite3

	# import scikit, pandas, and/or oranges?
	global conn
	conn = sqlite3.connect('folditx.db')
	global c
	c = conn.cursor()
	import_categories()
	import_experts(recalculate=False)
	clean_db()

print("...Loaded.")

if args.test:
	test(args)
else:
	io_mode(args)
