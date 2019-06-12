#! /usr/bin/python3
from __future__ import division, print_function
from collections import defaultdict
from sklearn.cluster import AgglomerativeClustering


# Python 2.x deprecated
# try:input = raw_input
# except NameError: pass
# try: from StringIO import StringIO
# except ImportError: from io import StringIO
# try: from future.utils import iteritems
# except ModuleNotFoundError: pass

GROUP_FOLDER = "groupuser_stats"
ENTROPIES_FILE = "entropies.csv"
FREQUENCIES_FILE = "frequencies.csv"
EXPERTS_FILE = "experts.csv"
MIN_HIGHSCORES_PER_EXPERT = 2
MIN_SAMPLES_PER_GROUP = 100
UID_LENGTH = 33
PID_LENGTH = 7


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

META_CATEGORIES = ["Design", "Prediction", "Electron Density", "Hand-Folding"]

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

CAT_KEYS = ["view_options__current_visor", "view_options__render_style", "view_options__sidechain_mode"]

CAT_OPTIONS = {
	"view_options__current_visor": ["AAColor", "AbegoColor", "CPK", "EnzDes", "Hydro", "Hydro/Score", "Hydro/Score+CPK", "Hydrophobic", "Ligand Specific", "Rainbow", "Score", "Score/Hydro", "Score/Hydro+CPK"],
	"view_options__render_style": ["Cartoon", "Cartoon Ligand", "Cartoon Thin", "Line", "Line+H", "Line+polarH", "Sphere", "Stick", "Stick+H", "Stick+polarH", "Trace Line", "Trace Tube"],
	"view_options__sidechain_mode": ["Don't Show (Fast)", "Show All (Slow)", "Show Stubs"]
}

ALL_USED_OPTIONS = [opt for opt in BINARY_OPTIONS]
for cat_opt in CAT_KEYS:
	for opt in CAT_OPTIONS[cat_opt]:
		ALL_USED_OPTIONS.append(opt)
		
TOTAL_DIMS = len(ALL_USED_OPTIONS)
				
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
	
	#sse_plot(weighted=True)	
	#cluster_plot("", "dendro_all_unique_6.png", weighted=False) # only need to run once, can comment out after
	# cluster mapping is now saved to clusters.csv
	
	clusters = {} # view : cluster
	with open("clusters.csv", 'r') as f:
		reader = csv.reader(f)
		next(reader) # skip header
		for row in reader:
			clusters[row[1]] = row[0]
	
	chi_square_analysis(clusters)
	#puzzle_type_analysis(clusters)
	group_cluster_analysis(clusters, nongroup=False)
	group_cluster_analysis(clusters, nongroup=True)
		
	print("Done.")
	
def count_results(where):
	c.execute('''select count(*) from options %s''' % where)
	results = c.fetchall()
	return results[0][0]
	
def chi_square_analysis(clusters):
	
	print("CQA: getting all dists")
	expert_dist = sum_view_dists_by_user(clusters, query_to_views('''where is_expert == 1'''))
	print("DEBUG: expert dist is:")
	print(expert_dist)
	
	nonexpert_dist = sum_view_dists_by_user(clusters, query_to_views('''where is_expert == 0 order by random() limit %d''' % count_results('''where is_expert == 1''')))
	#nonhs_dist = sum_view_dists_by_user(clusters, query_to_views('''where best_score_is_hs == 0 order by random() limit %d''' % len(hs_views)))
	#hs_dist = sum_view_dists_by_user(clusters, query_to_views('''where best_score_is_hs == 1'''))


	cat_expert_dists = []
	cat_nonexpert_dists = []
	#cat_hs_dists = []
	#cat_nonhs_dists = []
	for cat in META_CATEGORIES:
		print("CQA: getting all queries by " + str(cat))
		cat_expert_dists.append(sum_view_dists_by_user(clusters, query_to_views('''where is_expert == 1 and instr(puzzle_cat, \"%s\")''' % cat)))
		cat_nonexpert_dists.append(sum_view_dists_by_user(clusters, query_to_views('''where is_expert == 0 and instr(puzzle_cat, \"%s\") order by random() limit %d''' % (cat,count_results('''where is_expert == 1 and instr(puzzle_cat, \"%s\")''' % cat)))))

		# todo similalry for hs / nonhs


	print("CQA: doing analysis")
	chi_sq("expertise_main", expert_dist, nonexpert_dist)
	#chi_sq("hs_main", hs_dist, nonhs_dist)
	chi_sq("expertise_bycat", cat_expert_dists, cat_nonexpert_dists)
	#chi_sq("hs_bycat", cat_hs_dists, cat_nonhs_dists)
	
	
	print("CQA: vs null")
	null_expert = create_null_hypothesis_table(cat_expert_dists)
	null_nonexpert = create_null_hypothesis_table(cat_nonexpert_dists)
	#null_hs = create_null_hypothesis_table(cat_hs_dists)
	#null_nonhs = create_null_hypothesis_table(cat_nonhs_dists)
	chi_sq("catvsnull_expert", cat_expert_dists, null_expert)
	chi_sq("catvsnull_nonexpert", cat_nonexpert_dists, null_nonexpert)
	#chi_sq("catvsnull_hs", cat_hs_dists, null_hs)
	#chi_sq("catvsnull_nonhs", cat_nonhs_dists, null_nonhs)
	
# input: a num_categories x num_clusters table of view distributions
# output: what that table would look like if num_categories didn't affect distribution
def create_null_hypothesis_table(table):
	new_table = [row[:] for row in table] # copy
	for col in range(len(new_table[0])): # table[row][col
		column = []
		for row in range(len(new_table)):
			column.append(new_table[row][col])
		mean = numpy.mean(column)
		for row in range(len(new_table)):
			new_table[row][col] = mean
	print("null hypo table test:")
	print("original table:")
	print(table)
	print("new table:")
	print(new_table)
	return new_table
	
# no extension
def chi_sq(filename, table1, table2):
	import pickle
	pickle.dump(table1, open(filename + "1.p", 'wb'))
	pickle.dump(table1, open(filename + "2.p", 'wb'))
	with open(filename + '.txt', 'w') as f:
		chi_sq, p = stats.chisquare(table1, table2)
		f.write("X^2=" + str(chi_sq))
		f.write("\np=" + str(p))
	
def query_to_keys(where):
	c.execute('''select distinct uid, pid from rprp_puzzle_ranks ''' + where)
	keys = set([])
	for result in c.fetchall():
		uid = result[0]
		pid = result[1]
		#time = result[2]
		unique_id = str(uid) + str(pid) #+ str(time)
		keys.add(unique_id)
	return keys
	# if not getviews:
		# return keys
	# else:
		# views = query_to_views(where)
		# num_keys = str(len(keys))
		# for id in sorted(list(views)):			
			# if any(id.startswith(sub_key) for sub_key in keys):
				# #print("\r" + str(len(views)) + "/" + num_keys, end='', flush=True)
				# continue
			# else:
				# del views[id]
		# return views
		
def sum_view_dists_by_user(cluster_mapping, views):
	counter = [0, len(views)]
	current_user = ""
	users_views = {}
	dist = [0.0] * 6
	for key in sorted(views):
		counter[0] += 1
		print('\r' + str(counter[0]) + '/' + str(counter[1]), end='', flush=True)
		if current_user == key_to_uid(key): # still on same user, append
			users_views[key] = views[key]
		else: # switch users, flush out and start over
			if users_views != {}:
				view_distribution = views_to_normalized_cluster_distribution(users_views, cluster_mapping)
				dist = [sum(x) for x in zip(view_distribution, dist)] # add
			current_user = key_to_uid(key)
			user_views = {}
				
	return dist

	
# ------------------------------------------------------------

def views_to_normalized_cluster_distribution(views, cluster_mapping, num_clusters=6):
	view_distribution = [0.0] * num_clusters
	if len(views) == 0: # short-circuit for no views
		return view_distribution
		
	for (id,view) in views.items():
		list = view_dict_to_list(view)
		list_clean(list)
		view_string = view_list_to_string(list)
		cluster = cluster_mapping[view_string]
		view_distribution[int(cluster)] += 1
	
	# normalize
	scale = numpy.sum(view_distribution)
	for i in range(len(view_distribution)):
		view_distribution[i] /= scale
		
	return view_distribution
	
def puzzle_type_analysis(cluster_mapping, num_clusters=6):
	shannons = []
	counter = [0, len(META_CATEGORIES)]
	shannon_file = "puzzle_type_shannons.csv"
	
	with open(shannon_file, 'w') as pt_file:
		writer = csv.writer(pt_file)
		writer.writerow(["type", "users", "experts", "shannon"])
		for cat in META_CATEGORIES:
			print("Analysis on " + str(cat))
			cat_dist = [0] * num_clusters
			views = query_to_views('''where instr(puzzle_cat, \"%s\"); ''' % cat)
			num_experts = 0
			counter = [0, len(views)]
			current_user = ""
			users_views = {}
			for (key, list) in sorted(views):
				counter[0] += 1
				print('\r' + str(counter[0]) + '/' + str(counter[1]), end='', flush=True)
				if current_user == key_to_uid(key):
					users_views[key] = list
				else:
					if users_views != {}:
						view_distribution = views_to_normalized_cluster_distribution(users_views, cluster_mapping)
						cat_dist = [sum(x) for x in zip(view_distribution, cat_dist)] # add
						if current_user in EXPERTS:
							num_experts += 1
						current_user = key_to_uid(key)
						users_views = {}
			if numpy.mean(cat_dist) > 0.1: # avoid empty groups of all 0s
				print("\nType " + str(counter[0]) + "/" + str(counter[1]))
				print("Type frequency distribution across clusters: " + str(cat_dist))
				shan = shannon(cat_dist)
				print("Shannon index: " + str(shan))
				if shan != "nan":
					shannons.append(shan)
					writer.writerow([cat, len(users), num_experts, shan])
				else:
					print("Invalid shannon")
			else:
				print("Empty type")
			with open(cat + "_dist.txt", 'w') as cat_file:
				cat_file.write(str(cat_dist))
			
	shannons_mean = numpy.mean(shannons)
	shannons_std = numpy.std(shannons)	
	print("Average type Shannon index: " + str(shannons_mean))
	print("Std Dev type Shannon index: " + str(shannons_std))

	
def group_cluster_analysis(cluster_mapping, num_clusters=6, nongroup=False):
	gids = get_valid_gids()
	groups = []
	counter = [0, len(gids)]
	shannons = []
	valid_groups = 0
	shannon_file = "group_shannons.csv"
	if nongroup:
		shannon_file = "nongroup_shannons.csv"
	
	with open(shannon_file, 'w') as gs_file:
		writer = csv.writer(gs_file)
		writer.writerow(["gid", "users", "experts", "shannon"])
		for gid in gids:
			if (gid == 0 and not nongroup) or (gid != 0 and nongroup):
				continue
			group_dist = [0] * num_clusters
			c.execute('''select distinct uid from rprp_puzzle_ranks where gid == \"%s\"; ''' % gid)
			users = [result[0] for result in c.fetchall()]
			if len(users) < 2: # remove small groups
				continue
			print(str(len(users)) + " users")
			num_experts = 0
			for user in users:
				print('.', end='', flush=True)
				views = query_to_views('''where uid = \"%s\"''' % user)
				view_distribution = views_to_normalized_cluster_distribution(views, cluster_mapping)
				view_distribution = [x**2 for x in view_distribution] # NEW square the distribution so specializations stand out
				group_dist = [sum(x) for x in zip(view_distribution, group_dist)] # add
				if user in EXPERTS:
					num_experts += 1
			counter[0] += 1
			if numpy.mean(group_dist) > 0.1: # avoid empty groups of all 0s
				print("\nGroup " + str(counter[0]) + "/" + str(counter[1]))
				print("Group frequency distribution across clusters: " + str(group_dist))
				shan = shannon(group_dist)
				print("Shannon index: " + str(shan))
				if shan != "nan":
					shannons.append(shan)
					valid_groups += 1
					writer.writerow([gid, len(users), num_experts, shan])
				else:
					print("Invalid shannon")
			else:
				print("Empty group")
			
	shannons_mean = numpy.mean(shannons)
	shannons_std = numpy.std(shannons)	
	print("Average group Shannon index: " + str(shannons_mean))
	print("Std Dev group Shannon index: " + str(shannons_std))
	print("Valid groups: " + str(valid_groups))

	
# ------------------------------------------- END ANALYSIS -------------------------------------------
# ----------------------------------------------------------------------------------------------------
	
def get_cluster_centroids():
	clusters = {} # view : cluster
	with open("clusters.csv", 'r') as f:
		reader = csv.reader(f)
		next(reader) # skip header
		for row in reader:
			clusters[row[1]] = row[0]
	
	cl = []
	for i in range(6):
		cl.append([])
	for (view,num) in clusters.items():
		cl[num].append(view)
	print("clusters built")
	for cluster in cl:
		print("Centroid for cluster " + str(num) + " is " + str(centroid(cluster)))
	
def key_to_uid(key):
	return key[:UID_LENGTH]
	
def test_group_stats():
	gids = get_valid_gids()
	groups = []
	for gid in gids:
		if gid == 0: # user not in a group
			continue
		c.execute('''select distinct uid from rprp_puzzle_ranks where is_expert == 0 and gid == \"%s\"; ''' % gid)
		num_novices = len([result[0] for result in c.fetchall()])
		c.execute('''select distinct uid from rprp_puzzle_ranks where is_expert == 1 and gid == \"%s\"; ''' % gid)
		num_experts = len([result[0] for result in c.fetchall()])
		num_users = num_novices + num_experts
		if num_users < 2: # remove small groups
			continue
		g = {}
		g["id"] = gid
		g["experts"] = num_experts
		g["total"] = num_users
		g["percent"] = num_experts / num_users
		groups.append(g)
	sorted_groups = multikeysort(groups, ["-percent", "-total"])
	for gr in sorted_groups:
		percent = '{:.1%}'.format(gr["percent"])
		print("Group " + str(gr["id"]) + ": " + str(gr["experts"]) + "/" + str(gr["total"]) + " experts (" + percent + ")")

	
def count_view_popularity(data, file):
	dataset = defaultdict(int)
	for view in data:
		key = ""
		for ele in view:
			if ele is 1 or ele is 0:
				key += str(ele)
		dataset[key] += 1
	sorted_dict = sorted(dataset.items(), key=operator.itemgetter(1), reverse=True)
	with open(file, 'w') as f:
		writer = csv.writer(f)
		header = ["count"]
		for opt in ALL_USED_OPTIONS:
			header.append(opt)
		writer.writerow(header)
		for key, value in sorted_dict:
			row = [value]
			for i in range(len(key)):
				row.append(key[i])
			writer.writerow(row)
	
def list_to_set(data):
	dataset = set([])
	for d in data:
		dataset.add(tuple(d))
	return dataset

def sse_plot(weighted=True, max=15):
	plt.figure(figsize=(10,7))
	views = query_to_views("")
	data = []
	for (id,view) in views.items():
		if weighted:
			weighted_view = apply_inverse_frequency_weighting(view)
			data.append((view_dict_to_list(weighted_view)))
		else:
			data.append((view_dict_to_list(view)))
	unicode_clean(data)
	data = list_to_set(data) # convert to set to remove duplicates
	data = list(data) # convert back because we need as list
	graph_sses(data, max=max)
	
def cluster_plot(where, filename, n_clusters=6, weighted=False):
	plt.figure(figsize=(10,7))
	views = query_to_views(where)
	weighted_views = []
	for view in views:
		if weighted:
			weighted_views.append(apply_inverse_frequency_weighting(view))
		else:
			weighted_views.append(view)
	data = []
	for (id,view) in views.items():
		data.append((view_dict_to_list(view)))
	unicode_clean(data)
	if args.debug:
		print("Total views: " + str(len(data)))
	data = list_to_set(data) # convert to set to remove duplicates
	if args.debug:
		print("Unique views: " + str(len(data)))
	data = list(data) # convert back because we need as list
	dend = shc.dendrogram(shc.linkage(data, method='ward'))
	plt.savefig(filename)
	clusters_to_stats(data, num_clusters=n_clusters)
	
def get_sse(cluster):
	cent = centroid(cluster)
	sse = 0
	for view in cluster:
		for dim in range(len(view)):
			sse += abs(view[dim] - cent[dim]) ** 2
	return sse
	
def graph_sses(data, max=3):
	print("INFO: Beginning graph of SSE by clusters for up to " + str(max) + " clusters")
	sses = []
	cluster_counts = []
	for i in range(1, max+1):
		print("INFO: Calculating SSE for " + str(i) + " cluster(s)")
		data_buckets = clusters_to_buckets(data, num_clusters=i)
		sse_avg = 0
		for key in data_buckets.keys():
			print("---Cluster " + str(key+1))
			sse_avg += get_sse(data_buckets[key])
		sse_avg /= i
		sses.append(sse_avg)
		cluster_counts.append(i)
	
	plt.plot(cluster_counts, sses, linewidth=2)
	plt.savefig("cluster_scree.png")
	
def clusters_to_buckets(data, num_clusters=6):
	cluster = AgglomerativeClustering(n_clusters=num_clusters, affinity='euclidean', linkage='ward')
	cluster.fit_predict(data)
	data_buckets = {}
	for j in range(num_clusters):
		data_buckets[j] = []
	cluster_labels = cluster.labels_
	for i in range(len(cluster_labels)):
		data_buckets[cluster_labels[i]].append(data[i])
	return data_buckets
	
def clusters_to_stats(data, num_clusters=6):
	cluster = AgglomerativeClustering(n_clusters=num_clusters, affinity='euclidean', linkage='ward')
	cluster.fit_predict(data)
	data_buckets = {}
	for j in range(num_clusters):
		data_buckets[j] = []
	cluster_labels = cluster.labels_
	for i in range(len(cluster_labels)):
		data_buckets[cluster_labels[i]].append(data[i])
	for c in range(len(data_buckets.keys())):
		print("Analyzing cluster " + str(c))
		centroid_stats(cluster=data_buckets[c])
	with open("clusters.csv", 'w') as c_file:
		writer = csv.writer(c_file)
		writer.writerow(["cluster_num", "view"])
		for num, views in data_buckets.items():
			for view in views:
				view_str = view_list_to_string(view)
				writer.writerow([num, view_str])
		
def view_list_to_string(view):
	view_str = ''
	for v in view:
		if v == 0 or v == 1:
			view_str += str(v)
	return view_str

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
		for (id,view) in views.items():
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
def centroid_stats(where="", cluster=None, name=""):
	if cluster == []: # given empty cluster
		return
	# Get total centroid
	if cluster is None:
		views = query_to_views(where)
		cluster = []
		for (id,view) in views.items():
			cluster.append(view_dict_to_list(view))
		print("Analyzing this centroid: " + where)
	unicode_clean(cluster)
	data_count = str(len(cluster))
	print("Density (" + data_count + "):")
	d = density(cluster)
	print(d)
	print("Centroid (" + data_count + "):")
	c = centroid(cluster)
	print(c)
	if name == "":
		name = where
	if len(c) < 1:
		print("WARN: empty centroid")
		return
	with open(name + '.csv', 'w') as c_file:
		writer = csv.writer(c_file)
		writer.writerow(["dim", "M", "std"])
		dimensions = [opt for opt in BINARY_OPTIONS]
		for cat_opt in CAT_KEYS:
			for opt in CAT_OPTIONS[cat_opt]:
				dimensions.append(opt)
		for i in range(len(dimensions)):
			writer.writerow([dimensions[i], c[i], d[i]])


def print_experiment_details():

	from datetime import datetime as dt

	# print start and end dates of the experiment
	c.execute('''select min(time), max(time) from options;''')
	result = c.fetchall()[0]
	start = dt.utcfromtimestamp(result[0])
	end = dt.utcfromtimestamp(result[1])
	print("experiment start datetime: " + str(start))
	print("experiment end datetime: " + str(end))

	# num unique users
	c.execute('''select count(distinct(uid)) from options;''')
	result = c.fetchall()[0][0]
	num_unique_users = result
	print("num unique users: " + str(num_unique_users))

	# num unique puzzles
	c.execute('''select count(distinct(pid)) from options;''')
	results = c.fetchall()
	num_unique_puzzles = results[0][0]
	print("num unique puzzles: " + str(num_unique_puzzles))

	# num unique puzzles per category
	valid_puzzle_cats = get_valid_puzzle_categories()
	print("num unique puzzles per category")
	for cat in valid_puzzle_cats:
		search_cat = cat
		c.execute('''select count(distinct(pid)) from options where instr(puzzle_cat, \"%s\")''' % search_cat)
		category_count = c.fetchall()[0][0]
		print('''%s : %d''' % (cat, category_count))

	# num total samples before filtering

	if os.path.isfile('folditx.db'):
		temp_conn = sqlite3.connect('folditx.db')
		temp_c = temp_conn.cursor()
		temp_c.execute('''select count(*) from options;''')
		results = temp_c.fetchall()
		total_data_samples_before_filtering = results[0][0]
		print("total data samples (pre-filter): " + str(total_data_samples_before_filtering))
	else:
		print("ERR: Could not find database with name folditx.db")

	# num total data samples
	c.execute('''select count(*) from options;''')
	result = c.fetchall()[0][0]
	total_data_samples_after_filtering = result
	print("total data samples (post-filter): " + str(total_data_samples_after_filtering))

	# mean/std dev of options samples per user
	c.execute('''select count(uid) from options group by uid;''')
	results = c.fetchall()
	num_samples_per_user = [result[0] for result in results]
	mean_spu = round(calculate_mean(num_samples_per_user), 2)
	stddev_spu = round(calculate_stddev(num_samples_per_user, mean_spu), 2)
	print("mean of options samples per user: " + str(mean_spu))
	print("std dev of options samples per user: " + str(stddev_spu))

	return


def calculate_mean(data):
	return (sum(data) * 1.0) / len(data)


def calculate_variance(data, mean):
	return sum([(x - mean)**2 for x in data]) / (len(data) - 1)


def calculate_stddev(data, mean):
	variance = calculate_variance(data, mean)
	return variance**0.5


# ------------ END TEST BED -----------------------


def multikeysort(items, columns):
    from operator import itemgetter
    comparers = [((itemgetter(col[1:].strip()), -1) if col.startswith('-') else
                  (itemgetter(col.strip()), 1)) for col in columns]
    def comparer(left, right):
        for fn, mult in comparers:
            result = cmp(fn(left), fn(right))
            if result:
                return mult * result
        else:
            return 0
    return sorted(items, cmp=comparer)


# ------------ ONE TIME FUNCTIONS -----------------

def get_valid_puzzle_categories():
	c.execute('''select puzzle_cat, count(puzzle_cat) from options group by puzzle_cat;''')
	puzzle_category_results = c.fetchall()
	puzzle_categories = defaultdict(int)
	for result in puzzle_category_results:
		if result[1] > 0:
			cats = result[0].split(', ')
			for cat in cats:
				puzzle_categories[cat] += result[1]
	if args.debug:
		print("DEBUG: puzzle category sample count:")
		print(puzzle_categories)
	return puzzle_categories.keys()

def get_valid_gids():
	c.execute('''select gid, count(gid) from rprp_puzzle_ranks group by gid;''')
	group_results = c.fetchall()
	groups = []
	for result in group_results:
		if result[1] > MIN_SAMPLES_PER_GROUP:
			groups.append(result[0])
	return groups
	
def highscore_similarities(puzzle_categories):
	# Cluster by high score / not, report clustering statistics
	print("Calculating high score similarities")
	all_highscores = []
	for cat in puzzle_categories:
		search_cat = cat
		c.execute('''select uid, pid from rprp_puzzle_ranks where best_score_is_hs = 1 and instr(puzzle_cat, \"%s\"); ''' % search_cat)
		highscore_results = c.fetchall()
		print("\nINFO: " + str(len(highscore_results)) + " high score results for " + str(cat) + "\n")
		highscores_in_cat = []
		for uid, pid in highscore_results:
			print('.',end='')
			sys.stdout.flush()
			views_per_user_per_cat = query_to_views('''where uid = \"%s\" and pid = %d ''' % (uid, pid))
			for idkey, view in views_per_user_per_cat.items():
				highscores_in_cat.append(view_dict_to_list(view))
		centroid_name = "highscore_" + str(cat)
		centroid_stats(cluster=highscores_in_cat, name=centroid_name)
		all_highscores += highscores_in_cat
		centroid_name = "all_highscores"
		centroid_stats(cluster=all_highscores, name=centroid_name)
	

def group_similarities(gids, puzzle_categories):
	print("Calculating group and player similarities")
	gid_counter = [0, len(gids)]
	for gid in gids:
		if gid == 0: # user not in a group
			continue
		c.execute('''select distinct uid from rprp_puzzle_ranks where gid == \"%s\"; ''' % gid)
		user_results = c.fetchall()
		users = [result[0] for result in user_results]
		print("\n-------------------------")
		gid_counter[0] += 1
		print("INFO: Processing group " + str(gid_counter[0]) + " / " + str(gid_counter[1]))
		print("INFO: group " + str(gid) + " has " + str(len(users)) + " users")
		print("-------------------------\n")
		lists_per_group = []
		lists_per_group_per_cat = {}
		for user in users:
			lists_per_user = []
			for cat in puzzle_categories:
				print(".", end='')
				sys.stdout.flush()
				if cat not in lists_per_group_per_cat:
					lists_per_group_per_cat[cat] = []
				views_per_user_per_cat = query_to_views('''where uid = \"%s\" and instr(puzzle_cat,\"%s\") ''' % (user, cat))
				lists_per_user_per_cat = []
				for idkey, view in views_per_user_per_cat.items():
					lists_per_user_per_cat.append(view_dict_to_list(view))
				if lists_per_user_per_cat != []:
					print('\n')
					centroid_name = "u_" + str(user) + "_c_" + str(cat) + "_count_" + str(len(lists_per_user_per_cat))
					centroid_stats(cluster=lists_per_user_per_cat, name=os.path.join(GROUP_FOLDER, centroid_name))
					lists_per_user += lists_per_user_per_cat
					lists_per_group_per_cat[cat] += lists_per_user_per_cat
			centroid_name = "u_" + str(user) + "_count_" + str(len(lists_per_user))
			centroid_stats(cluster=lists_per_user, name=os.path.join(GROUP_FOLDER, centroid_name))
			lists_per_group += lists_per_user
		centroid_name = "g_" + str(gid) + "_count_" + str(len(lists_per_group))
		centroid_stats(cluster=lists_per_group, name=os.path.join(GROUP_FOLDER, centroid_name))
		for cat in puzzle_categories:
			centroid_name = "g_" + str(gid) + "_c_" + str(cat) + "_count_" + str(len(lists_per_group_per_cat[cat]))
			centroid_stats(cluster=lists_per_group_per_cat[cat], name=os.path.join(GROUP_FOLDER, centroid_name))
	
def incremental_similarity_averages(files_and_counts, user=False):
	# average the standard deviations across all files
	inc_avgs = [0] * TOTAL_DIMS
	inc_weight = 0
	for name, count in files_and_counts.items():
		prefix = "g_"
		if user:
			prefix = "u_"
		csvfile = prefix + str(name) + "_count_" + str(count) + ".csv"
		fullpath = os.path.join(GROUP_FOLDER, csvfile)
		sum = map(lambda x: x * inc_weight, inc_avgs)
		with open(fullpath, 'r') as f:
			reader = csv.reader(f)
			next(reader) # skip header
			i = 0
			for row in reader:
				sum[i] += (count * float(row[2])) # std		
				i += 1
			if i != len(sum): # assert
				print("ERR: assertion failed, file was " + str(i) + " rows long, there are " + str(len(sum)) + " total dimensions.")
				exit(1)
			inc_weight += count
			for j in range(len(sum)):
				sum[j] /= (inc_weight)
			inc_avgs = sum
		
	prefix = "group"
	if user:
		prefix = "user"
	with open(prefix + '_similarities.csv', 'w') as g:
		writer = csv.writer(g)
		writer.writerow(['dim','average_std'])
		for i in range(len(inc_avgs)):
			writer.writerow([ALL_USED_OPTIONS[i], inc_avgs[i]])
			
def incremental_similarity_averages_by_cat(files_and_counts, user=False):
	for metacat in META_CATEGORIES:
		# average the standard deviations across all files
		inc_avgs = [0] * TOTAL_DIMS
		inc_weight = 0
		for name, count in files_and_counts.items():
			# NOTE: count is wrong for every cat, use glob to find file
			prefix = "g_"
			if user:
				prefix = "u_"
			csv_prefix = prefix + str(name) + "_c_" + metacat + "_count_"
			fullpath = os.path.join(GROUP_FOLDER, csv_prefix)
			filename = ''
			for file in glob.glob(fullpath + '*.csv'):
				filename = file
			sum = map(lambda x: x * inc_weight, inc_avgs)
			with open(file, 'r') as f:
				reader = csv.reader(f)
				next(reader) # skip header
				i = 0
				for row in reader:
					sum[i] += (count * float(row[2])) # std		
					i += 1
				if i != len(sum): # assert
					print("ERR: assertion failed, file was " + str(i) + " rows long, there are " + str(len(sum)) + " total dimensions.")
					exit(1)
				inc_weight += count
				for j in range(len(sum)):
					sum[j] /= (inc_weight)
				inc_avgs = sum
			
		prefix = "group"
		if user:
			prefix = "user"
		with open(prefix + '_' + metacat + '_similarities.csv', 'w') as g:
			writer = csv.writer(g)
			writer.writerow(['dim','average_std'])
			for i in range(len(inc_avgs)):
				writer.writerow([ALL_USED_OPTIONS[i], inc_avgs[i]])
		
def groupuser_analysis():
	groups_and_counts = {}
	users_and_counts = {}
	for root, dir, files in os.walk("."):
		for file in files:
			if file.endswith(".csv"):
				if file.startswith("g_"):
					if "_c_" not in file: # category
						m = re.search('_count_(\d*)\.csv$', file)
						count = int(m.group(1))
						m = re.search('^g_(\d*)_', file)
						gid = m.group(1)
						groups_and_counts[gid] = count
				elif file.startswith("u_"):
					if "_c_" not in file: # category
						m = re.search('_count_(\d*)\.csv$', file)
						count = int(m.group(1))
						m = re.search('^u_([a-zA-Z0-9]*)_', file)
						uid = m.group(1)
						users_and_counts[uid] = count
	
	incremental_similarity_averages_by_cat(groups_and_counts)
	incremental_similarity_averages_by_cat(users_and_counts, user=True)
	incremental_similarity_averages(groups_and_counts)
	incremental_similarity_averages(users_and_counts, user=True)
	
def count_view_frequencies():
	views = query_to_views("")
	data = []
	for (id,view) in items(views):
		data.append((view_dict_to_list(view)))
	unicode_clean(data)
	count_view_popularity(data, "view_frequencies.csv")
	
	for metacat in META_CATEGORIES:
		views = query_to_views("where instr(puzzle_cat,\"" + metacat + "\")")
		data = []
		for (id,view) in items(views):
			data.append((view_dict_to_list(view)))
		unicode_clean(data)
		count_view_popularity(data, metacat + "_view_frequencies.csv")
		
# Calculate and print full report of interesting stats
def main_stats():
	global c
	print("INFO: Beginning main stats tests")
	
	"""
	MAIN STATS
	
	Metacategories (META_CATEGORIES):
		1. Design
		2. Prediction
		3. Electron Density (subcategory of Prediction)
		4. Hand Folding (subcategory of Prediction)
	
	Overall and per-metacategory: Experts vs Novices
	
	Groups/Users
		1. How much variance is there within a group?
			a. Overall and per-metacategory
		2. How much variance is there within a user?
			a. Overall and per-metacategory
			
	Clustering
		1. Run clustering algorithm, described
		2. Describe the centroids of each cluster, interpret
		3. In what clusters do the most modal views fall under?
			a. Overall and per-metacategory
		4. Group/user details
			a. Within each group/user, how many samples fall in each cluster?
			b. How many clusters does the group spread out over?
	
	Final questions:
		1. What are the popular settings?
		2. What does this mean beyond Foldit?	
	"""
	
	fast = True # TODO change to false if running for the first time
	if not fast:
		print("INFO: Expertise analysis")
		# Overall and per-metacategory Experts vs Novices
		for mc in META_CATEGORIES:
			search_mc = mc
			centroid_stats(where='''where is_expert == 0 and instr(puzzle_cat, \"%s\")''' % search_mc, name=mc + "Novice")
			centroid_stats(where='''where is_expert == 1 and instr(puzzle_cat, \"%s\")''' % search_mc, name=mc + "Expert")
		centroid_stats(where="where is_expert == 0", name="OverallNovice")
		centroid_stats(where="where is_expert == 1", name="OverallExpert")
	
		print("INFO: Expertise analysis")
		# Overall and per-metacategory Experts vs Novices
		centroid_stats(where="where is_expert == 0", name="OverallNovice")
		centroid_stats(where="where is_expert == 1", name="OverallExpert")
		for mc in META_CATEGORIES:
			centroid_stats(where="where is_expert == 0 and instr(puzzle_cat,\"" + mc + "\")", name= mc + "Novice")
			centroid_stats(where="where is_expert == 1 and instr(puzzle_cat,\"" + mc + "\")", name= mc + "Expert")
	
		# Groups/Users			
		print("INFO: Loading group and puzzle category data")
		gids = get_valid_gids()
		puzzle_categories = get_valid_puzzle_categories()
		print("INFO: Highscore analysis")
		highscore_similarities(puzzle_categories)
		print("INFO: Group analysis")
		group_similarities(gids, puzzle_categories)
	
		print("INFO: User analysis")
		groupuser_analysis()
					
		# Clustering
		cluster_plot("", "dendro_all_unique.png")
		
	views_to_cnum = {} # map view : cluster num, e.g. 110001101 : 3
	with open("clusters.csv", 'r') as c_file:
		reader = csv.reader(c_file)
		next(reader)
		for row in reader:
			views_to_cnum[row[1]] = row[0]
	
	fast2 = False
	if not fast2:
		# In what clusters do the most modal views fall under? Overall / per-metacategory
		count_view_frequencies()
		cluster_counts = defaultdict(int)
		with open("view_frequencies.csv", 'r') as f:
			reader = csv.reader(f)
			next(reader)
			for row in reader:
				view_str = ""
				for r in row[1:]:
					if r == 0 or r == 1:
						view_str += str(r)
				if view_str == "":
					continue
				cluster_num = views_to_cnum[view_str]
				cluster_counts[cluster_num] += row[0]
		with open('cluster_counts.csv', 'w') as cc:
			writer = csv.writer(cc)
			writer.writerow(["cluster", "freq"])
			for num, freq in cluster_counts.items():
				writer.writerow([num, freq])
		
	for metacat in META_CATEGORIES:
		cluster_counts = defaultdict(int)
		with open(metacat + "_view_frequencies.csv", 'r') as f:
			reader = csv.reader(f)
			next(reader)
			for row in reader:
				view_str = ""
				for r in row[1:]:
					if r == 0 or r == 1:
						view_str += str(r)
				if view_str == "":
					continue
				cluster_num = views_to_cnum[view_str]
				cluster_counts[cluster_num] += row[0]
		with open(metacat + '_cluster_counts.csv', 'w') as cc:
			writer = csv.writer(cc)
			writer.writerow(["cluster", "freq"])
			for num, freq in cluster_counts.items():
				writer.writerow([num, freq])
		
	
	# 4. Group/user details
		# a. Within each group/user, how many samples fall in each cluster?
		# b. How many clusters does the group spread out over?
	
	# Final questions:
		# 1. What are the popular settings?
		# 2. What does this mean beyond Foldit?	

	print_experiment_details()

def freq_all():
	for o in BINARY_OPTIONS + CAT_OPTIONS.keys():
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

def get_all_experts():
	# get all users
	c.execute('''select distinct uid from rprp_puzzle_ranks''')
	users = c.fetchall()
	print("Identifying experts:")
	expert_dict = {}
	user_count = 0
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


# Returns a dictionary mapping each puzzle id to its maximum high score threshold (score required
# to be in top 5% of rankings (95th percentile), lower scores are better
def get_all_puzzle_highscores_dict():

	c.execute('''select distinct pid from rprp_puzzle_ranks''')
	results = c.fetchall()
	puzzle_ids = [result[0] for result in results]

	# dictionary that maps pid to score at the 95th percentile for the puzzle
	pid_highscore = {}

	for pid in puzzle_ids:
		pid_highscore[pid] = get_highscore(pid)

	return pid_highscore


# add best_score_is_hs and cur_score_is_hs cols to specified table
# impt note: must call this function on rprp_puzzle_ranks prior to calling on other tables
def add_is_highscore_cols(table):

	# must get is_hs on ranks table before options table
	if table != "rprp_puzzle_ranks":
		c.execute('''PRAGMA table_info(rprp_puzzle_ranks)''')
		results = c.fetchall()
		rprp_puzzle_ranks_cols = [result[1].encode('ascii', 'ignore') for result in results]
		if "best_score_is_hs" not in rprp_puzzle_ranks_cols or "cur_score_is_hs" not in rprp_puzzle_ranks_cols:
			raise Exception("Must call add_is_highscore_cols('rprp_puzzle_ranks') first")

	# add best_score_is column to specified table
	try:
		c.execute('''ALTER TABLE %s ADD best_score_is_hs INT DEFAULT -1''' % table)
		print('''INFO: Created best_score_is_hs column in %s. Calculating best_score_is_hs ...''' % table)
	except Exception as e:
		print('''INFO: best_score_is_hs column already exists in %s. Recalculating best_score_is_hs...''' % table)

	# add cur_score_is_hs column to specified table
	try:
		c.execute('''ALTER TABLE %s ADD cur_score_is_hs INT DEFAULT -1 NOT NULL''' % table)
		print('''INFO: Created cur_score_is_hs column in %s. Calculating cur_score_is_hs ...''' % table)
	except Exception as e:
		print('''INFO: cur_score_is_hs column already exists in %s. Recalculating cur_score_is_hs...''' % table)

	# get dictionary {pid : high score} from rprp_puzzle_ranks table
	pid_highscore_dict = get_all_puzzle_highscores_dict()

	if table == "rprp_puzzle_ranks":
		update_is_highscore_cols_for_table("rprp_puzzle_ranks", pid_highscore_dict)
	elif table == "options":
		update_is_highscore_cols_for_table("options", pid_highscore_dict)
	else:
		raise Exception("is high score columns not relevant to specified table: " + str(table))


# update best_score_is_hs and cur_score_is_hs columns in specified table using dictionary {pid : highscore}
def update_is_highscore_cols_for_table(table, pid_highscore_dict):

	if table == "rprp_puzzle_ranks":

		for pid in pid_highscore_dict.keys():

			highscore = pid_highscore_dict[pid]
			c.execute('''update rprp_puzzle_ranks set best_score_is_hs = 0 where pid == %d and best_score > %d'''
				% (pid, highscore))
			c.execute('''update rprp_puzzle_ranks set best_score_is_hs = 1 where pid == %d and best_score <= %d'''
				% (pid, highscore))
			c.execute('''update rprp_puzzle_ranks set cur_score_is_hs = 0 where pid == %d and cur_score > %d'''
				% (pid, highscore))
			c.execute('''update rprp_puzzle_ranks set cur_score_is_hs = 1 where pid == %d and cur_score <= %d'''
				% (pid, highscore))

	elif table == "options":

		print("options.best_score_is_hs is DEPRECATED")
		return
		print("updating options best_score_is_hs")

		c.execute('''select distinct uid, pid from options''')
		entries = c.fetchall()
		count = 0
		for entry in entries:
			uid = entry[0]
			pid = entry[1]
			try:
				c.execute('''select best_score_is_hs from rprp_puzzle_ranks where uid == \"%s\" and pid == %d;''' % (uid, pid))
				best_score_is_hs = c.fetchone()
				if best_score_is_hs == None:
					best_score_is_hs = -1
				else:
					best_score_is_hs = best_score_is_hs[0]
				print(best_score_is_hs)
				c.execute('''update options set best_score_is_hs = %d where uid == \"%s\" and pid == %d;''' % (best_score_is_hs, uid, pid))
				count += 1
			except Exception as e:
				print(e)
			if count % 10 == 0:
				print('.',end='')
				sys.stdout.flush()
				return

	else:
		raise Exception("No is high score columns for specified table: " + str(table))

	# save changes to database
	conn.commit()


# Add is_expert col to specified table
def add_is_expert_col(table):
	try:
		c.execute('''ALTER TABLE %s ADD is_expert INT DEFAULT 0 NOT NULL''' % table)
		print('''INFO: Created is_expert column in %s. Calculating is_expert ...''' % table)
	except Exception as e:
		print('''INFO: is_expert column already exists in %s. Recalculating is_expert...''' % table)

	# Get list of experts
	if not os.path.isfile(EXPERTS_FILE):
		raise Exception("ERR: Experts file not found: " + EXPERTS_FILE)
	experts_list = []
	with open(EXPERTS_FILE, 'r') as experts_file:
		reader = csv.reader(experts_file)
		for row in reader:
			experts_list.append(row[0])
	c.execute('''update %s set is_expert = 1 where uid in %s''' % (table, str(tuple(experts_list))))
	conn.commit()


# Add puzzle_cat col to options table
def add_puzzle_cat_col_to_options():
	try:
		c.execute('''ALTER TABLE options ADD puzzle_cat TEXT DEFAULT ""''')
		print('''INFO: Created puzzle_cat column in options. Calculating puzzle_cat ...''')

	except Exception as e:
		print('''INFO: puzzle_cat column already exists in options. Recalculating puzzle_cat...''')

	for cat in PIDS_BY_CAT.keys():
		puzzle_ids = map(int, PIDS_BY_CAT[cat])
		c.execute('''update options set puzzle_cat = puzzle_cat || '%s' where pid in %s'''
			% (", " + str(cat), str(tuple(puzzle_ids))))

	conn.commit()

# Add puzzle_cat col to rprp_puzzle_ranks table
def add_puzzle_cat_col_to_ranks():
	try:
		c.execute('''ALTER TABLE rprp_puzzle_ranks ADD puzzle_cat TEXT DEFAULT ""''')
		print('''INFO: Created puzzle_cat column in rprp_puzzle_ranks. Calculating puzzle_cat ...''')

	except Exception as e:
		print('''INFO: puzzle_cat column already exists in rprp_puzzle_ranks. Recalculating puzzle_cat...''')

	for cat in PIDS_BY_CAT.keys():
		puzzle_ids = map(int, PIDS_BY_CAT[cat])
		c.execute('''update rprp_puzzle_ranks set puzzle_cat = puzzle_cat || '%s' where pid in %s'''
			% (", " + str(cat), str(tuple(puzzle_ids))))

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
	#for cat in CAT_KEYS:
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

	all_options = BINARY_OPTIONS + CAT_KEYS
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
	EXPERTS = []
	if recalculate:
		get_all_experts()
	if EXPERTS == []:
		with open('experts.csv', 'r') as exp_file:
			reader = csv.reader(exp_file)
			for row in reader:
				EXPERTS.append(row[0])
	print("Imported " + str(len(EXPERTS)) + " experts.")

# -------- END ONE TIME FUNCTIONS -----------------

# -------- VIEW-BASED CALCULATIONS ----------------

# Input: string of where queries for options table (e.g. "where uid=... and pid=....")
# For each result, create a view dict of bools representing each option, sorted by key
# Output: dict of views (dict of dicts, keys are unique ids = gid/uid + pid + time (concatted))
def query_to_views(where):

	if args.debug:
		print("\nDEBUG: query_to_views " + str(where))

	views = {}  # dict of dicts, uniquely identified by uid, pid, and time

	query = '''select r.gid, o.uid, o.pid, o.time, %s from options o 
	join (select gid, best_score_is_hs, uid, pid from rprp_puzzle_ranks) r 
	on o.uid == r.uid and o.pid == r.pid %s''' % (', '.join(opt for opt in BINARY_OPTIONS), where)

	c.execute(query)
	results = c.fetchall()

	for result in results:
		gid = -1 if result[0] is None else result[0]
		unique_id = str(gid) + "/" + str(result[1]) + str(result[2]) + str(result[3])
		if unique_id not in views:
			views[unique_id] = {}
		view = views[unique_id]
		for i in range(len(BINARY_OPTIONS)):
			view[BINARY_OPTIONS[i]] = result[i + 4]
		views[unique_id] = view

	# add CAT options to views dict
	if views != {}:
		views = query_binarize_cat_to_dict(where, views)
	if args.debug:
		print("    query_to_views: " + str(len(views.keys())) + " results\n")

	return views


# Input: string of where queries for options table (e.g. "where uid=... and pid=....") and
#        a dict of bools for options, sorted by key {unique_id : {option : bool}}
# For each result, add to the given dict of bools each categorical option, sorted by key
# Output: updated dict (dict of dicts, keys are unique ids = gid/uid + pid + time (concatted))
def query_binarize_cat_to_dict(where, views):

	query = '''select r.gid, o.uid, o.pid, o.time, %s from options o 
	join (select gid, best_score_is_hs, uid, pid from rprp_puzzle_ranks) r 
	on o.uid == r.uid and o.pid == r.pid %s''' % (', '.join(opt for opt in CAT_OPTIONS), where)

	c.execute(query)
	results = c.fetchall()
	for result in results:
		gid = -1 if result[0] is None else result[0]
		unique_id = str(gid) + "/" + str(result[1]) + str(result[2]) + str(result[3])
		if unique_id not in views:
			views[unique_id] = {}
		view = views[unique_id]

		for i in range(len(CAT_OPTIONS)):

			cat_option_name = list(CAT_OPTIONS.keys())[i]
			cat_option_values = CAT_OPTIONS[cat_option_name]
			result_value = result[i + 4]

			for option in cat_option_values:
				if option == result_value:
					view[option] = 1
				else:
					view[option] = 0
		views[unique_id] = view
	return views

def list_clean(list):
	for i in range(len(list)):
		if list[i] == u'0':
			list[i] = 0
		elif list[i] == u'1':
			list[i] = 1
	return list

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
		try:
			list.append(view[bin_opt])
		except Exception as e:
			print("view_dict_to_list error")
			if view.startswith("U"):
				print("Did you accidentally give it the uid instead of the value of views[uid]?")
	for cat_opt in CAT_KEYS:
		for opt in CAT_OPTIONS[cat_opt]:
			list.append(view[opt])
	return list

# doesn't work if some of the dimensions were deleted during analysis
# The reverse of view_dict_to_list
# Input: list of just the view option values in a sorted order to keep things consistent
# Output: view dict as "option name": option value
def list_to_view_dict(list):
	view = {}
	for bin_opt in BINARY_OPTIONS:
		view[bin_opt] = list.pop(0)
	for cat_opt in CAT_KEYS:
		for opt in CAT_OPTIONS[cat_opt]:
			view[opt] = list.pop(0)
	return view


# Returns true iff score is <= 5% of best scores for this puzzle
def is_highscore(pid, score):
	# get the score of the entry that's exactly 95th percentile, check our score vs that
	min_score = get_highscore(pid)
	return score <= min_score


# Returns score threshold for pid to be in top 5% of best scores for the puzzle, lower scores are better
def get_highscore(pid):
	c.execute(
		'''select distinct uid, best_score from rprp_puzzle_ranks where pid=%d group by uid order by best_score asc;''' % pid)
	# count entries, get the entry that's exactly 95th percentile
	results = c.fetchall()
	num_scores = len(results)
	index = min(int(math.ceil(num_scores * 0.05)) - 1, len(results) - 1)  # prevent index out of range error
	min_score = results[index][1]
	return min_score


# Returns number of high scores in puzzles
def count_expertise(uid):
	# get list of their best scores for each puzzle
	# count is_highscore
	has_hs_column = True
	try:
		c.execute('''select pid, best_score, best_score_is_hs from rprp_puzzle_ranks where uid=\"%s\" group by pid order by best_score asc;''' % uid)
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


def generate_frequencies_file():
	freq_bin_rows = []
	freq_cat_rows = []

	for o in BINARY_OPTIONS:
		try:
			c.execute(FREQ_COUNT_QUERY % (o,o,o))
			results = [[o] + list(r) for r in c.fetchall()]
			freq_bin_rows += results
		except Exception as e:
			print("Invalid option: " + str(o))

	for o in CAT_OPTIONS.keys():
		try:
			c.execute(FREQ_COUNT_QUERY % (o, o, o))
			results = c.fetchall()
			total = sum([x[1] for x in results])

			for result in results:
				freq_cat_rows += [[result[0], "0", total - result[1]], [result[0], "1", result[1]]]
		except Exception as e:
			print("Invalid option: " + str(o))

	with open(FREQUENCIES_FILE, 'w') as cc:
		writer = csv.writer(cc)
		writer.writerow(["option", "value", "freq"])
		writer.writerows(freq_bin_rows)
		writer.writerows(freq_cat_rows)


# Input: a View dict
# Output: the View Dict, elementwise multiplied by (1-frequency)
def apply_inverse_frequency_weighting(view):

	# Generate the frequencies file (uncomment if need be)
	#generate_frequencies_file()

	if not os.path.isfile(FREQUENCIES_FILE):
		raise Exception("ERR: Frequency file not found: " + FREQUENCIES_FILE)
	freq_dict = {}
	# Read in the frequencies file
	with open(FREQUENCIES_FILE, 'r') as frequencies_file:
		reader = csv.reader(frequencies_file)
		next(reader, None) # skip header row
		for row in reader:
			freq_dict[row[0] + row[1]] = int(row[2])
	for opt in view.keys():
		try:
			option_val = int(view[opt])
			zero = freq_dict[opt + "0"]
			one = freq_dict[opt + "1"]
			if option_val == 0:
				weight = zero / (zero + one) if zero > 0 else 0  # avoid div by 0 error
			else:
				weight = one / (zero + one) if one > 0 else 0
			view[opt] = 1.0 - weight
		except KeyError as e:
			if opt is not "Hydrophobic": # hard code :( but Hydrophobic seems to be removed from game
				print("WARN: No frequency found in " + FREQUENCIES_FILE + " for option: " + opt)
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
	if cluster == []: # handle empty set
		return []
	stds = []
	if dims == [-1]:
		dims = range(len(cluster[0]))
	for i in dims:
		stds.append(numpy.std([view[i] for view in cluster]))
	return stds



# maybe there should be some way to specify dims by human-readable option (for this and density function)
# returns the centroid of a cluster
# if dims option is set, calculates for only specific dimension(s)
def centroid(clus, dims=[-1]):
	if clus == []: # handle empty set
		return []
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
			print("clean - clean the database of bad entries")
			print("process - add new data to database, e.g. highscore info, is expert info")
			print("stats - print experiment details")
			print("main - run all main stats tests (will take a while)")
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

		if command == "main":
			main_stats()

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
			print("INFO: adding puzzle category labels")
			add_puzzle_cat_col_to_ranks()
			add_puzzle_cat_col_to_options()
			print("INFO: Updating high scores...")
			add_is_highscore_cols("rprp_puzzle_ranks")
			print("INFO: Finding experts...")
			import_experts(recalculate=True)
			add_is_expert_col("rprp_puzzle_ranks")
			add_is_expert_col("options")

		if command == "stats":
			print_experiment_details()

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
	import math, operator, csv, sys, re, numpy, sqlite3, datetime, os.path
	import cProfile, pstats, glob
	from scipy import stats
	import scipy.cluster.hierarchy as shc
	from skbio.diversity.alpha import shannon
	import matplotlib
	matplotlib.use('Agg')
	import matplotlib.pyplot as plt

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
	try:
		import_experts(recalculate=False)
	except IOError as e:
		import_experts(recalculate=True)

print("...Loaded.")

if args.debug:
	print("DEBUG mode on")

# TEST
# import StringIO
# pr = cProfile.Profile()
# pr.enable()
# s = StringIO.StringIO()
# test(args)
# pr.disable()
# sortby = 'cumulative'
# ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
# ps.print_stats()
# print(s.getvalue())
# exit(1)

if args.test:
	test(args)
else:
	io_mode(args)
