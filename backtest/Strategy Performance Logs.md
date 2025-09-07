# Strategy performance log - EMA Cross 9/25 strategy

**Goal:**  
The purpose of this log is to systematically test and optimize the EMA (9/25) crossover strategy with trailing stop logic. We aim to identify the optimal combination of risk, trailing start, and other parameters to maximize profitability, win rate, and risk-adjusted returns. The secondary goal of this performane log is to use the collected resutls to find other methods to improve the profitability of the strategy. I also intend on further developing an "optimizer" program that will use machine learning to better optimize the strategy parameters to maximise profitability however for now this method (trial and error) will work fine.

---

## Program code
This is the current code being used to test the strategy and "optimize" parameters:
```python
test_risk_percent_values = [0.01, 0.03, 0.05, 0.1]
test_trail_start_values = [0.3, 0.5, 0.7, 0.9]
test_trail_on = [True, False]
test_trail_distance_valuse = [0.1, 0.25, 0.5, 0.75, 0.9]

permutations = len(test_trail_on) * len(test_risk_percent_values) * len(test_trail_start_values) * len(test_trail_distance_valuse) # 160
counter = 0
for trail_on in test_trail_on:
    for risk_percent in test_risk_percent_values:
        for start_values in test_trail_start_values:
            for trail_distance in test_trail_distance_valuse:
                counter += 1
                print(f'Permutation: {counter} of {permutations}, {permutations-counter} remaining')
                results_filename = f'results_permutation_{counter}.csv'
                folder_name = f'results_set_{counter}'
                metric_filename = f'metrics_{counter}.csv'
                run_backtest('EUR_USD', risk_percent, 850, 34560, trail_on, start_values, trail_distance, False, results_filename, folder_name, metric_filename)
```
It uses 160 different permutations and stores results in a unique csv file along with images of the charts the backtester produces to help in assessing performance (drawdown over time, equity 
curve, distribution of trade profits, cumulative pips over time). I will then build a program to process each csv file and determine which parameters are the most suited to the strategy.

The program also outputs 4 different graphs that can be used to better understand how each parameter value affects the performance of the strategy. An example output of a not-so-good strategy can be seen below. these graphs were created using: ```python run_backtest('EUR_USD', 0.03, 850, 2016, True, 0.5, 0.1, False, 'trades_1.csv', 'trade_set_1', 'metric_set_1.csv')```. 

Results:

Equity curve:
![alt text](backtest/trade_set_1/EUR_USD_equity_curve.png)

Drawdown over time:
![alt text](backtest/trade_set_1/EUR_USD_drawdown.png)

Profit distribution:
![alt text](image-2.png)

Cumulative pips over time:
![alt text](backtest/trade_set_1/EUR_USD_cumulative_pips.png)

Metrics file:
Metric,Value
| Metric                     | Value  |
|-----------------------------|--------|
| total_trades               | 36     |
| wins                       | 14     |
| losses                     | 22     |
| breakeven                  | 0      |
| win_rate                   | 38.89  |
| avg_win                    | 31.63  |
| avg_loss                   | -22.75 |
| profit_factor              | 0.88   |
| be_reached_count           | 18     |
| be_reached_pct             | 50.0   |
| trail_start_reached_count  | 16     |
| trail_start_reached_pct    | 44.44  |
| trail_failures             | 2      |
| trail_successes            | 14     |
| avg_pct_tp_captured        | 70.43  |
| avg_rrr                    | 1.18   |
| win_rate_tp                | 0.0    |


Completed Trades file:
| trade_id | instrument | action | entry_price | stop_loss | original_stop_loss | take_profit | original_take_profit | units       | open_price | highest_price | lowest_price | close_price | be_reached | win   | profit   | profit_pips | profit_usd | %_TP_reached |
|----------|------------|--------|-------------|-----------|--------------------|-------------|----------------------|-------------|------------|---------------|--------------|-------------|------------|-------|----------|-------------|------------|--------------|
| 0        | EUR_USD    | sell   | 1.1412      | 1.14226   | 1.14226            | 1.14019     | 1.14019              | 24056.60    | 1.1412     | 1.14234       | 1.14047      | 1.14226     | False      | False | -0.00106 | -10.6       | -25.5      | True         |
| 1        | EUR_USD    | sell   | 1.14025     | 1.13928   | 1.14121            |             | 1.13892              | 25765.62    | 1.14025    | 1.14067       | 1.13915      | 1.13928     | True       | False | 0.00097  | 9.7         | 24.99      | True         |
| 2        | EUR_USD    | buy    | 1.15451     | 1.1537    | 1.1537             | 1.15629     | 1.15629              | 31462.59    | 1.15451    | 1.15474       | 1.15348      | 1.1537      | False      | False | -0.00081 | -8.1        | -25.48     | False        |
| 3        | EUR_USD    | buy    | 1.15431     | 1.15654   | 1.1527             |             | 1.15574              | 15354.22    | 1.15431    | 1.15668       | 1.15406      | 1.15654     | True       | False | 0.00223  | 22.3        | 34.24      | True         |
| 4        | EUR_USD    | buy    | 1.15876     | 1.15822   | 1.15822            | 1.16004     | 1.16004              | 47680.56    | 1.15876    | 1.15887       | 1.15775      | 1.15822     | False      | False | -0.00054 | -5.4        | -25.75     | False        |
| 5        | EUR_USD    | buy    | 1.15731     | 1.15839   | 1.15649            |             | 1.15907              | 30457.32    | 1.15731    | 1.15857       | 1.15719      | 1.15839     | True       | False | 0.00108  | 10.8        | 32.89      | True         |
| 6        | EUR_USD    | buy    | 1.1569      | 1.15648   | 1.15648            | 1.15891     | 1.15891              | 61813.57    | 1.1569     | 1.15772       | 1.15643      | 1.15648     | True       | False | -0.00042 | -4.2        | -25.96     | False        |
| 7        | EUR_USD    | buy    | 1.15737     | 1.15814   | 1.15659            |             | 1.15885              | 32285.77    | 1.15737    | 1.15829       | 1.15732      | 1.15814     | True       | False | 0.00077  | 7.7         | 24.86      | True         |
| 8        | EUR_USD    | buy    | 1.15838     | 1.15692   | 1.15692            | 1.15967     | 1.15967              | 17759.38    | 1.15838    | 1.15885       | 1.15663      | 1.15692     | False      | False | -0.00146 | -14.6       | -25.93     | False        |
| 9        | EUR_USD    | buy    | 1.15842     | 1.15709   | 1.15709            | 1.16058     | 1.16058              | 18910.38    | 1.15842    | 1.15856       | 1.15593      | 1.15709     | False      | False | -0.00133 | -13.3       | -25.15     | False        |
| 10       | EUR_USD    | buy    | 1.15701     | 1.15649   | 1.15649            | 1.15862     | 1.15862              | 46915.96    | 1.15701    | 1.15737       | 1.15648      | 1.15649     | False      | False | -0.00052 | -5.2        | -24.4      | False        |
| 11       | EUR_USD    | sell   | 1.15649     | 1.15717   | 1.15717            | 1.15532     | 1.15532              | 34800.44    | 1.15649    | 1.15733       | 1.15642      | 1.15717     | False      | False | -0.00068 | -6.8        | -23.66     | False        |
| 12       | EUR_USD    | buy    | 1.15733     | 1.15667   | 1.15667            | 1.15856     | 1.15856              | 34779.55    | 1.15733    | 1.15776       | 1.15659      | 1.15667     | False      | False | -0.00066 | -6.6        | -22.95     | False        |
| 13       | EUR_USD    | sell   | 1.1565      | 1.15713   | 1.15713            | 1.15557     | 1.15557              | 35342.86    | 1.1565     | 1.15721       | 1.1564       | 1.15713     | False      | False | -0.00063 | -6.3        | -22.27     | False        |
| 14       | EUR_USD    | buy    | 1.15684     | 1.15663   | 1.15663            | 1.15817     | 1.15817              | 102847.14   | 1.15684    | 1.15686       | 1.15658      | 1.15663     | False      | False | -0.00021 | -2.1        | -21.6      | False        |
| 15       | EUR_USD    | buy    | 1.15751     | 1.15694   | 1.15694            | 1.15844     | 1.15844              | 36754.21    | 1.15751    | 1.1576        | 1.15691      | 1.15694     | False      | False | -0.00057 | -5.7        | -20.95     | False        |
| 16       | EUR_USD    | buy    | 1.15756     | 1.15787   | 1.15723            |             | 1.15818              | 61580.00    | 1.15756    | 1.15793       | 1.15751      | 1.15787     | True       | False | 0.00031  | 3.1         | 19.09      | True         |
| 17       | EUR_USD    | sell   | 1.15457     | 1.15487   | 1.15487            | 1.15237     | 1.15237              | 69647.00    | 1.15457    | 1.15489       | 1.15415      | 1.15487     | True       | False | -0.0003  | -3.0        | -20.89     | False        |
| 18       | EUR_USD    | sell   | 1.1539      | 1.15436   | 1.15436            | 1.15259     | 1.15259              | 44059.57    | 1.1539     | 1.15478       | 1.15372      | 1.15436     | False      | False | -0.00046 | -4.6        | -20.27     | False        |
| 19       | EUR_USD    | sell   | 1.15325     | 1.15347   | 1.15347            | 1.15145     | 1.15145              | 89360.45    | 1.15325    | 1.15361       | 1.15321      | 1.15347     | False      | False | -0.00022 | -2.2        | -19.66     | False        |
| 20       | EUR_USD    | buy    | 1.15758     | 1.15808   | 1.15707            |             | 1.15812              | 37391.18    | 1.15758    | 1.15813       | 1.15708      | 1.15808     | True       | False | 0.0005   | 5.0         | 18.7       | True         |
| 21       | EUR_USD    | buy    | 1.15739     | 1.15778   | 1.15701            |             | 1.15806              | 51659.21    | 1.15739    | 1.15785       | 1.15738      | 1.15778     | True       | False | 0.00039  | 3.9         | 20.15      | True         |
| 22       | EUR_USD    | buy    | 1.15827     | 1.15767   | 1.15767            | 1.15902     | 1.15902              | 33725.00    | 1.15827    | 1.15882       | 1.15755      | 1.15767     | False      | False | -0.0006  | -6.0        | -20.24     | True         |
| 23       | EUR_USD    | buy    | 1.15819     | 1.15746   | 1.15746            | 1.15915     | 1.15915              | 26887.40    | 1.15819    | 1.15833       | 1.15716      | 1.15746     | False      | False | -0.00073 | -7.3        | -19.63     | False        |
| 24       | EUR_USD    | buy    | 1.15808     | 1.15866   | 1.15753            |             | 1.15936              | 34616.18    | 1.15808    | 1.15879       | 1.15807      | 1.15866     | True       | False | 0.00058  | 5.8         | 20.08      | True         |
| 25       | EUR_USD    | buy    | 1.16555     | 1.16542   | 1.16542            | 1.16698     | 1.16698              | 151086.92   | 1.16555    | 1.16599       | 1.1653       | 1.16542     | True       | False | -0.00013 | -1.3        | -19.64     | False        |
| 26       | EUR_USD    | buy    | 1.16635     | 1.16575   | 1.16575            | 1.16715     | 1.16715              | 31753.50    | 1.16635    | 1.16658       | 1.16562      | 1.16575     | False      | False | -0.0006  | -6.0        | -19.05     | False        |
| 27       | EUR_USD    | buy    | 1.16577     | 1.1664    | 1.16531            |             | 1.1669               | 40175.22    | 1.16577    | 1.16651       | 1.16558      | 1.1664      | True       | False | 0.00063  | 6.3         | 25.31      | True         |
| 28       | EUR_USD    | buy    | 1.16595     | 1.16637   | 1.16551            |             | 1.16653              | 43727.05    | 1.16595    | 1.16643       | 1.16589      | 1.16637     | True       | False | 0.00042  | 4.2         | 18.37      | True         |
| 29       | EUR_USD    | sell   | 1.16365     | 1.16307   | 1.1638             |             | 1.16232              | 131940.00   | 1.16365    | 1.16371       | 1.16294      | 1.16307     | True       | False | 0.00058  | 5.8         | 76.53      | True         |
| 30       | EUR_USD    | sell   | 1.16451     | 1.16365   | 1.1654             |             | 1.16359              | 24816.74    | 1.16451    | 1.16459       | 1.16356      | 1.16365     | True       | False | 0.00086  | 8.6         | 21.34      | True         |
| 31       | EUR_USD    | buy    | 1.16623     | 1.16583   | 1.16583            | 1.16712     | 1.16712              | 56817.75    | 1.16623    | 1.16667       | 1.16583      | 1.16583     | True       | False | -0.0004  | -4.0        | -22.73     | False        |
| 32       | EUR_USD    | sell   | 1.16553     | 1.16495   | 1.16571            |             | 1.16419              | 122473.33   | 1.16553    | 1.16558       | 1.16482      | 1.16495     | True       | False | 0.00058  | 5.8         | 71.03      | True         |
| 33       | EUR_USD    | sell   | 1.16455     | 1.16475   | 1.16475            | 1.16383     | 1.16383              | 120880.50   | 1.16455    | 1.16478       | 1.16451      | 1.16475     | False      | False | -0.0002  | -2.0        | -24.18     | False        |
| 34       | EUR_USD    | sell   | 1.16465     | 1.16429   | 1.16489            |             | 1.16385              | 97711.25    | 1.16465    | 1.16483       | 1.16421      | 1.16429     | True       | False | 0.00036  | 3.6         | 35.18      | True         |
| 35       | EUR_USD    | buy    | 1.16692     | 1.16678   | 1.16678            | 1.16793     | 1.16793              | 175043.57   | 1.16692    | 1.16696       | 1.16677      | 1.16678     | False      | False | -0.00014 | -1.4        | -24.51     | False        |


## Experiment Metadata

- **Strategy:** EMA 9/25 Crossover  
- **Instrument:** [e.g., EUR/USD]  
- **Data Source:** [CSV or API source]  
- **Candle Count:** [Number of candles used in backtest]  
- **Date Started:** YYYY-MM-DD  
- **Date Completed:** YYYY-MM-DD  

---

## Experiment Template

| Experiment # | Risk % | Trail Start | Trail Distance | Total Trades | Wins | Losses | Breakeven | Win Rate % | Total P/L ($) | % Return | Avg RRR | Notes |
|--------------|--------|------------|---------------|-------------|------|--------|-----------|------------|---------------|----------|---------|-------|
| 1            | 0.01   | 0.25       | 0.25          |             |      |        |           |            |               |          |         |       |
| 2            | 0.01   | 0.50       | 0.25          |             |      |        |           |            |               |          |         |       |
| 3            | 0.02   | 0.25       | 0.50          |             |      |        |           |            |               |          |         |       |

*Notes on parameters:*  
- **Risk %:** Maximum account equity risked per trade.  
- **Trail Start:** % of take profit reached before trailing stop activates.  
- **Trail Distance:** Distance of the trailing stop from highest/lowest price reached after trail activation.  

---

## Observations

- [Add general observations about strategy behavior, trade clustering, drawdowns, etc.]  

---

## Recommendations / Next Steps

1. Adjust risk or trail parameters based on experiment results.  
2. Consider optimizing other parameters (EMA periods, TP distance, SL distance).  
3. Document any anomalies or unexpected behavior.  

---

