import dash
from dash import dcc, html, Input, Output, State, no_update
import plotly.graph_objects as go
import pandas as pd
import requests
import time
from datetime import datetime

# =============================================================================
# 1. 应用初始化及布局
# =============================================================================

PLAYER_NAMES = {
    # 在这里预设一些已知的玩家ID和名称
    "114514": "老玩家",
    "9226643": "伊咪塔",
}

# [新增] 定义一些常见的时区选项
# 标签是用户看到的，值是标准的IANA时区数据库名称
TIMEZONE_OPTIONS = [
    {'label': '新加坡 (SGT, UTC+8)', 'value': 'Asia/Singapore'},
    {'label': '协调世界时 (UTC)', 'value': 'UTC'},
    {'label': '中国上海 (CST, UTC+8)', 'value': 'Asia/Shanghai'},
    {'label': '日本东京 (JST, UTC+9)', 'value': 'Asia/Tokyo'},
    {'label': '英国伦敦 (GMT/BST)', 'value': 'Europe/London'},
    {'label': '美国纽约 (EST/EDT)', 'value': 'America/New_York'},
    {'label': '美国洛杉矶 (PST/PDT)', 'value': 'America/Los_Angeles'},
]


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "星痕共鸣分时段伤害统计图"

app.layout = html.Div(children=[
    dcc.Store(id='history-store', storage_type='memory'),

    html.H1(children='星痕共鸣分时段增量伤害图', style={'textAlign': 'center'}),

    # --- API和控制面板 ---
    html.Div([
        # API URL输入框
        html.Div([
            dcc.Input(
                id='api-url-input',
                type='text',
                placeholder='请输入API服务器地址, 例如: http://127.0.0.1:8080',
                style={'width': '98%', 'margin-bottom': '10px'}
            ),
        ], style={'width': '100%'}),
        
        # 控制按钮
        html.Div([
            html.Button('开始', id='start-btn', n_clicks=0, style={'margin-right': '10px'}),
            html.Button('停止', id='stop-btn', n_clicks=0, style={'margin-right': '10px'}),
            html.Button('清空数据', id='clear-btn', n_clicks=0),
        ], style={'display': 'inline-block', 'vertical-align': 'middle'}),

        # 时间窗口长度滑动条
        html.Div([
            html.Label('统计窗口 (秒):', style={'margin-left': '20px', 'margin-right': '10px'}),
            dcc.Slider(
                id='interval-slider', min=0.5, max=10, step=0.5, value=5,
                marks={i: f'{i}s' for i in range(1, 11)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
        ], style={'width': '35%', 'display': 'inline-block', 'vertical-align': 'middle'}),

        # [新增] 时区选择下拉菜单
        html.Div([
            html.Label('选择时区:', style={'margin-left': '20px', 'margin-right': '10px'}),
            dcc.Dropdown(
                id='timezone-dropdown',
                options=TIMEZONE_OPTIONS,
                value='Asia/Singapore', # 默认值为新加坡时区
                clearable=False,
                style={'width': '220px'}
            ),
        ], style={'display': 'inline-block', 'vertical-align': 'middle'}),

    ], style={'padding': '10px', 'border': '1px solid #ddd', 'border-radius': '5px', 'margin-bottom': '20px'}),

    # --- 筛选和图表 ---
    # ... [这部分布局与之前完全相同] ...
    html.Div([
        html.Div([
            html.Label('选择要显示的玩家:'),
            dcc.Dropdown(
                id='user-dropdown',
                multi=True
            ),
        ], style={'width': '70%', 'display': 'inline-block'}),
        html.Div([
            dcc.Checklist(
                id='auto-add-checklist',
                options=[{'label': ' 自动添加新玩家', 'value': 'auto-add'}],
                value=['auto-add'],
                style={'margin-left': '20px'}
            )
        ], style={'width': '25%', 'display': 'inline-block', 'vertical-align': 'top', 'padding-top': '25px'}),
    ], style={'margin-bottom': '20px'}),
    
    dcc.Graph(id='live-graph', config={'displayModeBar': True}),
    dcc.Interval(id='interval-component', interval=2 * 1000, n_intervals=0, disabled=True),
    html.Div(id='status-output', style={'margin-top': '10px', 'font-style': 'italic'})
])

# =============================================================================
# 2. 回调函数
# =============================================================================

# --- 回调1: 控制定时器 (与之前相同) ---
@app.callback(
    Output('interval-component', 'disabled'),
    Input('start-btn', 'n_clicks'),
    Input('stop-btn', 'n_clicks'),
    prevent_initial_call=True
)
def control_interval(start_clicks, stop_clicks):
    triggered_id = dash.callback_context.triggered_id
    if triggered_id == 'start-btn': return False
    if triggered_id == 'stop-btn': return True
    return no_update

# --- 回调2: 主图表和数据更新逻辑 (核心改动) ---
@app.callback(
    Output('live-graph', 'figure'),
    Output('history-store', 'data'),
    Output('user-dropdown', 'options'),
    Output('user-dropdown', 'value'),
    Output('status-output', 'children'),
    # 主要触发器
    Input('interval-component', 'n_intervals'),
    # 其他控制参数
    Input('interval-slider', 'value'),
    Input('auto-add-checklist', 'value'),
    Input('timezone-dropdown', 'value'), # [新增] 时区选择作为输入
    # 使用State而不是Input
    State('api-url-input', 'value'),
    State('history-store', 'data'),
    State('user-dropdown', 'value')
)
def update_graph_and_data(n, interval_seconds, auto_add_list, selected_timezone, api_url, history_data, selected_users):
    history_data = history_data or []
    selected_users = selected_users or []
    
    # ... [API数据获取部分与之前相同] ...
    # 为了保持代码简洁，这部分逻辑省略，它负责填充 history_data
    if api_url:
        try:
            response = requests.get(f"{api_url.strip('/')}/api/data", timeout=2)
            response.raise_for_status()
            api_response = response.json()
            new_data = api_response.get("user", {})
            current_time_display = datetime.now().strftime('%H:%M:%S')
            for uid, user_data in new_data.items():
                last_entry = next((item for item in reversed(history_data) if item['user_id'] == uid), None)
                current_damage = user_data.get("total_damage", {}).get("total", 0)
                if not last_entry or last_entry['damage'] != current_damage:
                    history_data.append({'timestamp': time.time(), 'user_id': uid, 'damage': current_damage})
                if uid not in PLAYER_NAMES: PLAYER_NAMES[uid] = f"玩家_{uid}"
            status_msg = f"数据已于 {current_time_display} 更新"
        except Exception as e:
            status_msg = f"获取数据时出错: {e}"
    else:
        status_msg = "请输入API服务器地址并点击“开始”。"
        # 即使没有URL，也要继续执行以渲染已有数据
    
    if not history_data:
        # 提供一个空的figure对象以避免错误
        fig = go.Figure().update_layout(title="等待数据中...")
        return fig, [], [], [], status_msg

    # --- B. 数据处理：使用自定义窗口和时区 ---
    df = pd.DataFrame(history_data)
    
    # [核心改动] 时区处理
    # 1. 将unix时间戳转换为UTC时区的datetime对象
    df['timestamp_utc'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
    # 2. 将UTC时间转换为用户选择的目标时区
    df['timestamp_local'] = df['timestamp_utc'].dt.tz_convert(selected_timezone)
    df = df.set_index('timestamp_local') # 使用本地化时间作为索引

    # ... [动态下拉框和自动添加逻辑与之前相同] ...
    all_known_users = {uid: PLAYER_NAMES.get(uid, f"玩家_{uid}") for uid in df['user_id'].unique()}
    dropdown_options = [{'label': name, 'value': uid} for uid, name in all_known_users.items()]
    is_auto_add_enabled = 'auto-add' in auto_add_list
    if is_auto_add_enabled:
        users_for_plotting = list(all_known_users.keys())
    else:
        users_for_plotting = selected_users

    if not users_for_plotting:
        fig = go.Figure().update_layout(title="请在下拉框中选择要显示的玩家", xaxis_title="时间", yaxis_title=f"{interval_seconds}秒内伤害量")
        return fig, history_data, dropdown_options, users_for_plotting, status_msg
        
    df_filtered = df[df['user_id'].isin(users_for_plotting)]
    
    # [核心改动] 使用动态频率和本地化时间索引进行重采样
    freq_str = f"{int(interval_seconds * 1000)}L"
    pivot_df = df_filtered.pivot_table(index=df_filtered.index, columns='user_id', values='damage')
    # 使用UTC时间进行计算，避免夏令时等问题导致的计算错误
    pivot_df_utc = df_filtered.pivot_table(index='timestamp_utc', columns='user_id', values='damage')
    resampled_df_utc = pivot_df_utc.resample('1S').ffill()
    dps_df = resampled_df_utc.diff().fillna(0)
    interval_damage_df = dps_df.resample(freq_str).sum()
    # 将计算结果的UTC索引转换回目标时区以用于绘图
    interval_damage_df.index = interval_damage_df.index.tz_convert(selected_timezone)
    
    # --- C. 创建图表 ---
    fig = go.Figure()
    sorted_users = interval_damage_df.sum().sort_values().index
    for user_id in sorted_users:
        user_name = PLAYER_NAMES.get(user_id, f"玩家_{user_id}")
        fig.add_trace(go.Scatter(
            x=interval_damage_df.index, y=interval_damage_df[user_id],
            mode='lines', name=user_name, stackgroup='one', line={'width': 0.5}
        ))

    fig.update_layout(
        title=f'分时段增量伤害图 (每{interval_seconds}秒)',
        xaxis_title=f'时间 ({selected_timezone})', # 在坐标轴标题中显示当前时区
        yaxis_title=f'{interval_seconds}秒内伤害量',
        legend_title='玩家列表', hovermode='x unified'
    )
    
    return fig, history_data, dropdown_options, users_for_plotting, status_msg

# --- 回调3: 清空数据 (与之前相同) ---
@app.callback(
    Output('history-store', 'data', allow_duplicate=True),
    Output('status-output', 'children', allow_duplicate=True),
    Input('clear-btn', 'n_clicks'),
    State('api-url-input', 'value'),
    prevent_initial_call=True
)
def clear_all_data(n_clicks, api_url):
    status_msg = ""
    # ... [函数体与之前相同] ...
    if api_url:
        try:
            requests.get(f"{api_url.strip('/')}/api/clear", timeout=2)
            status_msg = "服务器和本地统计数据已清空。"
        except Exception as e:
            status_msg = f"清空服务器数据失败，但本地数据已清空。错误: {e}"
    else:
        status_msg = "API地址为空，仅清空本地数据。"
    return [], status_msg


# --- 应用启动入口 ---
if __name__ == '__main__':
    app.run(debug=True, port=8050)