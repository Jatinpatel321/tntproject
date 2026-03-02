import app.modules.group_cart.model  # noqa
import app.modules.feedback.model  # noqa
import app.modules.complaints.model  # noqa
import app.modules.ledger.model  # noqa
import app.modules.menu.model  # noqa
import app.modules.notifications.model
import app.modules.orders.history_model  # noqa
import app.modules.orders.model  # noqa
import app.modules.payments.model  # noqa
import app.modules.rewards.model  # noqa
import app.modules.slots.model  # noqa
import app.modules.stationery.job_model
import app.modules.stationery.service_model

# 🔥 FORCE IMPORT MODELS
import app.modules.users.model  # noqa
from app.database.base import Base
from app.database.session import engine


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
