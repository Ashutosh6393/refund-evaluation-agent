import logging
from datetime import date

from data import users_data
from dotenv import load_dotenv
from langchain.tools import tool
from objects import PurchaseItem

load_dotenv()

@tool
def get_user_purchase_history(username: str) -> list[PurchaseItem]:
    """this tool takes the username as input and returns the purchase history of the user if the user exists in the database"""

    logging.info(f"Getting purchase history for user: {username}")

    if username not in users_data:
        logging.error(f"User {username} not found in the database")
    
    return users_data[username]


@tool
def calculate_right_refund(username:str, items:list[PurchaseItem])-> str:
    """this tool takes the username and the list of items as input and returns the right refund for the user if the user exists in the database"""

    logging.info(f"Calculating right refund for user: {username} and items: {items}")

    if username not in users_data:
        logging.error(f"User {username} not found in the database")

    total_refund = 0

    for item in items:
        total_refund += users_data[username][item.name]["price"]

    return f"the value of the refund is: {total_refund}"


@tool
def issue_refund_ticket(user:str, refund_amount: int) -> str:
    """this tool will send a ticket to the right team to return the refund"""

    logging.info(f"using issue_refund_ticket for user: {user}")
    return f"a refund ticket has been issued successfully with the amount of {refund_amount}"

@tool
def get_today_date() -> str:
    """Return today's date in YYYY-MM-DD format
    This tool takes no arguments
    only use if a user exist and an item is present for refund"""
    logging.info(f"using the date tool")
    return date.today().isoformat()




# print(get_user_purchase_history.invoke("user123"))
# book = PurchaseItem(name="book")
# pen = PurchaseItem(name="pen")
# print(calculate_right_refund.invoke({"username": "user123", "items": [book, pen]}))
# print(issue_refund_ticket.invoke({"user":"user123",  "refund_amount":30}))
# print(get_today_date.invoke("user123"))