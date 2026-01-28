from odoo import models, fields, api


class FlightSchedule(models.Model):
    _name = "flight.schedule"
    _description = "Flight Schedule"
    _order = "departure_time desc"

    user_id = fields.Many2one(
        'res.users',
        string="Owner",
        default=lambda self: self.env.user,
        index=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        related='user_id.partner_id',
        store=True
    )
    flight_number = fields.Char(string="Flight Number", required=True)
    departure_time = fields.Datetime(string="Departure Time")
    arrival_time = fields.Datetime(string="Arrival Time")
    origin = fields.Char(string="Origin")
    destination = fields.Char(string="Destination")
    status = fields.Selection(
        [('active', 'Active'), ('cancelled', 'Cancelled')],
        default='active',
        string="Status"
    )
    price = fields.Float(string="Price")

    airline_name = fields.Char(string="Airline Name")
    airline_iata = fields.Char(string="Airline IATA")
    departure_iata = fields.Char(string="Departure IATA")
    arrival_iata = fields.Char(string="Arrival IATA")
    flight_status_api = fields.Char(string="API Flight Status")
    is_from_api = fields.Boolean(string="From API", default=False)

    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('flight_number', 'origin', 'destination')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.flight_number or 'N/A'}: {record.origin or ''} → {record.destination or ''}"
