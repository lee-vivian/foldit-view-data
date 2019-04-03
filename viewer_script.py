#! /usr/bin/python
from __future__ import division, print_function
from future.utils import iteritems
from collections import defaultdict


# Fix for Python 2.x
try: input = raw_input
except NameError: pass

try: from StringIO import StringIO
except ImportError: from io import StringIO

ENTROPIES_FILE = "entropies.csv"
FREQUENCIES_FILE = "frequencies.csv"
EXPERTS_FILE = "experts.csv"
MIN_HIGHSCORES_PER_EXPERT = 2


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

FREQ_COUNT_QUERY = '''select %s, count(%s) from options group by %s;'''
PIDS_BY_CAT = {}
ENTROPY_DICT = {}
OPT_FREQ_DICT = {}
EXPERTS = []

# For these options, there is a lot of missing data - replace missing with default value
MISSING_DEFAULTS = {
	"puzzle_dialog__show_beginner": 0,
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
	centroid_stats("limit 1000")
	centroid_stats("where is_highscore == 1")
	centroid_stats("where is_highscore == 0")
	centroid_stats("where is_expert == 0")
	centroid_stats("where is_expert == 1")
	centroid_stats("")

	print("freq test")
	# test apply_inverse_frequency_weighting()
	views = query_to_views("limit 1")
	weighted_views = dict()
	for id, view in views.iteritems():
		weighted_view = apply_inverse_frequency_weighting(view)
		weighted_views[id] = weighted_view
	print(weighted_views)
		
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


# Report stats for a centroid described by a where query
def centroid_stats(where):
	# Get total centroid
	views = query_to_views(where)
	cluster = []
	for (id,view) in iteritems(views):
		cluster.append(view_dict_to_list(view))
	unicode_clean(cluster)
	print("Analyzing this centroid: " + where)
	print("Density:")
	print(density(cluster))
	print("Centroid:")
	print(centroid(cluster))


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


def update_dictionary_apply_fn_options_freq(dictionary, fn):

	for o in BINARY_OPTIONS:
		try:
			c.execute(FREQ_COUNT_QUERY % (o,o,o))
			results = c.fetchall()
			# note that it returns (None,0) as result 0, I haven't figured out how to silence that
			count_0 = results[0][1]
			count_1 = results[1][1]
			dictionary[o] = fn(count_0, count_1)
		except Exception as e:
			print(e)
			print("Invalid option: " + str(o))

	# create dictionary for binarized cat options for each unique entry in options (uid + pid + time)
	# {unique id : {cat_option_val : bool}}
	binarized_cat_options_dict = query_binarize_cat_to_dict("", {})

	cat_options_dict_per_unique_id = binarized_cat_options_dict.values()

	num_unique_ids = len(binarized_cat_options_dict.keys())

	all_cat_option_values = cat_options_dict_per_unique_id[0].keys()

	for v in all_cat_option_values:
		count_1 = sum([d[v] for d in cat_options_dict_per_unique_id])
		count_0 = num_unique_ids - count_1

		dictionary[v] = fn(count_0, count_1)

	return dictionary

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
		num_hs = count_expertise(user)
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
	if not is_db_clean:
		raise Exception("Database must be clean to run get_all_entropies")
	global ENTROPY_DICT
	ENTROPY_DICT = defaultdict(float)

	update_dictionary_apply_fn_options_freq(ENTROPY_DICT, entropy)

	if output:
		sorted_dict = sorted(ENTROPY_DICT.items(), key=operator.itemgetter(1), reverse=True)
		for option, en in sorted_dict:
			print(option + "," + str(en))


def get_all_freq_binarized_options(output=False):
	if not is_db_clean:
		raise Exception("Database must be clean to run get_all_freq_binarized_options")
	global OPT_FREQ_DICT
	OPT_FREQ_DICT = defaultdict(float)
	update_dictionary_apply_fn_options_freq(OPT_FREQ_DICT, true_frequency)
	if output:
		sorted_dict = sorted(OPT_FREQ_DICT.items(), key=operator.itemgetter(1), reverse=True)
		for option, freq in sorted_dict:
			print(option + "," + str(freq))


# Add is_highscore col to rprp_puzzle_ranks table
def add_is_highscore_col():

	try:
		c.execute("ALTER TABLE rprp_puzzle_ranks ADD is_highscore INT DEFAULT -1 NOT NULL")
		print("INFO: Created is_highscore column in rprp_puzzle_ranks. Calculating is_highscore ...")
	except Exception as e:
		print("INFO: is_highscore column already exists in rprp_puzzle_ranks. Recalculating is_highscore...")

	# dictionary that maps pid to score at the 95th percentile for the puzzle
	pid_highscore = {}

	c.execute('''select distinct pid from rprp_puzzle_ranks''')
	results = c.fetchall()
	puzzle_ids = [result[0] for result in results]

	for pid in puzzle_ids:
		pid_highscore[pid] = get_highscore(pid)

	for pid in pid_highscore.keys():
		highscore = pid_highscore[pid]
		c.execute('''update rprp_puzzle_ranks set is_highscore = 0 where pid == %d and best_score > %d'''
				  % (pid, highscore))
		c.execute('''update rprp_puzzle_ranks set is_highscore = 1 where pid == %d and best_score <= %d'''
				  % (pid, highscore))

	conn.commit()


# Add is_expert col to rprp_puzzle_ranks table
def add_is_expert_col():
	try:
		c.execute("ALTER TABLE rprp_puzzle_ranks ADD is_expert INT DEFAULT 0 NOT NULL")
		print("INFO: Created is_expert column in rprp_puzzle_ranks. Calculating is_expert ...")
	except Exception as e:
		print("INFO: is_expert column already exists in rprp_puzzle_ranks. Recalculating is_expert...")

	# Get list of experts
	if not os.path.isfile(EXPERTS_FILE):
		raise Exception("ERR: Experts file not found: " + EXPERTS_FILE)
	experts_list = []
	with open(EXPERTS_FILE, 'r') as experts_file:
		reader = csv.reader(experts_file)
		for row in reader:
			experts_list.append(row[0])
	c.execute('''update rprp_puzzle_ranks set is_expert = 1 where uid in %s''' % str(tuple(experts_list)))
	conn.commit()


# ------------ WRITE TO CSV FUNCTIONS -----------------

# Input: a list of dictionaries of {column name : val} for each entry in the desired table
# to create, the name of the csv file to create
# Output: creates a csv file from the given dictionary data
def write_csv_from_dict(dict_data, name):
	csv_file_name = name
	csv_columns = dict_data[0].keys()
	try:
		with open(csv_file_name, 'w') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
			writer.writeheader()
			for data in dict_data:
				writer.writerow(data)
	except IOError:
		raise Exception("I/O error")


# Input: where query for query_to_views
# Output: creates a csv file for the options data containing relevant columns for
# viewing/visualization and hierarchical clustering
def write_options_csv(where):
	test_write_options_csv(where) # TEST
	return

	options_views_dicts = query_to_views(where)
	options_csv_dict = {}

	c.execute('''select uid, pid, time from options %s''' % where)
	results = c.fetchall()

	for result in results:
		uid = result[0]
		pid = result[1]
		time = result[2]
		unique_id = str(uid) + str(pid) + str(time)
		options_csv_dict[unique_id] = {"uid": uid, "pid": pid, "time": time}
		options_csv_dict[unique_id].update(options_views_dicts[unique_id])

	dict_data = options_csv_dict.values()
	write_csv_from_dict(dict_data, "options_view.csv")
	print("Created options_view csv")
	
def test_write_options_csv(where):
	#cat_opts = []
	#for cat in CAT_OPTIONS.keys():
	#	for o in CAT_OPTIONS[cat]
	#		cat_opts.append(o)
	options_list = ','.join(BINARY_OPTIONS) # + cat_opts)
	print("Options list test: " + options_list)
	c.execute('''select %s from options''' % options_list)
	results = c.fetchall()
	with open('test_csv.csv', 'w') as testfile:
		writer = csv.writer(testfile)
		writer.writerow(BINARY_OPTIONS)
		for r in results:
			writer.writerow(r)
	


# ------------ CLEAN DATABASE -----------------


def remove_error_entries():
	print("INFO: Removing entries with errors...")
	c.execute("select pid from options where error == 1")
	options_to_remove = [row[0] for row in c.fetchall()]
	for pid in options_to_remove:
		c.execute('''delete from options where pid == %d''' % pid)
	num_removed = len(options_to_remove)
	print("INFO: Removed " + str(num_removed) + " entries with errors from options")
	return num_removed


def remove_invalid_puzzle_ranks():
	print("INFO: Removing invalid puzzle rank entries...")
	c.execute("select pid from rprp_puzzle_ranks where is_valid == 0")
	ranks_to_remove = [row[0] for row in c.fetchall()]
	for pid in ranks_to_remove:
		c.execute('''delete from rprp_puzzle_ranks where pid == %d''' % pid)
	num_removed = len(ranks_to_remove)
	print("INFO: Removed " + str(num_removed) +
			  " entries from rprp_puzzle_ranks with invalid puzzle ranks")


def remove_beginner_puzzle_entries():
	print("INFO: Removing Beginner entries...")

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

	print("INFO: Removing Beginner entries from rpnode__puzzle...")
	for chunk in puzzles_to_remove_chunks:
		c.execute('''delete from rpnode__puzzle where nid IN %s''' % str(tuple(chunk)))
	print("INFO: Removed " + str(num_puzzles_to_remove) + " entries from rpnode__puzzle for beginner puzzles")

	print("INFO: Removing Beginner entries from rprp_puzzle_ranks...")
	for chunk in ranks_to_remove_chunks:
		c.execute('''delete from rprp_puzzle_ranks where pid IN % s''' % str(tuple(chunk)))
	print("INFO: Removed " + str(num_ranks_to_remove) + " entries from rprp_puzzle_ranks for beginner puzzles")

	print("INFO: Removing Beginner entries from options...")
	for chunk in options_to_remove_chunks:
		c.execute('''delete from options where pid IN %s''' % str(tuple(chunk)))
	print("INFO: Removed " + str(num_options_to_remove) + " entries from options for beginner puzzles")

	return num_options_to_remove


def remove_intro_puzzle_entries():

	print("INFO: Removing Intro entries...")

	c.execute("select pid from rprp_puzzle_ranks where pid not in (select nid from rpnode__puzzle)")
	ranks_to_remove = [row[0] for row in c.fetchall()]

	c.execute("select pid from options where pid not in (select nid from rpnode__puzzle)")
	options_to_remove = [row[0] for row in c.fetchall()]

	num_ranks_to_remove = len(ranks_to_remove)
	num_options_to_remove = len(options_to_remove)

	ranks_to_remove_chunks = [ranks_to_remove[i:i + 100] for i in range(0, len(ranks_to_remove), 100)]

	options_to_remove_chunks = \
		[options_to_remove[i:i + 1000] for i in range(0, len(options_to_remove), 1000)]

	print("INFO: Removing Intro entries from rprp_puzzle_ranks...")
	for chunk in ranks_to_remove_chunks:
		c.execute('''delete from rprp_puzzle_ranks where pid IN %s''' % str(tuple(chunk)))
	print("INFO: Removed " + str(num_ranks_to_remove) + " entries from rprp_puzzle_ranks for intro puzzles")


	print("INFO: Removing Intro entries from options...")
	for chunk in options_to_remove_chunks:
		c.execute('''delete from options where pid IN %s''' % str(tuple(chunk)))
	print("INFO: Removed " + str(num_options_to_remove) + " entries from options for intro puzzles")

	return num_options_to_remove


def remove_major_missing_entries():

	print("INFO: Removing entries with major missing data...")

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
	print("INFO: Replacing minor missing data entries with default values...")
	for option in MISSING_DEFAULTS.keys():
		# count / sanity check
		c.execute('''select %s from options where %s is NULL ''' % (option, option))
		results = c.fetchall()
		print("Replaced " + str(len(results)) + " missing entries for " + str(option) + " with default value")
		c.execute('''update options set %s = %d where %s is NULL ''' % (option, MISSING_DEFAULTS[option], option))


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
	print("INFO: Removed " + str(missing_dict["total_entry_count"]) + " entries with missing options data.")
	for option in missing_dict.keys():
		if option == "total_entry_count":
			continue
		print("INFO: Found " + str(missing_dict[option]) + " entries with missing " + str(option))
	replace_minor_missing_entries()
	conn.commit()
	print("INFO: Databased cleaned.")

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

	# add CAT options to views dict
	views = query_binarize_cat_to_dict(where, views)

	return views


# Input: string of where queries for options table (e.g. "where uid=... and pid=....") and
#        a dict of bools for options, sorted by key {unique_id : {option : bool}}
# For each result, add to the given dict of bools each categorical option, sorted by key
# Output: updated dict (dict of dicts, keys are unique ids = uid + pid + time (concatted))
def query_binarize_cat_to_dict(where, dictionary):

	for cat_opt in CAT_OPTIONS.keys():
		c.execute('''select uid, pid, time, %s from options %s''' % (cat_opt, where))
		results = c.fetchall()
		for result in results:
			unique_id = str(result[0]) + str(result[1]) + str(result[2])
			if unique_id not in dictionary:
				dictionary[unique_id] = {}
			dict_entry = dictionary[unique_id]
			for opt in CAT_OPTIONS[cat_opt]:
				if opt == result[3]:
					dict_entry[opt] = 1
				else:
					dict_entry[opt] = 0
			dictionary[unique_id] = dict_entry

	return dictionary


# convert unicode to ints, the hardcoded way
def unicode_clean(cluster):
	for i in range(len(cluster)):
		for j in range(len(cluster[i])):
			if cluster[i][j] == u'0':
				cluster[i][j] = 0
			elif cluster[i][j] == u'1':
				cluster[i][j] = 1
	return cluster

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
	# get the score of the entry that's exactly 95th percentile, check our score vs that
	min_score = get_highscore(pid)
	return score <= min_score


# Returns score threshold for pid to be in top 5% of best scores for the puzzle
def get_highscore(pid):
	c.execute(
		'''select distinct uid, best_score from rprp_puzzle_ranks where pid=%d group by uid order by best_score asc;''' % pid)
	# count entries, get the entry that's exactly 95th percentile
	results = c.fetchall()
	num_scores = len(results)
	index = min(int(math.ceil(num_scores * 0.05)), len(results) - 1)  # prevent index out of range error
	min_score = results[index][1]
	return min_score


# Returns number of high scores in puzzles
def count_expertise(uid):
	# get list of their best scores for each puzzle
	# count is_highscore
	has_hs_column = True
	try:
		c.execute('''select pid, best_score, is_highscore from rprp_puzzle_ranks where uid=\"%s\" group by pid order by best_score asc;''' % uid)
	except:
		print("WARN: no is_highscore column available")
		has_hs_column = False
		c.execute('''select pid, best_score from rprp_puzzle_ranks where uid=\"%s\" group by pid order by best_score asc;''' % uid)
	results = c.fetchall()
	num_highscores = 0
	for result in results:
		if has_hs_column:
			if result[2] == 1:
				num_highscores += 1
		elif is_highscore(result[0], result[1]):
			num_highscores += 1
	return num_highscores


# calculates the similarity between two views - Euclidean distance
# assumes views are a vector of interval variables
def distance(view1, view2):
	dist = [(a - b)**2 for a, b in zip(view1, view2)]
	return math.sqrt(sum(dist)) # apparently this method is faster than external lib methods


# Input: a View dict
# Output: the View Dict, elementwise multiplied by (1-frequency)
def apply_inverse_frequency_weighting(view):
	if not os.path.isfile(FREQUENCIES_FILE):
		raise Exception("ERR: Frequency file not found: " + FREQUENCIES_FILE)
	freq_dict = {}
	# Read in the frequencies file
	with open(FREQUENCIES_FILE, 'r') as frequencies_file:
		reader = csv.reader(frequencies_file)
		for row in reader:
			freq_dict[row[0]] = row[1]

	for opt in view.keys():
		try:
			option_val = int(view[opt])
			multiplier = -1 if option_val == 0 else 1
			view[opt] = multiplier * (1.0 - float(freq_dict[opt]))
		except KeyError as e:
			print("WARN: No frequency found in " + FREQUENCIES_FILE + " for option: " + opt)
	if args.debug: # TODO remove after testing
		print("DEBUG: Applied inverse frequency weighting. View is now:")
		print(view)
	return view

# calculates the density of a cluster - i.e., the mean similarity between every view and every other view
# returns mean and std
# if dims option is set, calculates density only for specific dimension(s)
# O(n^2) algorithm

#def density(cluster, dims=[-1]):
#	distances = []
#	for i in range(len(cluster)):
#		for j in range(len(cluster)):
#			if i != j:
#				if dims == [-1]:
#					distances.append(distance(cluster[i], cluster[j]))
#				else:
#					d_i = []
#					d_j = []
#					for d in dims:
#						if d > len(cluster[0])-1 or d < 0:
#							raise IndexError("Tried to calculate density of a cluster on an invalid dimension")
#						else:
#							d_i.append(cluster[i][d])
#							d_j.append(cluster[j][d])
#					distances.append(distance(d_i, d_j))
#	mean = numpy.mean(distances)
#	std = numpy.std(distances)
#	return mean,std

# Return an array of standard deviations for each dimension in the cluster
def density(cluster, dims=[-1]):
	stds = []
	for i in range(len(cluster)):
		if dims==[-1] or i in dims:
			stds.append(numpy.std([view[0] for view in cluster]))
	return stds
	


# TODO maybe there should be some way to specify dims by human-readable option (for this and density function)
# returns the centroid of a cluster
# if dims option is set, calculates for only specific dimension(s)
def centroid(clus, dims=[-1]):
	cluster = clus
	if dims != [-1]:
		cluster = numpy.delete(cluster, dims, axis=1)
	return numpy.mean(cluster, axis=0).tolist()


# returns the entropy for a binary var
def entropy(count_0, count_1):
	p = count_1 / (count_0 + count_1)

	# math.log(0,2) will raise a value error, taken to be 0.0 instead
	if p == 0.0 or p == 1.0:
		return 0.0

	return -(p * math.log(p,2)) - (1 - p) * math.log(1-p,2)


# returns frequency of true for a binary var
def true_frequency(count_0, count_1):
	return (count_1 * 1.0) / (count_0 + count_1)

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
			print("clean - clean the database of bad entries")
			print("process - add new data to database, e.g. highscore info, is expert info")
			print("csv options - write options table to csv")

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
		elif command == "binarized freq all":
			get_all_freq_binarized_options(output=True)
		elif command.startswith("freq "):
			option = command[5:]
			try:
				c.execute(FREQ_COUNT_QUERY % (option,option,option))
				print(c.fetchall())
			except Exception as e:
				print("Invalid option: " + str(option))

		if command == "clean":
			clean_db()

		if command == "csv options":
			write_options_csv("")

		if command == "ent all":
			get_all_entropies(output=True)
		elif command.startswith("ent "):
			if not is_db_clean:
				raise Exception("Database must be clean to get entropies")
			option = command[4:]
			try:
				c.execute(FREQ_COUNT_QUERY % (option,option,option))
				results = c.fetchall()
				# note that it returns (None,0) as result 0, I don't know why
				count_0 = results[0][1]
				count_1 = results[1][1]
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

		if command == "process":
			print("INFO: Processing data:")
			add_is_highscore_col()
			add_is_expert_col()

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
	import math, operator, csv, sys, numpy, sqlite3, datetime, os.path, cProfile, pstats
	# import scikit, pandas, and/or oranges?

	global conn, is_db_clean
	is_db_clean = False
	if os.path.isfile('foldit_clean.db'):
		conn = sqlite3.connect('foldit_clean.db')
		is_db_clean = True
		print("INFO: Found clean database: foldit_clean.db")
	elif os.path.isfile('folditx.db'):
		conn = sqlite3.connect('folditx.db')
		print("WARN: Database is not clean. Use the --quick clean command and save database as foldit_clean.db")
	else:
		print("ERR: No database found with name folditx.db or foldit_clean.db")
		exit(1)
	global c
	c = conn.cursor()
	import_categories()
	import_experts(recalculate=False)

print("...Loaded.")

# TEST
# pr = cProfile.Profile()
# pr.enable()
# test(args)
# pr.disable()
# s = StringIO.StringIO()
# sortby = 'cumulative'
# ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
# ps.print_stats()
# print(s.getvalue())

if args.test:
	test(args)
else:
	io_mode(args)
