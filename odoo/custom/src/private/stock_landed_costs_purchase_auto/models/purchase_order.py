# Copyright 2021-2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    landed_cost_ids = fields.One2many(
        comodel_name="stock.landed.cost",
        inverse_name="purchase_id",
        string="Landed Costs",
    )
    landed_cost_number = fields.Integer(compute="_compute_landed_cost_number")

    def _compute_landed_cost_number(self):
        domain = [("purchase_id", "in", self.ids)]
        res = self.env["stock.landed.cost"].read_group(
            domain=domain, fields=["purchase_id"], groupby=["purchase_id"]
        )
        landed_cost_dict = {x["purchase_id"][0]: x["purchase_id_count"] for x in res}
        for item in self:
            item.landed_cost_number = landed_cost_dict.get(item.id, 0)

    def _prepare_landed_cost_values(self, picking):
        return {
            "purchase_id": self.id,
            "picking_ids": [(4, picking.id)],
        }

    def _create_picking_with_stock_landed_cost(self, picking):
        self.ensure_one()
        product_category = self.env["product.category"].search(
            [("name", "=", "LPG CATEGORY")]
        )
        products = self.env["product.product"].search(
            [("categ_id", "in", product_category.ids), ("landed_cost_ok", "=", True)]
        )
        for product in products:
            landed_cost = (
                self.env["stock.landed.cost"]
                .with_company(self.company_id)
                .create(self._prepare_landed_cost_values(picking))
            )
            self.env["stock.landed.cost.lines"].create(
                {
                    "cost_id": landed_cost.id,
                    "product_id": product.id,
                    "name": product.name,
                    "price_unit": 0.0,
                    "split_method": "by_quantity",
                    "account_id": 112,
                    # "company_id": picking.company_id.id,
                }
            )
            self.write({"landed_cost_ids": [(4, landed_cost.id)]})

    def _create_picking(self):
        all_pickings = self.mapped("picking_ids")
        res = super()._create_picking()
        for line in self.order_line:
            product_category = line.product_id.categ_id
            if product_category.name == "LPG CATEGORY":
                for order in self:
                    order_pickings = order.picking_ids - all_pickings
                    if order_pickings:
                        order._create_picking_with_stock_landed_cost(
                            fields.first(order_pickings)
                        )
        return res

    def action_view_stock_landed_cost(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock_landed_costs.action_stock_landed_cost"
        )
        action["context"] = {"search_default_purchase_id": self.id}
        return action

    def create(self, vals):
        po = super(PurchaseOrder, self).create(vals)
        self.check_product_category_requirement(po)
        return po

    @staticmethod
    def check_product_category_requirement(po):
        for line in po.order_line:
            product_category = line.product_id.categ_id
            if product_category.name == "LPG CATEGORY":
                pickings = po.picking_ids
                if pickings:
                    po._create_picking_with_stock_landed_cost(fields.first(pickings))
                break  # Exit the loop after the first occurrence


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _create_or_update_picking(self):
        all_pickings = self.mapped("order_id.picking_ids")
        res = super()._create_or_update_picking()
        for order in self.mapped("order_id"):
            order_pickings = order.picking_ids - all_pickings
            if order_pickings:
                order._create_picking_with_stock_landed_cost(
                    fields.first(order_pickings)
                )
        return res
