from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_auto_price_enabled = fields.Boolean(string="Precio de venta automático")
    x_formula_type = fields.Selection(
        selection=[("percent", "Porcentaje"), ("factor", "Coeficiente"), ("fixed", "Suma fija")],
        string="Tipo de fórmula",
    )
    x_formula_value = fields.Float(
        string="Valor de fórmula",
        digits="Product Price",
    )
    x_formula_source = fields.Selection(
        selection=[("product", "Producto"), ("category", "Categoría")],
        string="Origen de fórmula",
        compute="_compute_formula_metadata",
        store=True,
        readonly=True,
    )
    x_formula_type_effective = fields.Selection(
        selection=[("percent", "Porcentaje"), ("factor", "Coeficiente"), ("fixed", "Suma fija")],
        string="Tipo de fórmula efectivo",
        compute="_compute_formula_metadata",
        store=True,
        readonly=True,
    )
    x_formula_value_effective = fields.Float(
        string="Valor efectivo",
        digits="Product Price",
        compute="_compute_formula_metadata",
        store=True,
        readonly=True,
    )

    @api.depends(
        "x_formula_type",
        "x_formula_value",
        "categ_id.x_default_formula_type",
        "categ_id.x_default_formula_value",
    )
    def _compute_formula_metadata(self):
        for product in self:
            formula = product._select_formula()
            if formula:
                product.x_formula_source = formula["source"]
                product.x_formula_type_effective = formula["type"]
                product.x_formula_value_effective = formula["value"]
            else:
                product.x_formula_source = False
                product.x_formula_type_effective = False
                product.x_formula_value_effective = 0.0

    def _select_formula(self):
        """Choose the product-specific formula or fall back to category defaults."""
        self.ensure_one()
        if self.x_formula_type:
            return {
                "source": "product",
                "type": self.x_formula_type,
                "value": self.x_formula_value,
            }
        if self.categ_id and self.categ_id.x_default_formula_type:
            return {
                "source": "category",
                "type": self.categ_id.x_default_formula_type,
                "value": self.categ_id.x_default_formula_value,
            }
        return None

    def _is_auto_price_enabled(self):
        """Only the product flag controls automation; categories set defaults on creation."""
        self.ensure_one()
        return bool(self.x_auto_price_enabled)

    def _compute_sale_price_from_formula(self, formula_type, formula_value):
        cost = self.standard_price
        if formula_type == "percent":
            new_price = cost * (1 + (formula_value or 0.0) / 100.0)
        elif formula_type == "factor":
            new_price = cost * (formula_value or 0.0)
        elif formula_type == "fixed":
            new_price = cost + (formula_value or 0.0)
        else:
            new_price = self.list_price
        currency = self.currency_id or self.company_id.currency_id
        if currency:
            new_price = currency.round(new_price)
        return new_price

    def _apply_auto_sale_price(self, force=False):
        if self.env.context.get("skip_auto_sale_price"):
            return
        for product in self:
            if not product._is_auto_price_enabled():
                continue
            formula = product._select_formula()
            if not formula:
                continue
            new_price = product._compute_sale_price_from_formula(
                formula["type"], formula["value"]
            )
            precision_rounding = (
                product.currency_id.rounding if product.currency_id else 0.01
            )
            if not force and float_compare(
                product.list_price, new_price, precision_rounding=precision_rounding
            ) == 0:
                continue
            product.with_context(skip_auto_sale_price=True).write(
                {"list_price": new_price}
            )

    @api.onchange(
        "x_auto_price_enabled",
        "x_formula_type",
        "x_formula_value",
        "standard_price",
        "categ_id",
    )
    def _onchange_auto_price_fields(self):
        for product in self:
            if not product._is_auto_price_enabled():
                continue
            formula = product._select_formula()
            if not formula:
                continue
            product.list_price = product._compute_sale_price_from_formula(
                formula["type"], formula["value"]
            )

    @api.onchange("categ_id")
    def _onchange_categ_id_defaults(self):
        for product in self:
            if (
                product.categ_id
                and not product.x_formula_type
                and product.categ_id.x_default_formula_type
            ):
                product.x_formula_type = product.categ_id.x_default_formula_type
                product.x_formula_value = product.categ_id.x_default_formula_value
            if (
                product.categ_id
                and not product.x_auto_price_enabled
                and product.categ_id.x_default_auto_price_enabled
            ):
                product.x_auto_price_enabled = True

    @api.model
    def _apply_category_defaults_to_vals(self, vals):
        categ_id = vals.get("categ_id")
        if not categ_id:
            return vals
        category = self.env["product.category"].browse(categ_id)
        if (
            not vals.get("x_formula_type")
            and category
            and category.x_default_formula_type
        ):
            vals["x_formula_type"] = category.x_default_formula_type
        if (
            "x_formula_value" not in vals
            and category
            and category.x_default_formula_type
        ):
            vals["x_formula_value"] = category.x_default_formula_value
        if (
            "x_auto_price_enabled" not in vals
            and category
            and category.x_default_auto_price_enabled
        ):
            vals["x_auto_price_enabled"] = True
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [
            self._apply_category_defaults_to_vals(vals.copy()) for vals in vals_list
        ]
        products = super().create(vals_list)
        products._apply_auto_sale_price(force=True)
        return products

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get("skip_auto_sale_price"):
            return res
        trigger_fields = {
            "standard_price",
            "x_auto_price_enabled",
            "x_formula_type",
            "x_formula_value",
            "categ_id",
        }
        if trigger_fields.intersection(vals):
            self._apply_auto_sale_price(force=True)
        return res

    def action_recompute_sale_price(self):
        self._apply_auto_sale_price(force=True)
        return True
