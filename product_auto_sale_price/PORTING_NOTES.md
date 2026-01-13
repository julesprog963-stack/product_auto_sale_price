# Porting Notes (Odoo 17)

## Files touched
- /home/julio/odoo17-dev/custom_addons/product_auto_sale_price/models/product_product.py
- /home/julio/odoo17-dev/custom_addons/product_auto_sale_price/data/server_actions.xml
- /home/julio/odoo17-dev/custom_addons/product_auto_sale_price/views/product_template_views.xml
- /home/julio/odoo17-dev/custom_addons/product_auto_sale_price/PORTING_NOTES.md

## Changes
- Kept the auto-price block editable on product templates (standard product form).
- Made the auto-price fields readonly in the product variant form (`product.product`) so the block is informational when accessed via a variant.
- Kept `product.product.x_auto_price_enabled` as a writable related field and restored the variant list server action for recalculation.

## Core validation evidence (Odoo 17)
- Variant tree XMLID `product.product_product_tree_view` verified in `/home/julio/odoo17-dev/odoo_core/addons/product/views/product_views.xml`.
- Variant form XMLID `product.product_normal_form_view` verified in `/home/julio/odoo17-dev/odoo_core/addons/product/views/product_views.xml`.
- `product.product` uses `product_tmpl_id` relationship in `/home/julio/odoo17-dev/odoo_core/addons/product/models/product_product.py`.
