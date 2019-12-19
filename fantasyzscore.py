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

#add [user input amount] random players to list
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
		"FT": float,
		"FTA": float,
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
#call should be filtered_stats = filter_stats(stats)
#update function to let user decide what to filter
#def filter_stats(season_stats, cat, min) <- possible update
def filter_stats(season_stats):
	season_df = pd.DataFrame(columns = season_stats.columns)
	for ind in season_stats.index:
		if float(season_stats.at[ind, 'G']) * float(season_stats.at[ind, 'MP']) > 200:
			temp_df = pd.Series(season_stats.loc[ind])
			season_df = season_df.append(temp_df)
	return season_df	

#z-score = (xi - xbar) / sd
def get_z_scores(players_df):
	z_headers = ["FG%", "FT%", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS"]
	z_score = pd.DataFrame(index = players_df.index, columns = z_headers)
	for col in players_df.columns:


#averages for df
def get_averages(players_df):
	return players_df.mean(axis = 0)

def get_sd(var):
	return sqrt(var)

#s**2 = [summation of [(xi - xbar)**2]] / (n - 1)
def get_variance(players_df):
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

my_team = initialize(my_team_as_list)
print(my_team)

