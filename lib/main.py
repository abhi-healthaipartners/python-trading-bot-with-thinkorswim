
import time
from src.services.logger import LoggerService
from src.utils.helper import Helper
from src.services.tda import TDA
from src.models.user_model import User
from src.services.database import Database
from src.services.gmail import Gmail
from src.trader import Trader


class Main(Database):

    def __init__(self) -> None:
        super().__init__()

        self.logger = LoggerService()
        self.gmail = Gmail(self.logger)

        self.usersToTrade = {}
        self.usersNotConnected = []

    def setupUsers(self):

        users = self.getUsers()
        for user in users:
            user: User = user
            try:
                for accountId in user.accounts.keys():
                    if accountId not in self.usersToTrade and accountId not in self.usersNotConnected:
                        tda = TDA(int(accountId),
                                  user.accounts[accountId], self.logger, user)
                        connected = tda.connect()

                        if not connected:
                            self.usersNotConnected.append(accountId)
                            continue

                        self.usersToTrade[accountId] = Trader(
                            tda, user, self.logger)

                        self.logger.info(
                            f"User {user.name} ready to trade. - Account ID: {Helper.modifiedAccountID(accountId)}\n")

                        time.sleep(0.1)

            except Exception as e:
                self.logger.error(
                    f"Error setting up user {user.name}  - Account ID: {Helper.modifiedAccountID(accountId)}: {e}")

    def runTrader(self):
        orders = self.gmail.getEmails()

        for user in self.usersToTrade:
            trader: Trader = self.usersToTrade[user]
            trader.trade(orders)

        if len(orders) > 0:
            print("--------------------------------------------------")


if __name__ == "__main__":

    """
    This program is a trading bot that trades based on emails sent to a gmail account.
    The emails sent to the gmail account are alerts that are sent from Thinkorswim.
    Alerts are sent when scanners within TOS find a stock that meets a strategies criteria to either buy or sell.

    Only LONG positions are allowed by default. You are able to modify the code to allow for SHORT positions.
    By default, paper trading is enabled. You are able to enable live trading if you wish. Good practice would be to run the bot in paper trading mode for a while to make sure it is working correctly.

    WARNING: This bot is not perfect. It is a work in progress. There are many things that can go wrong. I am not responsible for any losses you may incur. Use at your own risk.
    """

    main = Main()

    connected = main.gmail.connect()

    if connected:

        main.setupUsers()

        if len(main.usersToTrade) == 0:
            main.logger.info("No users to trade. Exiting...")
            exit()

        main.logger.info(
            "Starting Trading Bot...")

        print("\n--------------------------------------------------\n")

        while True:
            main.runTrader()
            time.sleep(5)
