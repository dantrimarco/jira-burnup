from jira import JIRA
import pandas as pd
import numpy as np
import plotly as py
import plotly.graph_objects as go
import plotly.express as px
import datetime as dt
import os.path


def create_jira_connection(url, username, password):

	options = {'server':url}
	jira = JIRA(options=options, basic_auth=(username, password))

	return jira

def get_issues_from_epic_query(jira, epics):

	# Generate list of issues objects
	issues = []

	if len(epics) > 1:

		for epic in epics:
			search_query = '"Epic Link"='+epic
			
			issues+=jira.search_issues(search_query)

	
	# Generate data from issues
	issues_data = []

	for issue in issues:
		key = issue.key
		story_points = issue.fields.customfield_10004
		status = issue.fields.status.name
		status_change_date = issue.fields.statuscategorychangedate
		
		if status == 'Done':
			last_sprint = issue.fields.customfield_10101[0]
			sprint_name = last_sprint[last_sprint.find('name=')+5:last_sprint.find(',goal=')]
			

		else:
			sprint_name = ''
		
		issue_dict = {
			'key': key,
			'story_points': story_points,
			'status': status,
			'status_change_date': status_change_date,
			'sprint_name': sprint_name
			
		}
		
		issues_data.append(issue_dict)

	issues_df = pd.DataFrame(issues_data)

	return issues_df

def aggregate_completed_points(issues_df):

	done_issues = issues_df[issues_df['status']=='Done']
	
	completed_points_per_sprint = done_issues.groupby('sprint_name')['story_points'].agg(sum).reset_index()

	completed_points_per_sprint['cumulative_points'] = completed_points_per_sprint['story_points'].cumsum()

	return completed_points_per_sprint


def get_sprint_list(jira):

	sprints = jira.sprints(233)

	sprint_data = []

	for sprint in sprints:
		name = sprint.name
		state = sprint.state
		
		sprint_dict = {
			'sprint_name':name,
			'sprint_state':state
		}
		
		sprint_data.append(sprint_dict)

	sprint_df = pd.DataFrame(sprint_data)

	return sprint_df

def create_total_scope_data(issues_df, completed_points_per_sprint, sprint_df, sprint_data_filename='sprint_data.csv'):

	if os.path.isfile('sprint_data.csv') == False:

		sprint_data = sprint_df.merge(completed_points_per_sprint,how='left',on='sprint_name')

		latest_sprint = sprint_data[sprint_data['sprint_state']=='CLOSED']['sprint_name'].iloc[-1]

		#Assign projected points based on average points for all stories

		sprint_data['projected_points'] = round(len(issues_df)*issues_df['story_points'].mean())

		# Calculate the total story points that have estimates in the JIRA data

		sprint_data['estimated_points'] = np.nan

		sprint_data.loc[sprint_data['sprint_name']<=latest_sprint,'estimated_points'] = issues_df['story_points'].sum()

		sprint_data.to_csv(sprint_data_filename)


	elif os.path.isfile('sprint_data.csv') == True:

		sprint_data = pd.read_csv(sprint_data_filename,index_col=0)
	
		# Create backup with time-based filename
		timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		filename = 'sprint_data_backup_'+timestamp+'.csv'

		# Write data
		sprint_data.to_csv(sprint_data_filename)

		# Get the latest CLOSED sprint
		latest_sprint = sprint_data[sprint_data['sprint_state']=='CLOSED']['sprint_name'].iloc[-1]

		# Get the value for complete/cumulative points in this sprint from the aggregate JIRA data
		latest_sprint_complete_points = completed_points_per_sprint[completed_points_per_sprint['sprint_name']==latest_sprint]['story_points'].values[0]
		latest_sprint_cumulative_points = completed_points_per_sprint[completed_points_per_sprint['sprint_name']==latest_sprint]['cumulative_points'].values[0]

		# Calculate the projected points based on the average story points for all stories in the JIRA data
		latest_projected_points = round(len(issues_df)*issues_df['story_points'].mean())

		# Calculate the total story points that have estimates in the JIRA data
		latest_estimated_points = issues_df['story_points'].sum()

		 # Assign updated values for complete, cumulative and estimated points to this current sprint

		sprint_data.loc[sprint_data['sprint_name']==latest_sprint, ['complete_points','cumulative_points','estimated_points']] = [latest_sprint_complete_points, latest_sprint_cumulative_points, latest_estimated_points]

		# Assign updated values for projected points to the current and all future sprints
		sprint_data.loc[sprint_data['sprint_name']>=latest_sprint,'projected_points'] = latest_projected_points 

		# Write to file

		sprint_data.to_csv(sprint_data_filename)

		
	return sprint_data


def plot_burnup(sprint_data, display=True):

	# Filter sprint_data to plot only sprints that are CLOSED

	completed_sprints = sprint_data[sprint_data['sprint_state']=='CLOSED']

	# Calculate trendline data

	trendline = px.scatter(x=completed_sprints.index.to_list(),y=completed_sprints['cumulative_points'],trendline='ols').data[1]
	fit_y = trendline['y'].tolist()

	y_delta = fit_y[-1]-fit_y[-2]

	x_delta = len(sprint_data)-len(fit_y)

	forecasted_y = [(y_delta*i)+fit_y[-1] for i in range(1,x_delta+1)]

	new_y = fit_y+forecasted_y


	# Create plotly plot

	fig = go.Figure()


	fig.add_trace(go.Scatter(x=sprint_data['sprint_name'],y=sprint_data['projected_points'],
							mode='lines+text+markers',
							name='Projected scope',
							text=sprint_data['projected_points'].to_list(),
							textposition='top center'
							))
	fig.add_trace(go.Scatter(x=sprint_data['sprint_name'],y=sprint_data['estimated_points'],
							mode='lines+text+markers',
							name='Estimated scope',
							text=sprint_data['estimated_points'].to_list(),
							textposition='top center'
							))
	fig.add_trace(go.Scatter(x=sprint_data['sprint_name'],y=sprint_data['cumulative_points'],
							mode='lines+text+markers',
							name='Completed points',
							text=sprint_data['cumulative_points'].to_list(),
							textposition='top center',
							line=dict(color='#58FF33')
							))
	fig.add_trace(go.Scatter(x=sprint_data['sprint_name'], y = new_y,
							line=dict(dash='dash',color='#D6D6D6'),
							name='Velocity projection'
							))
	fig.update_layout(template="plotly_white")

	if display==True:

		fig.show()

	return

