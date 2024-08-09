import socket
import json
from terminaltables import AsciiTable
from colorama import Fore, Style, init

init(autoreset=True)

class CTSPClient:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.socket = None
        self.player_id = None
        self.logged_in = False

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"{Fore.RED}Error connecting to server: {e}{Style.RESET_ALL}")
            return False

    def send_request(self, command, payload=None):
        if not self.socket:
            if not self.connect():
                return None, None

        request = f"CTSP/1.0 {command}\n"
        if self.player_id:
            request += f"Player-ID: {self.player_id}\n"
        if payload:
            request += f"\n{json.dumps(payload)}"
        else:
            request += "\n"

        try:
            self.socket.send(request.encode())
            response = self.socket.recv(4096).decode()
        except Exception as e:
            print(f"{Fore.RED}Error communicating with server: {e}{Style.RESET_ALL}")
            return None, None

        # Parse the response
        lines = response.split('\n')
        status_line = lines[0].split()
        status_code = int(status_line[1]) if len(status_line) > 1 else 500
        try:
            body = json.loads(lines[-1]) if lines[-1] else None
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error decoding server response: {lines[-1]}{Style.RESET_ALL}")
            body = None

        # Update player_id if it's in the response
        if body and 'player_id' in body:
            self.player_id = body['player_id']
            self.logged_in = True

        return status_code, body

    def login(self, username, password):
        status_code, body = self.send_request('ENTER', {
            'username': username,
            'password': password
        })
        if status_code == 200:
            self.logged_in = True
        return status_code, body

    def logout(self):
        if self.logged_in:
            status_code, body = self.send_request('EXIT')
            if status_code == 200:
                self.player_id = None
                self.logged_in = False
            return status_code, body
        return 400, {"error": "Not logged in"}

    def get_prices(self):
        if not self.logged_in:
            return None
        status_code, body = self.send_request('SCAN')
        if status_code == 200 and body:
            return body.get('market_data', [])
        return None

    def trade(self, trade_type, coin, amount):
        if not self.logged_in:
            return 400, {"error": "Not logged in"}
        return self.send_request(trade_type, {
            'coin': coin,
            'amount': float(amount)
        })

    def get_portfolio(self):
        if not self.logged_in:
            return None
        status_code, body = self.send_request('CHECK', {'type': 'portfolio'})
        if status_code == 200 and body:
            return body
        return None

    def get_leaderboard(self):
        if not self.logged_in:
            return None
        status_code, body = self.send_request('RANK')
        if status_code == 200 and body:
            return body.get('leaderboard', [])
        return None
def print_menu():
    menu = [
        ['Crypto Trading Simulator'],
        ['1. Login', '5. Buy'],
        ['2. Logout', '6. Sell'],
        ['3. Get Prices', '7. View Portfolio'],
        ['4. View Dashboard', '8. View Leaderboard'],
        ['0. Exit']
    ]
    table = AsciiTable(menu)
    table.inner_heading_row_border = False
    print(f"\n{Fore.CYAN}{table.table}{Style.RESET_ALL}")

def format_currency(value):
    try:
        return f"${float(value):.2f}"
    except (ValueError, TypeError):
        return "$0.00"

def print_prices(prices):
    if prices:
        data = [['Coin', 'Price', 'Change (24h)']]
        for coin in prices:
            data.append([
                coin.get('coin', 'Unknown'),
                format_currency(coin.get('price', 0)),
                coin.get('change_24h', '0%')
            ])
        table = AsciiTable(data)
        print(f"\n{Fore.GREEN}Current Prices:{Style.RESET_ALL}")
        print(table.table)
    else:
        print(f"{Fore.RED}Unable to fetch prices.{Style.RESET_ALL}")

def print_portfolio(portfolio):
    if portfolio:
        data = [['Coin', 'Amount']]
        for coin, amount in portfolio.get('portfolio', {}).items():
            data.append([coin, amount])
        table = AsciiTable(data)
        print(f"\n{Fore.GREEN}Your Portfolio:{Style.RESET_ALL}")
        print(table.table)
        print(f"Balance: {format_currency(portfolio.get('balance', 0))}")
        print(f"Total Value: {format_currency(portfolio.get('total_value', 0))}")
    else:
        print(f"{Fore.RED}Unable to fetch portfolio.{Style.RESET_ALL}")

def print_dashboard(client):
    prices = client.get_prices()
    portfolio = client.get_portfolio()

    print(f"\n{Fore.CYAN}{'=' * 40}")
    print(f"{Fore.CYAN}{'Dashboard':^40}")
    print(f"{Fore.CYAN}{'=' * 40}{Style.RESET_ALL}")

    print_prices(prices)
    print_portfolio(portfolio)

def print_leaderboard(leaderboard):
    if leaderboard:
        data = [['Rank', 'Username', 'Total Value']]
        for i, user in enumerate(leaderboard, 1):
            data.append([
                i,
                user.get('username', 'Unknown'),
                format_currency(user.get('total_value', 0))
            ])
        table = AsciiTable(data)
        print(f"\n{Fore.GREEN}Leaderboard:{Style.RESET_ALL}")
        print(table.table)
    else:
        print(f"{Fore.RED}Unable to fetch leaderboard.{Style.RESET_ALL}")

def main():
    client = CTSPClient()

    while True:
        print_menu()
        choice = input(f"{Fore.YELLOW}Enter your choice: {Style.RESET_ALL}")

        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            status, message = client.login(username, password)
            print(f"{Fore.GREEN if status == 200 else Fore.RED}Status: {status}, Message: {json.dumps(message)}{Style.RESET_ALL}")

        elif choice == '2':
            status, message = client.logout()
            print(f"{Fore.GREEN if status == 200 else Fore.RED}Status: {status}, Message: {json.dumps(message)}{Style.RESET_ALL}")

        elif choice == '3':
            if not client.logged_in:
                print(f"{Fore.RED}You must be logged in to perform this action.{Style.RESET_ALL}")
                continue
            prices = client.get_prices()
            print_prices(prices)

        elif choice == '4':
            if not client.logged_in:
                print(f"{Fore.RED}You must be logged in to perform this action.{Style.RESET_ALL}")
                continue
            print_dashboard(client)

        elif choice in ['5', '6']:
            if not client.logged_in:
                print(f"{Fore.RED}You must be logged in to perform this action.{Style.RESET_ALL}")
                continue
            trade_type = 'BUY' if choice == '5' else 'SELL'
            coin = input("Enter coin (BTC/ETH/DOGE): ").upper()
            amount = input("Enter amount: ")
            try:
                amount = float(amount)
                status, message = client.trade(trade_type, coin, amount)
                print(f"{Fore.GREEN if status == 200 else Fore.RED}Status: {status}, Message: {json.dumps(message)}{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Invalid amount. Please enter a number.{Style.RESET_ALL}")

        elif choice == '7':
            if not client.logged_in:
                print(f"{Fore.RED}You must be logged in to perform this action.{Style.RESET_ALL}")
                continue
            portfolio = client.get_portfolio()
            print_portfolio(portfolio)

        elif choice == '8':
            if not client.logged_in:
                print(f"{Fore.RED}You must be logged in to perform this action.{Style.RESET_ALL}")
                continue
            leaderboard = client.get_leaderboard()
            print_leaderboard(leaderboard)

        elif choice == '0':
            print(f"{Fore.CYAN}Thank you for using Crypto Trading Simulator. Goodbye!{Style.RESET_ALL}")
            break

        else:
            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()