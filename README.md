# Crypto Trading Simulator Protocol (CTSP)

## Overview

The Crypto Trading Simulator Protocol (CTSP) is an application-layer protocol designed for a cryptocurrency trading simulation platform. It facilitates communication between clients and servers in a virtual trading environment, allowing users to practice trading strategies without real financial risk.

## Protocol Specification

### Message Format

#### Request:
```
CTSP/1.0 COMMAND
Player-ID: <player_id>

{JSON payload}
```

#### Response:
```
CTSP/1.0 STATUS_CODE
Player-ID: <player_id>

{JSON payload}
```

### Commands

1. `ENTER`: Log in or create a new account
2. `EXIT`: Log out
3. `SCAN`: View market data
4. `BUY`: Purchase cryptocurrency
5. `SELL`: Sell cryptocurrency
6. `CHECK`: Check portfolio or transaction history
7. `RANK`: View user rankings

### Status Codes

- `200 OK`: Successful operation
- `400 Bad Request`: Invalid request or missing required data
- `401 Unauthorized`: Authentication failure

## Usage Examples

### 1. Login (ENTER)

Request:
```
CTSP/1.0 ENTER

{"username": "Satoshi", "password": "bitcoin123"}
```

Response:
```
CTSP/1.0 200 OK
Player-ID: 123456

{"message": "Welcome back, Satoshi!", "balance": 10000, "player_id": "123456"}
```

### 2. View Market Data (SCAN)

Request:
```
CTSP/1.0 SCAN
Player-ID: 123456

```

Response:
```
CTSP/1.0 200 OK
Player-ID: 123456

{
  "market_data": [
    {"coin": "BTC", "price": 50000.00, "change_24h": "2.5%"},
    {"coin": "ETH", "price": 3000.00, "change_24h": "-1.2%"},
    {"coin": "DOGE", "price": 0.50, "change_24h": "5.0%"}
  ]
}
```

### 3. Buy Cryptocurrency (BUY)

Request:
```
CTSP/1.0 BUY
Player-ID: 123456

{"coin": "BTC", "amount": 0.5}
```

Response:
```
CTSP/1.0 200 OK
Player-ID: 123456

{
  "message": "Purchase successful",
  "transaction": {
    "coin": "BTC",
    "amount": 0.5,
    "price": 50000.00,
    "total": 25000.00
  },
  "new_balance": 85000.00
}
```

### 4. Check Portfolio (CHECK)

Request:
```
CTSP/1.0 CHECK
Player-ID: 123456

{"type": "portfolio"}
```

Response:
```
CTSP/1.0 200 OK
Player-ID: 123456

{
  "portfolio": {
    "BTC": 0.5,
    "ETH": 3.0,
    "DOGE": 1000
  },
  "balance": 85000.00,
  "total_value": 110000.00
}
```

## Error Handling

In case of an error, the server will respond with an appropriate status code and an error message:

```
CTSP/1.0 400 Bad Request
Player-ID: 123456

{"error": "Insufficient funds", "details": "Your balance is too low for this transaction"}
```
