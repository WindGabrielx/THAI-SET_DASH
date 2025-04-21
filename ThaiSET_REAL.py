
from dash import Dash, Output, html, dcc, Input
import dash_bootstrap_components as dbc
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots  ## <-- เพิ่ม make_subplots สำหรับ subplot

# สร้าง Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# ตั้งค่าช่วงเวลาเริ่มต้น
start_date = "2023-01-01"
end_date = pd.to_datetime("today").strftime('%Y-%m-%d')

# กำหนดหุ้นไทยที่ใช้
tickers = ["PTT.BK", "CPALL.BK", "SCB.BK"]

# Layout ของ Dash
app.layout = dbc.Container([
    html.Div([
        html.H1("ThaiSET", className='Topic', style={'textAlign': 'center'})
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='category',
                value=[tickers[0]],
                multi=True,
                clearable=False,
                options=[{'label': ticker, 'value': ticker} for ticker in tickers]
            )
        ], width=4),

        dbc.Col([
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date=start_date,
                end_date=end_date,
                display_format='YYYY-MM-DD',
                style={'width': '100%'}
            )
        ], width=4)
    ], justify='between', className='my-3'),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='line-graph-plotly')
        ])
    ])
], fluid=True)

# Callback สำหรับอัปเดตกราฟ
@app.callback(
    Output(component_id='line-graph-plotly', component_property='figure'),
    Input(component_id='category', component_property='value'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_graph(selected_tickers, start_date, end_date):
    if not isinstance(selected_tickers, list):
        selected_tickers = [selected_tickers]

    # สร้าง subplot 2 แถว: Candlestick และ Volume
    fig = make_subplots(
        rows=2, cols=1,                             ## เพิ่ม subplot layout
        shared_xaxes=True,                         ## แชร์แกน X
        shared_yaxes=True,                         ## แชร์แกน y
        row_heights=[7, 2],                         ##  ปรับความสูงของแถว
        vertical_spacing=0.05,                     ## ระยะห่างระหว่างแถว
        subplot_titles=("Candlestick", "Volume")   ## ชื่อ subplot
    )

    for ticker in selected_tickers:
        df = yf.download(ticker, start=start_date, end=end_date)

        if df.empty:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        ##ทำการเพิ่ม EMA
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA100'] = df['Close'].ewm(span=100, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

        ##ทำการเพิ่ม SMA
        df['SMA30'] = df['Close'].rolling(window=30).mean()


        # กำหนดสี Volume แดง/เขียว ตามราคาเปิดปิด
        colors = ['green' if df['Close'][i] > df['Open'][i] else 'red' for i in range(len(df))]  ## เพิ่ม logic กำหนดสี

        # กราฟแท่งเทียน
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=ticker,
            increasing_line_color='green',
            decreasing_line_color='red'
        ), row=1, col=1)  ## เพิ่มใน subplot row 1
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['EMA50'],
            mode='lines',
            line=dict(color='#239dfc', width=1.5),
            name="EMA50"
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['EMA100'],
            mode='lines',
            line=dict(color='red', width=1.5),
            name="EMA100"
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['EMA200'],
            mode='lines',
            line=dict(color='#d3d909', width=1.5),
            name="EMA200"
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['SMA30'],
            mode='lines',
            line=dict(color='orange', width=5, dash='dash'),
            name="SMA30"
        ), row=1, col=1)
        
        
        
        # กราฟปริมาณการซื้อขาย (Volume)
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            marker_color=colors,
            name=ticker+'_Volume'
        ), row=2, col=1)  ## เพิ่มใน subplot row 2

    fig.update_layout(
        title='Stock Price and Volume',
        xaxis_rangeslider_visible=False,  ## ปิดแถบ slider ด้านล่าง
        template='plotly_white',
        height=700,                        ## เพิ่มความสูงให้ดูชัดขึ้น
        hovermode='x unified'
    )
    

    return fig

# Run app
if __name__ == '__main__':
    app.run(debug=True, port=8507)