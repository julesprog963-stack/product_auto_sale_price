from odoo import fields, models
from odoo.exceptions import AccessError


class ProductCategory(models.Model):
    _inherit = "product.category"

    x_default_auto_price_enabled = fields.Boolean(
        string="Activar cálculo automático por defecto",
        help="Si está activo, los productos nuevos en esta categoría habilitan el cálculo automático.",
    )
    x_default_formula_type = fields.Selection(
        selection=[("percent", "Porcentaje"), ("factor", "Coeficiente"), ("fixed", "Suma fija")],
        string="Tipo de fórmula por defecto",
        help="Configuración heredable para productos sin fórmula propia.",
    )
    x_default_formula_value = fields.Float(
        string="Valor de fórmula por defecto",
        digits="Product Price",
    )

    def write(self, vals):
        if not self.env.user.has_group(
            "product_auto_sale_price.group_auto_sale_price_manager"
        ):
            for key in ("x_default_formula_type", "x_default_formula_value", "x_default_auto_price_enabled"):
                if key in vals:
                    raise AccessError(
                        "No tienes permisos para usar el cálculo automático de precio."
                    )
        res = super().write(vals)
        trigger_fields = {"x_default_formula_type", "x_default_formula_value"}
        if trigger_fields.intersection(vals):
            products = self.env["product.template"].search(
                [
                    ("categ_id", "in", self.ids),
                    ("x_auto_price_enabled", "=", True),
                    ("x_formula_type", "=", False),
                ]
            )
            if products:
                products._apply_auto_sale_price(force=True)
        return res
