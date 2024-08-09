import socket
import json
import threading
import time
import random
import uuid

class CTSPServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.prices = {'BTC': 500.0, 'ETH': 30.0, 'DOGE': 0.5}
        self.users = {
            'Satoshi': {'password': 'bitcoin123', 'balance': 10000, 'portfolio': {'BTC': 1, 'ETH': 5, 'DOGE': 1000}}
        }
        self.trade_history = {}

    def start(self):
        self._setup_server()
        self._start_price_update_thread()
        self._accept_clients()

    def _setup_server(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server listening on {self.host}:{self.port}")

    def _start_price_update_thread(self):
        price_thread = threading.Thread(target=self._update_prices)
        price_thread.daemon = True
        price_thread.start()

    def _accept_clients(self):
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"New connection from {addr}")
                self._start_client_thread(client_socket)
            except Exception as e:
                print(f"Error accepting client connection: {e}")

    def _start_client_thread(self, client_socket):
        client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
        client_thread.start()

    def _handle_client(self, client_socket):
        player_id = None
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                request = self._parse_request(data)
                response = self._process_request(request)
                client_socket.send(response.encode('utf-8'))
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            if player_id and player_id in self.clients:
                del self.clients[player_id]
            client_socket.close()

    def _parse_request(self, data):
        print("\n"+data)
        lines = data.split('\n')
        headers = {}
        payload = None

        for i, line in enumerate(lines):
            if i == 0:
                continue
            if line.strip() == '':
                if i + 1 < len(lines):
                    try:
                        payload = json.loads(lines[i + 1])
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON payload: {lines[i + 1]}")
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

        return {
            'command': lines[0].split()[1] if len(lines[0].split()) > 1 else '',
            'player_id': headers.get('player-id'),
            'payload': payload
        }

    def _process_request(self, request):
        command = request['command']
        player_id = request['player_id']
        payload = request['payload']
        
        handlers = {
            'ENTER': self._handle_enter,
            'EXIT': self._handle_exit,
            'SCAN': self._handle_scan,
            'BUY': self._handle_buy,
            'SELL': self._handle_sell,
            'CHECK': self._handle_check,
            'RANK': self._handle_rank
        }
        
        handler = handlers.get(command)
        if handler:
            status, response_data = handler(player_id, payload)
            if command == 'ENTER' and status == "200 OK":
                player_id = response_data['player_id']
            return self._create_response(status, player_id, response_data)
        else:
            return self._create_response("400 Bad Request", player_id, {"error": "Invalid command"})

    def _handle_enter(self, player_id, data):
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return "400 Bad Request", {"error": "Username and password are required"}
        
        if username in self.users and self.users[username]['password'] == password:
            return self._login_existing_user(username)
        elif username not in self.users:
            return self._create_new_user(username, password)
        else:
            return "401 Unauthorized", {"error": "Invalid credentials"}

    def _login_existing_user(self, username):
        player_id = str(uuid.uuid4())  
        self.clients[player_id] = {'username': username}
        return "200 OK", {
            "message": f"Welcome back, {username}!",
            "balance": self.users[username]['balance'],
            "player_id": player_id
        }

    def _create_new_user(self, username, password):
        player_id = str(uuid.uuid4())  
        self.users[username] = {'password': password, 'balance': 10000, 'portfolio': {}}
        self.clients[player_id] = {'username': username}
        return "200 OK", {
            "message": f"Welcome, {username}! Your account has been created.",
            "balance": 10000,
            "player_id": player_id
        }

    def _handle_exit(self, player_id, data):
        if player_id in self.clients:
            del self.clients[player_id]
            return "200 OK", {"message": "Logout successful"}
        return "400 Bad Request", {"error": "Not logged in"}

    def _handle_scan(self, player_id, data):
        if player_id not in self.clients:
            return "400 Bad Request", {"error": "User not logged in"}
        return "200 OK", {"market_data": [
            {"coin": coin, "price": price, "change_24h": f"{random.uniform(-10, 10):.1f}%"}
            for coin, price in self.prices.items()
        ]}

    def _handle_buy(self, player_id, data):
        if player_id not in self.clients:
            return "400 Bad Request", {"error": "User not logged in"}
        
        username = self.clients[player_id]['username']
        coin = data.get('coin')
        amount = data.get('amount')
        
        if not coin or not amount:
            return "400 Bad Request", {"error": "Coin and amount are required"}
        
        try:
            amount = float(amount)
        except ValueError:
            return "400 Bad Request", {"error": "Invalid amount"}
        
        if coin in self.prices:
            return self._process_buy(username, coin, amount)
        return "400 Bad Request", {"error": "Invalid coin"}

    def _process_buy(self, username, coin, amount):
        total_cost = amount * self.prices[coin]
        if self.users[username]['balance'] >= total_cost:
            self.users[username]['balance'] -= total_cost
            self.users[username]['portfolio'][coin] = self.users[username]['portfolio'].get(coin, 0) + amount
            self._add_to_trade_history(username, 'BUY', coin, amount, self.prices[coin])
            return "200 OK", {
                "message": f"Purchase successful",
                "transaction": {
                    "coin": coin,
                    "amount": amount,
                    "price": self.prices[coin],
                    "total": total_cost
                },
                "new_balance": self.users[username]['balance']
            }
        else:
            return "400 Bad Request", {"error": "Insufficient funds"}

    def _handle_sell(self, player_id, data):
        if player_id not in self.clients:
            return "400 Bad Request", {"error": "User not logged in"}
        
        username = self.clients[player_id]['username']
        coin = data.get('coin')
        amount = data.get('amount')
        
        if not coin or not amount:
            return "400 Bad Request", {"error": "Coin and amount are required"}
        
        try:
            amount = float(amount)
        except ValueError:
            return "400 Bad Request", {"error": "Invalid amount"}
        
        if coin in self.prices and coin in self.users[username]['portfolio']:
            return self._process_sell(username, coin, amount)
        return "400 Bad Request", {"error": "Invalid coin or insufficient balance"}

    def _process_sell(self, username, coin, amount):
        if self.users[username]['portfolio'].get(coin, 0) >= amount:
            total_value = amount * self.prices[coin]
            self.users[username]['balance'] += total_value
            self.users[username]['portfolio'][coin] -= amount
            self._add_to_trade_history(username, 'SELL', coin, amount, self.prices[coin])
            return "200 OK", {
                "message": "Sale successful",
                "transaction": {
                    "coin": coin,
                    "amount": amount,
                    "price": self.prices[coin],
                    "total": total_value
                },
                "new_balance": self.users[username]['balance']
            }
        else:
            return "400 Bad Request", {"error": "Insufficient coins"}

    def _handle_check(self, player_id, data):
        if player_id not in self.clients:
            return "400 Bad Request", {"error": "User not logged in"}
        
        username = self.clients[player_id]['username']
        check_type = data.get('type')
        if not check_type:
            return "400 Bad Request", {"error": "Check type is required"}
        
        if check_type == 'portfolio':
            return self._check_portfolio(username)
        elif check_type == 'history':
            return self._check_history(username)
        return "400 Bad Request", {"error": "Invalid check type"}

    def _check_portfolio(self, username):
        return "200 OK", {
            "portfolio": self.users[username]['portfolio'],
            "balance": self.users[username]['balance'],
            "total_value": self._calculate_total_value(username)
        }

    def _check_history(self, username):
        return "200 OK", {"history": self.trade_history.get(username, [])}

    def _handle_rank(self, player_id, data):
        if player_id not in self.clients:
            return "400 Bad Request", {"error": "User not logged in"}
        
        leaderboard = sorted(
            [(username, self._calculate_total_value(username)) for username in self.users],
            key=lambda x: x[1],
            reverse=True
        )
        return "200 OK", {
            "leaderboard": [
                {"username": username, "total_value": value}
                for username, value in leaderboard[:10]
            ]
        }

    def _calculate_total_value(self, username):
        portfolio_value = sum(amount * self.prices.get(coin, 0) for coin, amount in self.users[username]['portfolio'].items())
        return self.users[username]['balance'] + portfolio_value

    def _update_prices(self):
        while True:
            time.sleep(5)
            for coin in self.prices:
                self.prices[coin] *= (1 + (random.random() - 0.5) * 0.02)

    def _create_response(self, status, player_id, body):
        body_json = json.dumps(body)
        
        headers = f"CTSP/1.0 {status}\n"
        if player_id:
            headers += f"Player-ID: {player_id}\n"
        
        return f"{headers}\n{body_json}"

    def _add_to_trade_history(self, username, trade_type, coin, amount, price):
        if username not in self.trade_history:
            self.trade_history[username] = []
        self.trade_history[username].append({
            "type": trade_type,
            "coin": coin,
            "amount": amount,
            "price": price,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })

if __name__ == "__main__":
    server = CTSPServer()
    server.start()