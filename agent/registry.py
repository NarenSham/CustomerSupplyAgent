"""Add a new capability by writing a Tool subclass in tools/ and listing it here."""
from tools.check_inventory import CheckInventory
from tools.confirm_order import ConfirmOrder
from tools.draft_order import DraftOrder
from tools.order_status import OrderStatus

TOOLS = [CheckInventory(), DraftOrder(), ConfirmOrder(), OrderStatus()]
BY_NAME = {t.name: t for t in TOOLS}
