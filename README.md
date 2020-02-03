# jira-burnup

Flexible JIRA burnup charts with Python

## Installation

This project was built and tested on Python 3.8.0. Compatibility with older versions of Python is not guaranteed.

To install the package dependencies, run

```python3 -m pip install -r requirements.txt```

## Usage

### Prerequisites

Before using, you must modify `jira_config.yaml` with the necessary data:

```yaml
url: 'https://vividseats.atlassian.net/'
username: '<your email address>'
password: '<your API token>'
jira_board_id: '<your_jira_board_id>'
```

To create an API token, visit https://id.atlassian.com/manage-profile/security. JIRA board ID can be found in the URL of your team's board. For example, `jira_board_id = 233` for the following url URL: https://vividseats.atlassian.net/secure/RapidBoard.jspa?rapidView=233&projectKey=MPLS

### Important considerations

Due to the disjoined nature of JIRA data, this script is not perfect. It is **strongly recommended** that you consdier the following when running:

* Only issues marked as `Done` will be counted as completed in a sprint
* If an issue was completed outside of a sprint, it will be counted in the last sprint in which it was worked on
* Modified estimates of issues of closed sprints are not updated retroactively
* Projected story points and estimated story points cannot be calculated retroactively. Upon the first run of this script, historical data will be identical to the latest sprint
* The forecast considers `cumulative_points` from the previous 3 sprints. Adding future sprints in JIRA controls how far into the future the forecast is projected

### Example


```python
import jira_burnup as jb
```

Read JIRA configs and create the connection:


```python
config = jb.read_config()

jira = jb.create_jira_connection(config['url'], config['username'], config['password'])
```

Get data from JIRA from a JQL query.

```python
query = '"Epic Link"=MPLS-34 OR "Epic Link"=MPLS-72'

issues_df = jb.get_issues(jira, query)

issues_df.head()
```

![issues_df](https://github.com/dantrimarco/jira-burnup/blob/master/images/issues_df.png)

Aggregate completed points for each sprint and create a cumulative total


```python
completed_points_per_sprint = jb.aggregate_completed_points(issues_df)

completed_points_per_sprint
```

![completed_points_per_sprint](https://github.com/dantrimarco/jira-burnup/blob/master/images/completed_points_per_sprint.png)



Create a list of sprints with the current status of each. This list is used to determine which sprint is the latest that has been closed. It is recommended to create future sprints in JIRA to better view the forecast.


```python
sprint_df = jb.get_sprint_list(jira, config['jira_board_id'])

sprint_df
```

![sprint_df](https://github.com/dantrimarco/jira-burnup/blob/master/images/sprint_df.png)



Create the total scope dataset from the above data. The first run of this function will create a master file called `sprint_data.csv`. Subsequent runs will read from and write to this file, modifying data from **only the latest closed sprint forward**


```python
sprint_data = jb.create_total_scope_data(issues_df, completed_points_per_sprint, sprint_df, export=False)

sprint_data
```

![sprint_data](https://github.comdantrimarco/jira-burnup/blob/master/images/sprint_data.png)


With the most recently closed sprint data updated, we need to create the forecast data. This forecast is an ordinary least squares regression. It will extend to the sprints that are defined in JIRA.


```python
sprint_data = jb.create_forecast(sprint_data)

sprint_data
```

![sprint_data_with_forecast](https://github.com/dantrimarco/jira-burnup/blob/master/images/sprint_data_with_forecast.png)



Now that we have the data, all that is left is to create the plot


```python
jb.plot_burnup(sprint_data, renderer='notebook')
```

![forecast_plot](https://github.com/dantrimarco/jira-burnup/blob/master/images/forecast_plot.png)

Definitions for each calculated value that appears on the graph:
* **"Projected total estimate"** (`projected_points`): Count of total stories * average points per story. Used to roughly estimate the total scope of the project while accounting for issues that have not yet been workshopped
* **"Total workshopped points"** (`estimated_points`): Total story points for issues with estimates. The delta between this line and `projected_points` is the magnitude of unestimated issues
* **"Complete points"** (`cumulative_points`): Cumulative total of story points completed
* **"Projected velocity"** An ordinary least squares regression of `complete_points` over the previous 3 sprints


```python

```
