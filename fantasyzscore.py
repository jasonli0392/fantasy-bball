#make separate file for imports?
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from math import sqrt
from unidecode import unidecode

#determines what season of NBA data
year = 2020

#data source
url = "https://www.basketball-reference.com/leagues/NBA_{}_per_game.html".format(year)

#parse bball ref for data
html = urlopen(url)
soup = BeautifulSoup(html, 'html.parser')

headers = [th.getText() for th in soup.findAll('tr', limit=2)[0].findAll('th')]
headers = headers[1:] #don't care about Rk

rows = soup.findAll('tr')[1:] #skip row 0 because it contains the headers
player_stats = [[td.getText() for td in rows[i].findAll('td')] for i in range(len(rows))]
stats = pd.DataFrame(player_stats, columns = headers)
stats = pd.DataFrame(player_stats, index = stats['Player'], columns = headers)
stats = stats.dropna(how='all') #delete all NaN rows
del stats['Player'] #don't need as it is the df's index

#prompt user to input roster
my_team_as_string_input = input("Enter your roster separated by commas. " 
								"Capitalization not required.\n")

#TODO: add [user input amount] random players to list
if my_team_as_string_input == "random":
	pass

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
			string = string.capitalize()
			full_name += string
	my_team_as_list.append(full_name)

#call alphabetical_sort(), fill(), filter_cats(), cats_to_float()
def initialize(players):
	players = alphabetical_sort(players)
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
		"PTS": float,
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
				teamdata.append(list(stats.loc[p]))
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
			temp_df = pd.DataFrame(players_df[col], index = players_df.index)
			filtered_df = filtered_df.join(temp_df)
	return filtered_df	

#filter out players with low minutes played 
#call should be filter_stats = filter_stats(stats)
#update function to let user decide what to filter
#def filter_stats(season_stats, cat, min) <- possible update
def filter_stats(season_stats):
	season_df = pd.DataFrame(columns = season_stats.columns)
	for ind in season_stats.index:
		if float(season_stats.at[ind, 'G']) * float(season_stats.at[ind, 'MP']) > 200:
			temp_df = pd.Series(season_stats.loc[ind])
			season_df = season_df.append(temp_df)
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
	variance = get_var(players_df, f_stats, avg)
	count = 0

	for b in players_df.columns:
		if b != 'FG' and b != 'FGA' and b != 'FG%' and b != 'FT' and b != 'FTA' and b != 'FT%':
			for a in players_df.index:
				z_score[b][a] = (players_df[b][a] - avg[count]) / sqrt(variance[count])
		count += 1
	return z_score

#TODO: averages for df
def get_averages(players_df):
	return players_df.mean(axis = 0)

#TODO: s**2 = [summation of [(xi - xbar)**2]] / (n - 1)
def get_var(players_df, f_stats, avg):
	count = 0
	my_var_list = []

	for b in players_df.columns:
		summation = 0
		if b != 'FG' and b != 'FGA' and b != 'FG%' and b != 'FT' and b != 'FTA' and b != 'FT%':
			for a in players_df.index:
				summation += ((players_df[b][a] - avg[count]) ** 2)
		var = summation / ((len(f_stats.index)) - 1)
		my_var_list.append(var)
		count += 1
	return my_var_list

def get_totals(players_df):
	z_headers_percent = ["FG%", "FT%", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]
	z_headers_no_percent = ["FG", "FGM", "FT", "FTM", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]
	fg_or_ft = []
	fgm_or_ftm = []
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

#TODO: 
def get_z_fg():
	pass

#TODO: 
def get_z_ft():
	pass

#TODO: 
def get_z_3pm():
	pass

#TODO: 
def get_z_reb():
	pass

#TODO: 
def get_z_ast():
	pass

#TODO: 
def get_z_stl():
	pass

#TODO: 
def get_z_blk():
	pass

#TODO: 
def get_z_to():
	pass

#TODO: 
def get_z_pts():
	pass

#TODO: add player to roster
def add_player(player):
	pass

#TODO: remove player from roster
def remove_player(player):
	pass

'''
jason = ["Andre Drummond",
		"Luka Dončić",
		"Donovan Mitchell",
		"Robert Covington",
		"Eric Bledsoe",
		"Ricky Rubio",
		"Rajon Rondo",
		"PJ Washington",
		"Kevon Looney",
		"Danuel House",
		"Elfrid Payton",
		"Nerlens Noel"]
'''

#filter out all players with <X minutes played
#sort by total z-score
#keep top 12*14 players
#find new z-score based on 12*14 players avg

my_team = initialize(my_team_as_list)
print(my_team)
my_team = get_z_scores(my_team, stats)
print(my_team)
'''
#totals for season
total_stats = filter_stats(stats)
total_stats = filter_cats(total_stats)
total_stats = cats_to_float(total_stats)
stats = stats.astype({"G": float})
for b in total_stats.columns:
	if b != 'G':
		for a in total_stats.index:
			total_stats[b][a] = stats['G'][a] * total_stats[b][a]

print(total_stats)
'''






'''
def main():
	pass

if __name__ == '__main__':
	main()
'''