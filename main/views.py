from django.shortcuts import render
from django.http import HttpResponse
from . import forms
import plotly.graph_objects as go
from plotly.offline import plot
import yfinance as yf
from plotly.subplots import make_subplots


def calculate_rsi(df, period=13):
    net_change = df['Close'].diff()
    increase = net_change.clip(lower=0)
    decrease = -1*net_change.clip(upper=0)
    ema_up = increase.ewm(com=period, adjust=False).mean()
    ema_down = decrease.ewm(com=period, adjust=False).mean()
    RS = ema_up/ema_down
    df['RSI'] = 100 - (100/(1+RS))
    return df


def generate_table(df):
    df = calculate_rsi(df)
    df['date'] = df.index.date.astype(str)
    df_group = df.groupby(['date']).agg({
        'Close': ['mean', 'std', lambda x: x.iloc[0], lambda x: x.iloc[-1]],
        'RSI': ['mean'],
    }).round(2)
    df_group.columns = [x[1] for x in df_group.columns]
    df_group = df_group.reset_index()
    df_group.columns = ['Date', 'Mean Price',
                        'STD Price', 'Start', 'End', 'RSI Mean']
    df_group['Net Change'] = (df_group['Start'] - df_group['End']).round(2)
    df_group = df_group[['Date', 'Mean Price', 'STD Price',
                         'RSI Mean', 'Start', 'End', 'Net Change']]  # Re-ordering
    return df_group


def update_chart(form):
    if form is None:
        print('Form is none')
        ticker = 'AAPL'
        interval = '1m'
        period = '1d'
    else:
        print('Form is not none')
        ticker = form.cleaned_data['equity_name']
        interval = form.cleaned_data['interval']
        period = form.cleaned_data['period']

    # Get the data from yfinance
    rolling_period = 15
    df = yf.download(ticker, interval=interval, period=period)
    df = calculate_rsi(df, rolling_period)
    df_group = generate_table(df)

    fig = go.Figure(make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        vertical_spacing=0.05,
        specs=[[{}], [{}], [{}], [{"type": "table"}]]
    ))

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name=ticker +
            ' Candlestick',
            increasing_line_color='rgb(27,158,119)', decreasing_line_color='rgb(204,80,62)'
        ), row=1, col=1,
    )

    # Bollinger Bands
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df['Close'],
            name=ticker+' Price', marker_color='#0099C6'
        ), row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=list(df.index)+list(df.index[::-1]),
            y=list(df['Close'].transform(lambda x: x.rolling(rolling_period, 1).mean(
            )) + (2*df['Close'].transform(lambda x: x.rolling(rolling_period, 1).std())))
            + list(df['Close'].transform(lambda x: x.rolling(rolling_period, 1).mean()) - (
                2*df['Close'].transform(lambda x: x.rolling(rolling_period, 1).std()))[::-1]),
            fill='toself',
            fillcolor='rgba(0,176,246,0.2)', line_color='rgba(255,255,255,0)',
            name='Bollinger Bands', showlegend=False,
        ), row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index, y=df['Close'].transform(
                lambda x: x.rolling(rolling_period, 1).mean()),
            line=dict(dash='dot'), marker_color='rgba(0,176,246,0.2)',
            showlegend=False, name='Moving Average'
        ), row=2, col=1,
    )

    # RSI
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df['RSI'],
            name='RSI', marker_color='#109618'
        ), row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=[70] * len(df.index),
            name='Overbought', marker_color='#109618',
            line=dict(dash='dot'), showlegend=False,
        ), row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=[30] * len(df.index),
            name='Oversold', marker_color='#109618',
            line=dict(dash='dot'), showlegend=False,
        ), row=3, col=1,
    )

    # Table
    fig.add_trace(
        go.Table(
            header=dict(
                values=list(df_group.columns),
                font=dict(size=10), align="left"),
            cells=dict(
                values=[df_group[k].tolist() for k in df_group.columns[0:]], align="left")
        ), row=4, col=1
    )
    fig.update_layout(
        title=ticker + ' Report',
        yaxis_title='Price',
        xaxis1_rangeslider_visible=False,
        height=800,
        width=1500
    )

    return plot(fig, output_type='div')


def main(request):
    if request.method == 'POST':
        print('POST')
        form = forms.MainForm(request.POST)
        if form.is_valid():
            print('valid')
            context = {'form': form, 'chart': update_chart(
                form), 'title': form.cleaned_data['equity_name']}
            return render(request, 'main/index.html', context)

    print('GET')
    form = forms.MainForm()
    context = {'form': form, 'chart': update_chart(None), 'title': 'Apple'}
    return render(request, 'main/index.html', context)
