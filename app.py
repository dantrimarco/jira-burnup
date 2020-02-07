import jira_burnup as jb

config = jb.read_config()

jira = jb.create_jira_connection(config['url'], config['username'], config['password'])

query = ''

issues_df = jb.get_issues(jira, query)

completed_points_per_sprint = jb.aggregate_completed_points(issues_df)

sprint_df = jb.get_sprint_list(jira, config['jira_board_id'], sprint_id_start=0, sprint_id_end=9999)

sprint_data = jb.create_total_scope_data(issues_df, completed_points_per_sprint, sprint_df, export=False, sprint_data_filename='sprint_data.csv')

sprint_data_forecast = jb.create_forecast(sprint_data)

jb.plot_burnup(sprint_data_forecast, renderer='iframe')