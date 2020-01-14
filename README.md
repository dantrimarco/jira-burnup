# jira-burnup
Flexible JIRA burnup charts with Python

## Installation
This project was built and tested on Python 3.8.0. Compatibility with older versions of Python is not guaranteed.

To install the package dependencies, run 
```python3 -m pip install -r requirements.txt'``

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

### Example


```python
import jira_burnup as jb
```

Read JIRA configs and create the connection:


```python
config = jb.read_config()

jira = jb.create_jira_connection(config['url'], config['username'], config['password'])
```

Get data from JIRA. The only support method runs a JQL query based on a list of epics.


```python
epics = ['Team-34', 'Team-72']

issues_df = jb.get_issues_from_epics(jira, epics)

issues_df.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>key</th>
      <th>story_points</th>
      <th>status</th>
      <th>status_change_date</th>
      <th>sprint_name</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Team-137</td>
      <td>NaN</td>
      <td>Backlog</td>
      <td>2020-01-09T12:04:11.226-0600</td>
      <td></td>
    </tr>
    <tr>
      <th>1</th>
      <td>Team-136</td>
      <td>NaN</td>
      <td>Backlog</td>
      <td>2020-01-09T11:42:50.394-0600</td>
      <td></td>
    </tr>
    <tr>
      <th>2</th>
      <td>Team-134</td>
      <td>2.0</td>
      <td>Ready for Development</td>
      <td>2020-01-08T16:44:40.586-0600</td>
      <td></td>
    </tr>
    <tr>
      <th>3</th>
      <td>Team-131</td>
      <td>3.0</td>
      <td>Backlog</td>
      <td>2020-01-07T12:06:44.023-0600</td>
      <td></td>
    </tr>
    <tr>
      <th>4</th>
      <td>Team-126</td>
      <td>1.0</td>
      <td>Done</td>
      <td>2020-01-09T16:13:35.137-0600</td>
      <td>Team Sprint 4</td>
    </tr>
  </tbody>
</table>
</div>



Aggregate completed points for each sprint and create a cumulative total


```python
completed_points_per_sprint = jb.aggregate_completed_points(issues_df)

completed_points_per_sprint
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sprint_name</th>
      <th>story_points</th>
      <th>cumulative_points</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Team Sprint 1</td>
      <td>18.0</td>
      <td>18.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Team Sprint 2</td>
      <td>7.0</td>
      <td>25.0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Team Sprint 3</td>
      <td>26.0</td>
      <td>51.0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Team Sprint 4</td>
      <td>10.0</td>
      <td>61.0</td>
    </tr>
  </tbody>
</table>
</div>



Create a list of sprints with the current status of each. This list is used to determine which sprint is the latest that has been closed. It is recommended to create future sprints in JIRA to better view the forecast.


```python
sprint_df = jb.get_sprint_list(jira, config['jira_board_id'])

sprint_df
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sprint_name</th>
      <th>sprint_state</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Team Sprint 1</td>
      <td>CLOSED</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Team Sprint 2</td>
      <td>CLOSED</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Team Sprint 3</td>
      <td>CLOSED</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Team Sprint 4</td>
      <td>ACTIVE</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Team Sprint 5</td>
      <td>FUTURE</td>
    </tr>
    <tr>
      <th>5</th>
      <td>Team Sprint 6</td>
      <td>FUTURE</td>
    </tr>
    <tr>
      <th>6</th>
      <td>Team Sprint 7</td>
      <td>FUTURE</td>
    </tr>
  </tbody>
</table>
</div>



Create the total scope dataset from the above data. The first run of this function will create a master file called `sprint_data.csv`. Subsequent runs will read from and write to this file, modifying data from **only the latest closed sprint forward**


```python
sprint_data = jb.create_total_scope_data(issues_df, completed_points_per_sprint, sprint_df)

sprint_data
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sprint_name</th>
      <th>sprint_state</th>
      <th>complete_points</th>
      <th>cumulative_points</th>
      <th>projected_points</th>
      <th>estimated_points</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Team Sprint 1</td>
      <td>CLOSED</td>
      <td>18.0</td>
      <td>18.0</td>
      <td>130.0</td>
      <td>35.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Team Sprint 2</td>
      <td>CLOSED</td>
      <td>7.0</td>
      <td>25.0</td>
      <td>130.0</td>
      <td>75.0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Team Sprint 3</td>
      <td>CLOSED</td>
      <td>26.0</td>
      <td>51.0</td>
      <td>151.0</td>
      <td>113.0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Team Sprint 4</td>
      <td>ACTIVE</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>151.0</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Team Sprint 5</td>
      <td>FUTURE</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>151.0</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>5</th>
      <td>Team Sprint 6</td>
      <td>FUTURE</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>151.0</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>6</th>
      <td>Team Sprint 7</td>
      <td>FUTURE</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>151.0</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>



Now that we have the data, all that is left is to create the plot


```python
jb.plot_burnup(sprint_data)
```