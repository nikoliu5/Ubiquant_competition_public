# High Frequency Trading System for Ubiquant Competition
This repository is dedicated to a sophisticated high-frequency trading (HFT) system developed for the Ubiquant competition. Unlike traditional market-neutral strategies, this system is engineered to capitalize on short-term market inefficiencies by processing and reacting to tick data within 100 milliseconds. The core of this system is built on asynchronous programming and multiprocessing techniques, enabling it to handle rapid streams of trading data and execute trades at an exceptionally high speed.

## Features
- Asynchronous Data Handling: Utilizes Python's asyncio library to manage simultaneous data streams and API calls without blocking, ensuring real-time data processing and decision-making.
- Multiprocessing for Speed: Implements multiprocessing to distribute data processing and model prediction tasks across multiple CPU cores, significantly enhancing computation speed.
- Compliance with Rate Limits: Designed to operate within the Ubiquant competition's strict API call rate limits (3000 calls every 10 seconds for Limit Order Book (LOB) updates, among others), ensuring uninterrupted operation.

## System Structure
```
Ubiquant High Frequency Trading System
|
├── main.py - Entry point, orchestrates the bot's operation cycle.
|
├── Neutralizer_Bot.py - Executes neutralization strategy to clear positions.
|
├── broker.py - Manages interactions with the brokerage, including orders and trades.
|   |
|   ├── submit_order() - Submits trading orders(market, best bid/ask), with detailed parameters.
|   |
|   ├── cancel_order() - Cancels existing orders via the trading API.
|   |
|   ├── get_trade_info() - Retrieves trade execution details asynchronously.
|   |
|   └── risk_management_all() - Applies risk management strategies across all trades.
|
├── data_manager.py - Handles data retrieval and management, serving as a data backbone.
|   |
|   ├── update_lob() - Asynchronously updates the Limit Order Book (LOB) data.
|   |
|   ├── fetch_stock_data() - Asynchronously fetches and processes stock data for individual stock.
|   |
|   └── get_model_data() - Prepares and outputs trading data for strategy analysis.
|
├── position_manager.py - Manages positions, leveraging data_manager for historical data.
|   |
|   ├── update_position() - Updates positions with execution details of new trades.
|   |
|   ├── calculate_pnl() - Calculates current profit and loss, adjusting positions accordingly.
|   |
|   └── calibrate() - Recalculates realized/unrealized PnL, position sizes, average prices based on trade information.
|
├── strategy.py - Encapsulates the trading strategy, making decisions based on data inputs.
|   |
|   ├── trade_decision_all() - Decision-making process for all available stocks.
|   |
|   └── trade_decision_stock() - Executes trading decisions for individual stocks.
|
├── trade_mgmt.py - Contains classes for managing trades and orders, and storing LOB data.
|   |
|   ├── Order - Represents trading orders with execution logic.
|   |
|   ├── Trade - Manages trade details post-execution.
|   |
|   └── StockData - Retains LOB data for the last 100 ticks for analysis.
|
├── interface.py - Facilitates API communication with the trading platform for data and orders.
|   |
|   ├── send_order() - Interface method to send orders to the market.
|   |
|   └── get_market_data() - Retrieves and processes market data from the trading platform.
```