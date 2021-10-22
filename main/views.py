from django.shortcuts import render
from django.http import HttpResponse
import numpy as np
from . import forms
import plotly.graph_objects as go
from plotly.offline import plot
import yfinance as yf
from plotly.subplots import make_subplots


def calculateRsi(df, period):
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1*delta.clip(upper=0)
    ema_up = up.ewm(com=period, adjust=False).mean()
    ema_down = down.ewm(com=period, adjust=False).mean()
    rs = ema_up/ema_down
    df['RSI'] = 100 - (100/(1 + rs))

    return df


def calculateMACD(df, paramters):
    df['k'] = df['Close'].ewm(
        span=paramters[0], adjust=False, min_periods=paramters[0]).mean()
    df['d'] = df['Close'].ewm(
        span=paramters[1], adjust=False,  min_periods=paramters[1]).mean()
    df['MACD'] = df['d'] - df['k']
    df['Signal'] = df['MACD'].ewm(
        span=paramters[2], adjust=False, min_periods=paramters[1]).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    return df


def generateTable(df, period):
    df = calculateRsi(df, period)
    df['date'] = df.index.date.astype(str)
    dfGroup = df.groupby(['date']).agg({
        'Close': ['mean', 'std', lambda x: x.iloc[0], lambda x: x.iloc[-1]],
        'RSI': ['mean'],
    }).round(2)
    dfGroup.columns = [x[1] for x in dfGroup.columns]
    dfGroup = dfGroup.reset_index()
    dfGroup.columns = ['Date', 'Mean Price',
                       'STD Price', 'Start', 'End', 'RSI Mean']
    dfGroup['Net Change'] = (dfGroup['Start'] - dfGroup['End']).round(2)
    dfGroup = dfGroup[['Date', 'Mean Price', 'STD Price',
                       'RSI Mean', 'Start', 'End', 'Net Change']]
    return dfGroup


def updateChart(form):
    plotCount = 2

    if form is None:
        emptyForm = forms.MainForm()
        print('Form is none')
        ticker = emptyForm.fields['equityName'].initial
        interval = emptyForm.fields['interval'].initial
        period = emptyForm.fields['period'].initial
        chartType = emptyForm.fields['chartType'].initial
        rsiStatus = emptyForm.fields['rsiStatus'].initial
        macdStatus = emptyForm.fields['macdStatus'].initial
        ma1Status = emptyForm.fields['ma1Status'].initial
        ma2Status = emptyForm.fields['ma2Status'].initial
        print(ticker, interval, period, chartType, rsiStatus,
              ma1Status, ma2Status, macdStatus)

    else:
        print('Form is not none')
        ticker = form.cleaned_data['equityName']
        interval = form.cleaned_data['interval']
        period = form.cleaned_data['period']
        chartType = form.cleaned_data['chartType']
        rsiStatus = form.cleaned_data['rsiStatus']
        macdStatus = form.cleaned_data['macdStatus']
        ma1Status = form.cleaned_data['ma1Status']
        ma2Status = form.cleaned_data['ma2Status']
        rsiParameter = form.cleaned_data['rsiParameter']
        macdParameters = form.cleaned_data['macdParameters']
        print(ticker, interval, period, chartType, rsiStatus, macdStatus,
              ma1Status, ma2Status, rsiParameter, macdParameters)
    # Get the data from yfinance

    df = yf.download(ticker, interval=interval, period=period)

    specs = [[{}], [{}]]
    rowHeights = [1.0, 0.3]
    subplotTitles = [chartType, 'Volume']

    if(rsiStatus):
        plotCount += 2
        df = calculateRsi(df, period=int(rsiParameter))
        df_group = generateTable(df, period=int(rsiParameter))
        specs.extend([[{}], [{"type": "table"}]])
        rowHeights.extend([0.3, 0.3])
        subplotTitles.extend(['RSI', 'RSI Table'])

    if(macdStatus):
        plotCount += 1
        df = calculateMACD(df, [int(x) for x in macdParameters.split(',')])
        rowHeights.append(0.3)
        if not rsiStatus:
            specs.append([{}])
            subplotTitles.append('MACD')
        else:
            specs.insert(-1, [{}])
            subplotTitles.insert(-1, 'MACD')

    fig = go.Figure(make_subplots(
        rows=plotCount, cols=1, shared_xaxes=True,
        vertical_spacing=0.06,
        specs=specs,
        row_heights=rowHeights,
        subplot_titles=subplotTitles
    ))

    # Candlestick chart
    if chartType == 'Candlestick':
        fig.add_trace(
            go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name=ticker + chartType,
                increasing_line_color='rgb(27,158,119)', decreasing_line_color='rgb(204,80,62)'
            ), row=1, col=1,
        )
    elif chartType == 'OHLC':
        fig.add_trace(
            go.Ohlc(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name=ticker + chartType,
                increasing_line_color='rgb(27,158,119)', decreasing_line_color='rgb(204,80,62)'
            ), row=1, col=1,
        )

    # Volume chart
    fig.add_trace(
        go.Bar(
            x=df.index, y=df['Volume'],
            marker_color='orange', showlegend=False),
        row=2, col=1
    )

    # Moving Average 1
    if(ma1Status):
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['Close'].rolling(
                    int(20)).mean(), name=ticker + 'MA1'),
            row=1, col=1
        )

    # Moving Average 2
    if(ma2Status):
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['Close'].rolling(
                    int(50)).mean(), name=ticker + 'MA2'),
            row=1, col=1
        )

    # RSI
    if rsiStatus:
        rowIndex = plotCount - 2 if macdStatus else plotCount - 1
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['RSI'],
                name='RSI', marker_color='#109618'
            ), row=rowIndex, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=[70] * len(df.index),
                name='Overbought', marker_color='#109618',
                line=dict(dash='dot'),
            ), row=rowIndex, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=[30] * len(df.index),
                name='Oversold', marker_color='#109610',
                line=dict(dash='dot'),
            ), row=rowIndex, col=1,
        )

        fig.add_trace(
            go.Table(
                header=dict(
                    values=list(df_group.columns),
                    fill_color='#C2D4FF',
                    font=dict(size=10), align="left"),
                cells=dict(
                    fill_color='#F5F8FF',
                    values=[df_group[k].tolist() for k in df_group.columns[0:]], align="left")
            ), row=plotCount, col=1
        )

    if macdStatus:
        rowIndex = plotCount - 1 if rsiStatus else plotCount
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['MACD'],
                name='MACD', marker_color='#ff9900'
            ), row=rowIndex, col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['Signal'],
                name='Signal', marker_color='#000000',
                line=dict(dash='dot'),
            ), row=rowIndex, col=1,
        )

        colors = np.where(df['Hist'] < 0, '#000', '#ff9900')

        fig.append_trace(
            go.Bar(
                x=df.index,
                y=df['Hist'],
                name='Histogram',
                marker_color=colors,
            ), row=rowIndex, col=1
        )

    fig.update_layout(
        title=ticker + ' Report',
        yaxis_title='Price',
        xaxis1_rangeslider_visible=False,
        height=800,
        width=1500,
        # xaxis_rangeslider_visible=True
    )

    return plot(fig, output_type='div')


def main(request):
    if request.method == 'POST':
        print('POST')
        form = forms.MainForm(request.POST)
        if form.is_valid():
            print('valid')
            context = {'form': form, 'chart': updateChart(
                form), 'title': dict(form.fields['equityName'].choices)[form.cleaned_data['equityName']]}
            return render(request, 'main/index.html', context)

    print('GET')
    form = forms.MainForm()
    context = {'form': form, 'chart': updateChart(None), 'title': 'Apple'}
    return render(request, 'main/index.html', context)
