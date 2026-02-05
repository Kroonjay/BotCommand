"""Calculate and update action costs based on current prices."""

from logging import getLogger

logger = getLogger(__name__)


async def calculate_action_cost(ctx):
    """Calculate net cost of actions based on input/output item prices."""
    db = ctx.get("db")
    actions = await db.action.find_many(
        include={
            "requirements": {"include": {"item": True}},
            "inputs": {"include": {"item": True}},
            "outputs": {"include": {"item": True}},
        }
    )
    last_result = {"action_id": None, "cost": 0}

    for action in actions:
        cost = 0
        if action.cost is None:
            continue

        # Add cost from inputs (items consumed when taking the action)
        for input_item in action.inputs:
            itemprice = await db.itemprice.find_first(
                where={"item_source_id": input_item.item_source_id},
                order={"created_at": "desc"},
            )
            if itemprice is None:
                logger.error(
                    f"Item price not found for item {input_item.item_source_id} | Action {action.id}"
                )
                continue
            cost += itemprice.average_price * input_item.quantity
        logger.info(f"Calculated Input Cost for Action {action.id} |  Cost: {cost}")

        # Subtract value from outputs (items produced by the action)
        for output in action.outputs:
            itemprice = await db.itemprice.find_first(
                where={"item_source_id": output.item_source_id},
                order={"created_at": "desc"},
            )
            if itemprice is None:
                logger.error(
                    f"Item price not found for item {output.item_source_id} | Action {action.id}"
                )
                continue
            cost -= itemprice.average_price * output.quantity
        logger.info(f"Calculated Output Cost for Action {action.id} |  Cost: {cost}")
        logger.info(f"Calculated Total Cost for Action {action.id} |  Cost: {cost}")

        if cost != action.cost:
            cost_per_hour = cost * action.actions_per_hour
            await db.action.update(
                where={"id": action.id},
                data={"cost": cost, "cost_per_hour": cost_per_hour},
            )
            logger.info(
                f"Updated Cost for Action {action.id} |  Cost: {cost} | Cost Per Hour: {cost_per_hour}"
            )
        else:
            cost_per_hour = cost * action.actions_per_hour
            logger.info(
                f"Cost for Action {action.id} is already up to date |  Cost: {cost} | Cost Per Hour: {cost_per_hour}"
            )
        last_result = {"action_id": action.id, "cost": cost}
    return last_result
