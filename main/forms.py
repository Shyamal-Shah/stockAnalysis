from django import forms

INTERVALS = (
    ('1m', '1 minute'),
    ('2m', '2 minute'),
    ('5m', '5 minute'),
    ('15m', '15 minute'),
    ('30m', '30 minute'),
    ('60m', '60 minute'),
    ('90m', '90 minute'),
    ('1h', '1 hour'),
    ('1d', '1 day'),
    ('5d', '5 day'),
    ('1wk', '1 week'),
    ('1mo', '1 month'),
    ('3mo', '3 month'),
)
PERIODS = (
    ('1d', '1 day'),
    ('5d', '5 day'),
    ('1mo', '1 month'),
    ('3mo', '3 month'),
    ('6mo', '6 month'),
    ('1y', '1 year'),
    ('2y', '2 year'),
    ('5y', '5 year'),
    ('10y', '10 year'),
    ('ytd', 'year-to-date'),
    ('max', 'Max'),
)
CHARTS = (
    ('Candlestick', 'Candlestick'),
    ('OHLC', 'OHLC'),
)

EQUITY_TYPES = (
    ('AAPL', 'APPLE'),
    ('AMZN', 'AMAZON'),
    ('GOOGL', 'GOOGLE'),
    ('MSFT', 'MICROSOFT'),
    ('FB', 'FACEBOOK'),
    ('NFLX', 'NETFLIX'),
    ('TSLA', 'TESLA'),
    ('TWTR', 'TWITTER'),
    ('CMCSA', 'COMCAST'),
    ('CSCO', 'CISCO'),
    ('NSEI^', 'NIFTY')
)


class MainForm(forms.Form):

    equityName = forms.ChoiceField(
        choices=EQUITY_TYPES, widget=forms.Select(attrs={'class': 'custom-select'}), label='Equity Name', required=True, initial=EQUITY_TYPES[0][0]
    )

    interval = forms.ChoiceField(
        choices=INTERVALS, widget=forms.Select(attrs={'class': 'custom-select'}), label='Interval', required=True, initial=INTERVALS[0][0]
    )

    period = forms.ChoiceField(
        choices=PERIODS, widget=forms.Select(attrs={'class': 'custom-select'}), label='Period', required=True, initial=PERIODS[0][0])

    chartType = forms.ChoiceField(
        choices=CHARTS, widget=forms.Select(attrs={'class': 'custom-select'}), label='Chart', required=True, initial=CHARTS[0][0])

    rsiStatus = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'class': 'custom-control-input'}),
        required=False, label='RSI: Relative Strength Index', initial=False)
    macdStatus = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'class': 'custom-control-input'}),
        required=False, label='MACD: Moving Average Convergence Divergence', initial=False)

    ma1Status = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'class': 'custom-control-input'}), required=False, label='MA1: Moving Average', initial=False)
    ma2Status = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'class': 'custom-control-input'}),
        required=False, label='MA2: Moving Average', initial=False)

    rsiParameter = forms.IntegerField(
        required=False, min_value=1, max_value=100, label='RSI Parameter',
        initial='14', widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    macdParameters = forms.CharField(
        required=False, label='MACD Parameter',
        initial='12, 26, 9', widget=forms.TextInput(attrs={'class': 'form-control'})
    )
