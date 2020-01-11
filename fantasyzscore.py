#make separate file for imports?
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import math
import time
import unidecode

#parse bball ref for data
year = 2020
url = "https://www.basketball-reference.com/leagues/NBA_{}_per_game.html".format(year)
html = urlopen(url)
soup = BeautifulSoup(html, 'html.parser')

headers = [th.getText() for th in soup.findAll('tr', limit=2)[0].findAll('th')]
headers = headers[1:] #don't care about Rk
rows = soup.findAll('tr')[1:] #skip row 0 because it contains the headers
player_stats = [[td.getText() for td in rows[i].findAll('td')] for i in range(len(rows))]

stats = pd.DataFrame(player_stats, columns = headers)
stats = stats.dropna(how='all') #delete all NaN rows

unidecode_names_list = [] #remove accents from characters like 'Luka Dončić' becomes 'Luka Doncic'

for player_name in stats['Player']:
	unidecode_name = unidecode.unidecode(player_name).lower()
	unidecode_names_list.append(unidecode_name)

stats['Player'] = unidecode_names_list
stats = stats.set_index('Player')

#prompt user to input roster
my_team_as_string_input = input("Enter your roster separated by commas. " 
								"Capitalization not required.\n")

my_team_as_list = my_team_as_string_input.split(",")

temp_my_team_as_list = my_team_as_list
my_team_as_list = []

#string manipulation for cases where input includes ", "
#removing the space after the comma if it exists
for name in temp_my_team_as_list:
	full_name = ""
	split_name = name.split(" ")
	for string in split_name:
		if (full_name != ""):
			full_name += " " #add space after first name
		if (string != " "):
			string = string.lower()
			full_name += string
	my_team_as_list.append(full_name)

#call alphabetical_sort(), fill(), filter_cats(), cats_to_float()
def initialize(players):
	#players = alphabetical_sort(players)
	db = fill(players)
	db = filter_cats(db)
	db = cats_to_float(db)
	return db

#might actually have to manually change each column type
def cats_to_float(db):
	db = db.astype({
		"FG": float,
		"FGA": float,
		"FG%": float,
		"FT": float,
		"FTA": float,
		"FT%": float,
		"3P": float,
		"TRB": float,
		"AST": float,               
		"STL": float,
		"BLK": float,
		"TOV": float,
		"PTS": float
		})
	return db

#sort by last name then first name; latter only works if players have same last name
def alphabetical_sort(db):
	db = sorted(sorted(db), key=lambda n: n.split()[1])
	return db

#fill team stats df, pass in my_team_as_list and returns filled df
#call should be my_team = fill(my_team_as_list) 
def fill(indices):
	teamdata = []
	for p in indices:
		for ind in stats.index:
			if p == ind:
				if type(stats.loc[p]) is pd.DataFrame:
					df = stats.loc[p]
					df = df.iloc[:1].values.tolist()
					teamdata.append(df[0])
					break
				else:
					teamdata.append(list(stats.loc[p]))
					break
	temp_headers = headers[1:] #get rid of 'Player' because it's being used as index
	temp_df = pd.DataFrame(teamdata, index = indices, columns = temp_headers)
	return temp_df

#filter out unnecessary stats for fantasy
#call should be my_team = filter_cats(my_team)
def filter_cats(players_df):
	filtered_df = pd.DataFrame(index = players_df.index)
	for col in players_df.columns:
		if (col == "FG" or col == "FGA" or col == "FG%"
				or col == "FT" or col == "FTA" or col == "FT%"
				or col == "3P" or col == "TRB" or col == "AST"
				or col == "STL" or col == "BLK" or col == "TOV" or col == "PTS"):
			filtered_df[col] = players_df[col]
	return filtered_df	

#filter out players with low minutes played 
#call should be filter_stats = filter_stats(stats)
#update function to let user decide what to filter
#def filter_stats(season_stats, cat, min) <- possible update
def filter_stats(season_stats):
	season_df = pd.DataFrame(columns = season_stats.columns)
	for ind in season_stats.index:
		try:
			if float(season_stats.at[ind, 'G']) * float(season_stats.at[ind, 'MP']) > 250:
				temp_df = pd.Series(season_stats.loc[ind])
				season_df = season_df.append(temp_df)
		except TypeError:
			if float(season_stats.at[ind, 'G'][0]) * float(season_stats.at[ind, 'MP'][0]) > 250:
				temp_df = (stats.loc[ind]).iloc[0]
				season_df = season_df.append(temp_df)
		except KeyError:
			return season_stats
	return season_df	

#TODO: z-score = (xi - xbar) / sd
#create dictionary that maps each category to their respective get_z_{} functions
#call is df = get_z_scores(my_team, stats)
def get_z_scores(players_df, bball_ref_df):
	z_headers_percent = ["FG%", "FT%", "3P", "TRB", "AST", "STL", "BLK", "TOV", "PTS"]
	z_score = pd.DataFrame(index = players_df.index, columns = z_headers_percent)
	f_stats = filter_stats(bball_ref_df)
	f_stats = filter_cats(f_stats)
	f_stats = cats_to_float(f_stats)
	avg = get_averages(f_stats)
	variance = get_var(f_stats, avg)
	fga_list = []
	fta_list = []
	count = 0

	for b in players_df.columns:
		if b == 'FG' or b == 'FT':
			useless = True
		elif b == 'FGA':
			for a in f_stats.index:
				fga_list.append(f_stats[b][a])
		elif b == 'FTA':
			for a in f_stats.index:
				fta_list.append(f_stats[b][a])
		elif b == 'FG%':
			for a in players_df.index:
				z_score[b][a] = ((players_df[b][a] - avg[count]) * fga_list[count]) / math.sqrt(variance[count])
				z_score[b][a] = round(z_score[b][a], 2)
		elif b == 'FT%':
			for a in players_df.index:
				z_score[b][a] = ((players_df[b][a] - avg[count]) * fta_list[count]) / math.sqrt(variance[count])
				z_score[b][a] = round(z_score[b][a], 2)
		elif b == 'TOV':
			for a in players_df.index:
				z_score[b][a] = (players_df[b][a] - avg[count]) / math.sqrt(variance[count])
				z_score[b][a] = round(z_score[b][a], 2) * (-1)
		else:
			for a in players_df.index:
				z_score[b][a] = (players_df[b][a] - avg[count]) / math.sqrt(variance[count])
				z_score[b][a] = round(z_score[b][a], 2)
		count += 1
	return z_score

#TODO: averages for df
def get_averages(players_df):
	'''
	fgm = 0
	fga = 0
	ftm = 0
	fta = 0
	threep = 0
	trb = 0
	ast = 0
	stl = 0
	blk = 0 
	tov = 0
	pts = 0
	n = len(players_df.index)
	avg_list = []

	for c in players_df.columns:
		if c == 'FG':
			for ind in players_df.index:
				fgm += players_df[c][ind]
		elif c == 'FGA':
			for ind in players_df.index:
				fga += players_df[c][ind]
		elif c == 'FT':
			for ind in players_df.index:
				ftm += players_df[c][ind]
		elif c == 'FTA':
			for ind in players_df.index:
				fta += players_df[c][ind]
		elif c == '3P':
			for ind in players_df.index:
				threep += players_df[c][ind]
		elif c == 'TRB':
			for ind in players_df.index:
				trb += players_df[c][ind]
		elif c == 'AST':
			for ind in players_df.index:
				ast += players_df[c][ind]
		elif c == 'STL':
			for ind in players_df.index:
				stl += players_df[c][ind]
		elif c == 'BLK':
			for ind in players_df.index:
				blk += players_df[c][ind]
		elif c == 'TOV':
			for ind in players_df.index:
				tov += players_df[c][ind]
		elif c == 'PTS':
			for ind in players_df.index:
				pts += players_df[c][ind]

	fgp = fgm / fga
	ftp = ftm / fta
	threep = threep / n
	trb = trb / n
	ast = ast / n
	stl = stl / n
	blk = blk / n
	tov = tov / n
	pts = pts / n

	avg_list.append(fgp)
	avg_list.append(ftp)
	avg_list.append(threep)
	avg_list.append(trb)
	avg_list.append(ast)
	avg_list.append(stl)
	avg_list.append(blk)
	avg_list.append(tov)
	avg_list.append(pts)

	print(avg_list)
	return avg_list
	'''
	return players_df.mean(axis = 0)

#TODO: s**2 = [summation of [(xi - xbar)**2]] / (n - 1)
def get_var(f_stats, avg):
	count = 0
	my_var_list = []
	n = len(f_stats.index)
	fga_list_2 = []
	fta_list_2 = []

	for b in f_stats.columns:
		summation = 0
		if b == 'FG' or b == 'FT':
			useless = True
		elif b == 'FGA':
			for a in f_stats.index:
				fga_list_2.append(f_stats[b][a])
		elif b == 'FTA':
			for a in f_stats.index:
				fta_list_2.append(f_stats[b][a])
		elif b == 'FG%':
			for a in f_stats.index:
				if isinstance(f_stats[b][a], pd.Series):
					first_instance = list(f_stats[b][a])[0]
					xi_minus_xbar = (first_instance - avg[count]) * fga_list_2[count]
				else:
					xi_minus_xbar = (f_stats[b][a] - avg[count]) * fga_list_2[count]
				if xi_minus_xbar < 0:
					xi_minus_xbar = xi_minus_xbar * (-1)
				summation = summation + (xi_minus_xbar**2)
		elif b == 'FT%':
			for a in f_stats.index:
				if isinstance(f_stats[b][a], pd.Series):
					first_instance = list(f_stats[b][a])[0]
					xi_minus_xbar = (first_instance - avg[count]) * fta_list_2[count]
				else:
					xi_minus_xbar = f_stats[b][a] - avg[count] * fta_list_2[count]
				if xi_minus_xbar < 0:
					xi_minus_xbar = xi_minus_xbar * (-1)
				summation = summation + (xi_minus_xbar**2)
		else:
			for a in f_stats.index:
				if isinstance(f_stats[b][a], pd.Series):
					first_instance = list(f_stats[b][a])[0]
					xi_minus_xbar = (first_instance - avg[count])
				else:
					xi_minus_xbar = f_stats[b][a] - avg[count]
				if xi_minus_xbar < 0:
					xi_minus_xbar = xi_minus_xbar * (-1)
				summation = summation + (xi_minus_xbar**2)
		var = summation / (n - 1)
		my_var_list.append(var)
		count += 1

	return my_var_list

#add total z-score for each cat and each player
#total for each cat, append as row
#total for each player, append as column
def add_total_z_score(players_df):
	indices = players_df.index.tolist()
	indices.append('TOTAL')
	player_total_z_score = pd.DataFrame(players_df.sum(axis = 1))
	players_df = players_df.join(player_total_z_score)
	players_df.rename(columns = {0: 'VALUE'}, inplace = True)
	players_df = players_df.astype({"VALUE": float})
	cat_total_z_score = players_df.sum(axis = 0)
	players_df = players_df.append(cat_total_z_score, ignore_index = True)
	players_df['NAME'] = indices
	players_df = players_df.set_index('NAME')
	return players_df

#unnecessary function but will keep for potential future use
#can also just scrape total stats URL
def get_totals(players_df):
	z_headers_percent = ["FG%", "FT%", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]
	z_headers_no_percent = ["FG", "FGM", "FT", "FTM", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]
	temp_list = []
	total = 0.0

	for b in players_df.columns:
		if b != 'FG%' and b != 'FT%':
			for a in players_df.index:
				total += players_df[b][a]
			temp_list.append(total)
		total = 0

	temp_df = pd.DataFrame(columns = z_headers_no_percent)
	temp_df.loc[len(temp_df)] = temp_list
	return temp_df

#TODO: add player to roster
def add_player(player):
	pass

#TODO: remove player from roster
def remove_player(player):
	pass

'''
#filter out all players with <X minutes played
#sort by total z-score
#keep top 12*14 players
#find new z-score based on 12*14 players avg
'''
'''

my_team = initialize(my_team_as_list)
print(my_team)
my_team = get_z_scores(my_team, stats)
my_team = add_total_z_score(my_team)
print(my_team)
'''

abcd = filter_stats(stats)

no_duplicates_list = []
for ind in abcd.index:
	if ind not in no_duplicates_list:
		no_duplicates_list.append(ind)

temp_stats = initialize(no_duplicates_list)
stats_z_scores = get_z_scores(temp_stats, stats)
stats_z_scores = add_total_z_score(stats_z_scores)
stats_z_scores.drop(stats_z_scores.tail(1).index,inplace=True)
stats_z_scores = stats_z_scores.sort_values('VALUE', ascending=False)

top_200_players = stats_z_scores[:200].index
top_200_players = initialize(top_200_players)
top_200_z_score = get_z_scores(top_200_players, top_200_players)
top_200_z_score = add_total_z_score(top_200_z_score)
top_200_z_score = top_200_z_score.sort_values('VALUE', ascending=False)
print(top_200_z_score.head(10))
a = top_200_z_score.sort_values('FG%', ascending=False)
print(a.head(10))
b = top_200_z_score.sort_values('FT%',ascending=False)
print(b.head(10))


'''
1. filter player by minutes played
2. get z-score of filtered player list
3. sort by highest z-score value and take top 200
4. get z-score of team 
'''

'''
def main():
	pass

if __name__ == '__main__':
	main()
'''
