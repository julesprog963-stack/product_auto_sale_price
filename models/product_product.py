from odoo import fields, models
from odoo.exceptions import AccessError
from odoo.tools.float_utils import float_compare


class ProductProduct(models.Model):
    _inherit = "product.product"

    x_auto_price_enabled = fields.Boolean(
        related="product_tmpl_id.x_auto_price_enabled",
        readonly=False,
    )

    def _compute_sale_price_from_formula(self, cost, formula_type, formula_value):
        if formula_type == "percent":
            new_price = cost * (1 + (formula_value or 0.0) / 100.0)
        elif formula_type == "factor":
            new_price = cost * (formula_value or 0.0)
        elif formula_type == "fixed":
            new_price = cost + (formula_value or 0.0)
        else:
            new_price = self.product_tmpl_id.list_price
        currency = self.product_tmpl_id.currency_id or self.product_tmpl_id.company_id.currency_id
        if currency:
            new_price = currency.round(new_price)
        return new_price

    def action_recompute_sale_price(self):
        if not self.env.user.has_group(
            "product_auto_sale_price.group_auto_sale_price_manager"
        ):
            raise AccessError("No tienes permisos para recalcular precios de venta.")
        for product in self:
            template = product.product_tmpl_id
            if not template.x_auto_price_enabled:
                continue
            formula = template._select_formula()
            if not formula:
                continue
            new_price = product._compute_sale_price_from_formula(
                product.standard_price, formula["type"], formula["value"]
            )
            precision_rounding = (
                template.currency_id.rounding if template.currency_id else 0.01
            )
            if float_compare(
                template.list_price, new_price, precision_rounding=precision_rounding
            ) == 0:
                continue
            template.with_context(skip_auto_sale_price=True).write(
                {"list_price": new_price}
            )
        return True
