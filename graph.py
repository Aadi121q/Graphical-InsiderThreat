import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from flask import Flask, render_template_string

app = Flask(__name__)

def load_data():
    df = pd.read_csv('user_activities.csv', names=['ID', 'User', 'Activity', 'Date', 'Time', 'Details'])
    return df

@app.route('/')
def index():
    df = load_data()
    insider_threats = identify_insider_threats(df)
    return render_template_string(template, tables=[df.to_html(classes='data table table-striped', index=False)], titles=df.columns.values, graphs=create_graphs(df, insider_threats), threats=insider_threats.to_html(classes='data table table-striped', index=False))

def identify_insider_threats(df):
    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%m/%d %H:%M', errors='coerce')
    df['Day'] = df['DateTime'].dt.day_name()
    df['Hour'] = df['DateTime'].dt.hour
    df['Minute'] = df['DateTime'].dt.minute
    df['Weekday'] = df['DateTime'].dt.weekday

    def is_insider_threat(row):
        if row['Activity'] == 'Login':
            if (row['Hour'] == 9 and row['Minute'] >= 30) or (row['Hour'] == 10 and row['Minute'] < 30):
                return 'Early Login'
            if row['DateTime'] > row['DateTime'].replace(hour=16, minute=0):
                return 'Late Login'
            if row['Weekday'] == 4 and row['Hour'] >= 14:
                return 'Friday Afternoon Login'
        if row['Activity'] in ['File Uploaded', 'File Downloaded', 'File Renamed', 'File Deleted']:
            if row['DateTime'] < row['DateTime'].replace(hour=10, minute=0) or row['DateTime'] > row['DateTime'].replace(hour=16, minute=0):
                return 'Outside Working Hours Activity'
            if row['DateTime'] >= row['DateTime'].replace(hour=13, minute=30) and row['DateTime'] <= row['DateTime'].replace(hour=14, minute=0):
                return 'Lunch Break Activity'
        if row['Day'] == 'Saturday':
            return 'Saturday Activity'
        return None

    df['Insider Threat'] = df.apply(is_insider_threat, axis=1)

    # Further conditions based on multiple activities
    user_activity_counts = df.groupby(['User', 'Date']).size().reset_index(name='Activity Count')
    frequent_upload_download = user_activity_counts[user_activity_counts['Activity Count'] > 5]['User'].unique()
    frequent_delete_rename = df[(df['Activity'].isin(['File Deleted', 'File Renamed']))].groupby(['User', 'Date']).size().reset_index(name='Delete Rename Count')
    frequent_delete_rename = frequent_delete_rename[frequent_delete_rename['Delete Rename Count'] > 1]['User'].unique()

    df['Insider Threat'] = df.apply(lambda row: 'Frequent Upload/Download' if row['User'] in frequent_upload_download else row['Insider Threat'], axis=1)
    df['Insider Threat'] = df.apply(lambda row: 'Frequent Delete/Rename' if row['User'] in frequent_delete_rename else row['Insider Threat'], axis=1)

    return df[df['Insider Threat'].notna()]

def create_graphs(df, insider_threats):
    graphs = []

    # Graph 1: Scatter Plot for Login Time Analysis
    login_times = df[df['Activity'] == 'Login']
    login_times['Time'] = login_times['DateTime'].dt.time
    fig1 = px.scatter(login_times, x='DateTime', y='Time', color='User', title='Login Time Analysis')
    fig1.update_layout(yaxis_title='Login Time', xaxis_title='Date')
    graphs.append(fig1.to_html(full_html=False))

    # Graph 2: Group Bar Chart for File Activities (Upload, Edit, Download)
    file_activities = df[df['Activity'].isin(['File Uploaded', 'File Downloaded', 'File Renamed', 'File Deleted'])]
    file_activities_count = file_activities.groupby(['Activity', 'User']).size().reset_index(name='Count')
    fig2 = px.bar(file_activities_count, x='User', y='Count', color='Activity', barmode='group', title='File Activities Count by User')
    fig2.update_layout(yaxis_title='Count', xaxis_title='User')
    graphs.append(fig2.to_html(full_html=False))

    # Graph 3: Bullet Chart for File Size Analysis (Upload and Download)
    df['Details'] = df['Details'].astype(str).fillna('')
    df['File Size'] = df['Details'].str.extract(r'Size: (\d+) bytes')[0].astype(float).fillna(0)
    file_size_by_activity = df[df['Activity'].isin(['File Uploaded', 'File Downloaded'])].groupby(['Activity', 'User'])[['File Size']].sum().reset_index()
    bullet_figs = []
    for activity in ['File Uploaded', 'File Downloaded']:
        activity_data = file_size_by_activity[file_size_by_activity['Activity'] == activity]
        for _, row in activity_data.iterrows():
            fig3 = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = row['File Size'],
                title = {'text': f"{activity} Size for {row['User']}"},
                domain = {'x': [0.1, 1], 'y': [0.1, 1]}
            ))
            bullet_figs.append(fig3.to_html(full_html=False))
    graphs.extend(bullet_figs)

    # Graph 4: Pie Chart for File Renamed Analysis
    renamed_files = df[df['Activity'] == 'File Renamed']
    renamed_files['Count'] = 1
    renamed_files_count = renamed_files.groupby('User')['Count'].sum().reset_index()
    fig4 = px.pie(renamed_files_count, values='Count', names='User', title='File Renamed Count by User')
    graphs.append(fig4.to_html(full_html=False))

    # Graph 5: Histogram for Insider Threats
    fig5 = px.histogram(insider_threats, x='User', color='Insider Threat', title='Distribution of Insider Threats')
    fig5.update_layout(yaxis_title='Count', xaxis_title='User')
    graphs.append(fig5.to_html(full_html=False))
    return graphs

template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CSV Data Visualization</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: url('https://www.transparenttextures.com/patterns/connected.png');
        }
        h1, h2 {
            color: #333;
            text-align: center;
        }
        .table-wrapper {
            overflow-y: auto;
            max-height: 300px;
            margin: auto;
        }
        .table-wrapper table {
            width: 100%;
        }
        .data th, .data td {
            border: 1px solid #ccc;
            padding: 8px;
            text-align: left;
        }
        .data th {
            background-color: #f2f2f2;
        }
        .graph {
            margin-bottom: 30px;
        }
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>CSV Data Visualization</h1>
        <h2>Data Table</h2>
        <div class="table-wrapper">
            {% for table in tables %}
                {{ table|safe }}
            {% endfor %}
        </div>
        <h2>Graphs</h2>
        {% for graph in graphs %}
            <div class="graph">{{ graph|safe }}</div>
        {% endfor %}
        <h2>Insider Threats</h2>
        <div class="table-wrapper">
            {{ threats|safe }}
        </div>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)