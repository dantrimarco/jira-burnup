from jira import JIRA
import pandas as pd
import numpy as np
import plotly as py
import plotly.graph_objects as go
import plotly.express as px
import datetime as dt
import os
import yaml
import re

def read_config():

	with open("jira_config.yaml", 'r') as stream:
		try:
			config = yaml.safe_load(stream)

		except yaml.YAMLError as exc:
			print(exc)

	return config

def create_jira_connection(url, username, password):

	options = {'server':url}
	jira = JIRA(options=options, basic_auth=(username, password))

	return jira

def get_issues(jira, search_query):

	# Generate list of issues objects
		
	issues = jira.search_issues(search_query, maxResults=False)

	
	# Generate data from issues
	issues_data = []

	for issue in issues:
		key = issue.key
		story_points = issue.fields.customfield_10004
		status = issue.fields.status.name
		status_change_date = issue.fields.statuscategorychangedate
		created_date = issue.fields.created
		
		sprint_data_raw = issue.fields.customfield_10101
		
		if sprint_data_raw is None:
			sprint_name = ''
			sprint_id = ''
			
		elif len(sprint_data_raw)>1:
			parsed_id_list = []
			parsed_name_list = []

			for i in sprint_data_raw:
				id_match = [m.start() for m in re.finditer('id=',i)]

				id_start = id_match[0]+3
				id_slice = i[id_start:]
				id_end = id_slice.find(',')

				id_val = int(id_slice[0:id_end])

				name_match = [m.start() for m in re.finditer('name=',i)]

				name_start = name_match[0]+5
				name_slice = i[name_start:]
				name_end = name_slice.find(',')

				name_val = name_slice[0:name_end]

				parsed_id_list.append(id_val)
				parsed_name_list.append(name_val)

			name_index = parsed_id_list.index(max(parsed_id_list))

			sprint_name = parsed_name_list[name_index]
			sprint_id = int(max(parsed_id_list))
		

		else:
			last_sprint = issue.fields.customfield_10101[0]
			sprint_name = last_sprint[last_sprint.find('name=')+5:last_sprint.find(',goal=')]
			sprint_id = int(last_sprint[last_sprint.find('id=')+3:last_sprint.find(',rapidViewId=')])
			

		
		
		issue_dict = {
			'key': key,
			'story_points': story_points,
			'status': status,
			'created_date': created_date,
			'status_change_date': status_change_date,
			'sprint_id': sprint_id,
			'sprint_name': sprint_name
			
		}
		
		issues_data.append(issue_dict)

	issues_df = pd.DataFrame(issues_data)

	return issues_df

def aggregate_completed_points(issues_df):

	done_issues = issues_df[issues_df['status']=='Done']
	
	completed_points_per_sprint = done_issues.groupby('sprint_id')['story_points'].agg(sum).reset_index()

	completed_points_per_sprint = completed_points_per_sprint.sort_values(by=['sprint_id'])

	completed_points_per_sprint['cumulative_points'] = completed_points_per_sprint['story_points'].cumsum()

	completed_points_per_sprint.columns = ['sprint_id','completed_points','cumulative_points']

	return completed_points_per_sprint


def get_sprint_list(jira, jira_board_id, sprint_id_start=0, sprint_id_end=9999):


	sprints = jira.sprints(jira_board_id)

	sprint_data = []

	for sprint in sprints:

		name = sprint.name
		state = sprint.state
		sprint_id = sprint.id
		
		sprint_dict = {
			'sprint_id':sprint_id,
			'sprint_name':name,
			'sprint_state':state
		}
		
		sprint_data.append(sprint_dict)

	sprint_df = pd.DataFrame(sprint_data)

	# Filter sprint_id range
	sprint_df = sprint_df[(sprint_df['sprint_id'] >= sprint_id_start) & (sprint_df['sprint_id'] <= sprint_id_end)]

	return sprint_df

def create_total_scope_data(issues_df, completed_points_per_sprint, sprint_df, export=True, sprint_data_filename='sprint_data.csv'):

	extension_check = sprint_data_filename[-4:] == '.csv'

	if extension_check == False:
		raise ValueError('Only .csv format is accepted.')
		
	else:
		pass

	# TO-DO: add a check for adding new sprints from sprint_df

	if os.path.isfile(sprint_data_filename) == False:

		print('Creating new dataset')

		sprint_data = sprint_df.merge(completed_points_per_sprint,how='left',on='sprint_id')
		

		# Calculate the projected points based on the average story points for all stories in the JIRA data
		projected_points = round(len(issues_df)*issues_df['story_points'].mean())

		# Calculate the total story points that have estimates in the JIRA data
		estimated_points = issues_df['story_points'].sum()

		sprint_data['projected_points'] = projected_points
		sprint_data['estimated_points'] = estimated_points


		latest_sprint = sprint_data[['sprint_state', 'sprint_id']].iloc[-1]

		sprint_data.loc[sprint_data['sprint_state']=='ACTIVE', ['completed_points','cumulative_points']] = [np.nan, np.nan]

		sprint_data = sprint_data.sort_values(by=['sprint_id'])

		# Write to file
		if export==True:

			# Write new sprint data
			sprint_data.to_csv(sprint_data_filename)


	elif os.path.isfile(sprint_data_filename) == True:

		# Read data and backup
		sprint_data = pd.read_csv(sprint_data_filename,index_col=0)

		sprint_data_backup = sprint_data.copy()

		# Update sprint names and state from sprint_df

		sprint_data = sprint_df.merge(sprint_data, on=['sprint_id','sprint_name','sprint_state'],how='left')

		# Get the latest CLOSED sprint
		latest_sprint_id = sprint_data[sprint_data['sprint_state']=='CLOSED']['sprint_id'].iloc[-1]
		latest_sprint_name = sprint_data[sprint_data['sprint_state']=='CLOSED']['sprint_name'].iloc[-1]

		# Get the value for complete/cumulative points in this sprint from the aggregate JIRA data
		latest_sprint_complete_points = completed_points_per_sprint[completed_points_per_sprint['sprint_id']==latest_sprint_id]['completed_points'].values[0]
		latest_sprint_cumulative_points = completed_points_per_sprint[completed_points_per_sprint['sprint_id']==latest_sprint_id]['cumulative_points'].values[0]

		# Calculate the projected points based on the average story points for all stories in the JIRA data
		latest_projected_points = round(len(issues_df)*issues_df['story_points'].mean())

		# Calculate the total story points that have estimates in the JIRA data
		latest_estimated_points = issues_df['story_points'].sum()

		 # Assign updated values for complete and cumulative points to this current sprint

		sprint_data.loc[sprint_data['sprint_id']==latest_sprint_id, ['completed_points','cumulative_points']] = [latest_sprint_complete_points, latest_sprint_cumulative_points]

		 # Assign updated values for estimated points to the current and all future sprints

		sprint_data.loc[sprint_data['sprint_id']>=latest_sprint_id, ['estimated_points']] = [latest_estimated_points]

		# Assign updated values for projected points to the current and all future sprints
		sprint_data.loc[sprint_data['sprint_id']>=latest_sprint_id,'projected_points'] = latest_projected_points 

		# Write to file
		if export==True:

			# Write new sprint data
			sprint_data.to_csv(sprint_data_filename)

			# Create backup with time-based filename
			timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			sprint_data_backup_filename = 'backup_'+timestamp+sprint_data_filename

			# Write backup sprint data
			sprint_data_backup.to_csv(sprint_data_backup_filename)

		
	return sprint_data


def create_forecast(sprint_data):

	# Filter sprint_data to calculate forecast from only the last 3 sprints that are CLOSED

	completed_sprints = sprint_data[sprint_data['sprint_state']=='CLOSED'].iloc[-3:].copy()

	# Calculate trendline data. Probably shouldn't use plotly for this, but it's easier than using another package for now

	trendline = px.scatter(x=completed_sprints.index.to_list(),y=completed_sprints['cumulative_points'],trendline='ols').data[1]
	fit_y = trendline['y'].tolist()
	fit_x = trendline['x'].tolist()

	y_delta = fit_y[-1]-fit_y[-2]

	x_end = sprint_data.index[-1]
	x_start = fit_x[-1]
	x_index_delta = x_end - x_start

	forecasted_y = [(y_delta*i)+fit_y[-1] for i in range(1,x_index_delta+1)]
	forecasted_x = [i+1 for i in range(x_start,x_end)]

	new_y = fit_y+forecasted_y
	new_x = fit_x+forecasted_x

	#Add forecast data to dataframe

	sprint_data_forecast = sprint_data.copy()

	forecast_list = [np.nan for i in range(0,len(sprint_data_forecast))]
	forecast_list[new_x[0]:new_x[-1]+1] = new_y

	sprint_data_forecast['forecast'] = forecast_list

	return sprint_data_forecast

def plot_burnup(sprint_data, renderer='notebook', forecast=True):

	# Create plotly plot

	fig = go.Figure()


	fig.add_trace(go.Scatter(x=sprint_data['sprint_name'],y=sprint_data['projected_points'],
							mode='lines+text+markers',
							name='Projected total estimate',
							text=sprint_data['projected_points'].to_list(),
							textposition='top center'
							))
	fig.add_trace(go.Scatter(x=sprint_data['sprint_name'],y=sprint_data['estimated_points'],
							mode='lines+text+markers',
							name='Total workshopped points',
							text=sprint_data['estimated_points'].to_list(),
							textposition='top center'
							))
	fig.add_trace(go.Scatter(x=sprint_data['sprint_name'],y=sprint_data['cumulative_points'],
							mode='lines+text+markers',
							name='Complete points',
							text=sprint_data['cumulative_points'].to_list(),
							textposition='top center',
							line=dict(color='#58FF33'),
							connectgaps=True
							))

	if forecast==True:

		fig.add_trace(go.Scatter(x=sprint_data['sprint_name'], y =sprint_data['forecast'],
								line=dict(dash='dash',color='#D6D6D6'),
								name='Projected velocity'
								))

	fig.update_layout(template="plotly_white")
	fig.update_xaxes(tickangle=45)
	fig.update_yaxes(range=[0,sprint_data['projected_points'].max()*1.05])


	fig.show(renderer=renderer)

	#Rename figure
	if renderer=='iframe':

		new_filename = 'burnup_'+dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'.html'
		os.rename('iframe_figures/figure_0.html','iframe_figures/'+new_filename)

	return

